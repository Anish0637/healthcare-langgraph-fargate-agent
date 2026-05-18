import time
from uuid import uuid4

from fastapi import FastAPI

from app.governance import check_guardrails, sanitize_for_model, sanitize_for_output
from app.graph import graph
from app.memory import MemoryStore
from app.models import InvokeRequest, InvokeResponse, HealthResponse
from app.security import authorize

app = FastAPI(title="Healthcare LangGraph Agent", version="0.1.0")
memory = MemoryStore()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@app.post("/invoke", response_model=InvokeResponse)
def invoke(request: InvokeRequest):
    trace_id = str(uuid4())

    decision = authorize(
        role=request.role,
        tenant_id=request.tenant_id,
        purpose_of_use=request.purpose_of_use,
        attributes={**request.attributes, "tenant_id": request.tenant_id},
        context=request.context,
        patient_context=request.patient_context,
    )
    if not decision.allow:
        return InvokeResponse(
            output=f"Access denied: {decision.reason}",
            status="denied",
            policy_decision=decision.decision,
            trace_id=trace_id,
        )

    ok, reason = check_guardrails(request.message)
    if not ok:
        return InvokeResponse(
            output=f"Blocked by guardrail: {reason}",
            status="blocked",
            policy_decision="deny",
            trace_id=trace_id,
        )

    sanitized_input = sanitize_for_model(request.message)

    started = time.perf_counter()
    result = graph.invoke({"messages": [("user", sanitized_input)]})
    duration = time.perf_counter() - started

    output = result["messages"][-1].content if result.get("messages") else ""
    output = sanitize_for_output(str(output))

    memory.save(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        prompt=sanitized_input,
        response=output,
        duration_sec=duration,
    )

    return InvokeResponse(
        output=output,
        status="success",
        policy_decision="allow",
        trace_id=trace_id,
    )
