import time
from uuid import uuid4

from fastapi import FastAPI, Header
from pydantic import ValidationError

from app.audit import audit_event
from app.auth import AuthError, decode_bearer_token, merge_request_with_claims
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
def invoke(request: InvokeRequest, authorization: str | None = Header(default=None)):
    trace_id = str(uuid4())

    try:
        claims = decode_bearer_token(authorization)
        merged = merge_request_with_claims(request.model_dump(), claims)
        request = InvokeRequest(**merged)
    except AuthError as exc:
        audit_event("auth_denied", trace_id, {"reason": str(exc)})
        return InvokeResponse(
            output=f"Access denied: {exc}",
            status="denied",
            policy_decision="deny",
            trace_id=trace_id,
        )
    except ValidationError as exc:
        audit_event("request_invalid", trace_id, {"reason": str(exc)})
        return InvokeResponse(
            output=f"Invalid request after claim mapping: {exc}",
            status="error",
            policy_decision="deny",
            trace_id=trace_id,
        )

    decision = authorize(
        role=request.role,
        tenant_id=request.tenant_id,
        purpose_of_use=request.purpose_of_use,
        attributes={**request.attributes, "tenant_id": request.tenant_id},
        context=request.context,
        patient_context=request.patient_context,
    )
    if not decision.allow:
        audit_event(
            "policy_denied",
            trace_id,
            {
                "reason": decision.reason,
                "role": request.role,
                "tenant_id": request.tenant_id,
                "purpose_of_use": request.purpose_of_use,
            },
        )
        return InvokeResponse(
            output=f"Access denied: {decision.reason}",
            status="denied",
            policy_decision=decision.decision,
            trace_id=trace_id,
        )

    ok, reason = check_guardrails(request.message)
    if not ok:
        audit_event("guardrail_blocked", trace_id, {"reason": reason, "tenant_id": request.tenant_id})
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

    audit_event(
        "invoke_success",
        trace_id,
        {
            "tenant_id": request.tenant_id,
            "user_id": request.user_id,
            "role": request.role,
            "purpose_of_use": request.purpose_of_use,
            "duration_sec": duration,
        },
    )

    return InvokeResponse(
        output=output,
        status="success",
        policy_decision="allow",
        trace_id=trace_id,
    )
