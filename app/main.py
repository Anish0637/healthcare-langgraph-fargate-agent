import os
import time
from uuid import uuid4

from fastapi import FastAPI, Header
from pydantic import ValidationError

from app.audit import audit_event
from app.config import LANGCHAIN_API_KEY, LANGCHAIN_ENDPOINT, LANGCHAIN_PROJECT, LANGCHAIN_TRACING_V2

# Activate LangSmith tracing if the API key is present
if LANGCHAIN_API_KEY:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", LANGCHAIN_TRACING_V2)
    os.environ.setdefault("LANGCHAIN_API_KEY", LANGCHAIN_API_KEY)
    os.environ.setdefault("LANGCHAIN_PROJECT", LANGCHAIN_PROJECT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", LANGCHAIN_ENDPOINT)
from app.auth import AuthError, decode_bearer_token, merge_request_with_claims
from app.hitl import HitlStore
from app.governance import check_guardrails, sanitize_for_model, sanitize_for_output
from app.graph import graph
from app.memory import MemoryStore
from app.models import InvokeRequest, InvokeResponse, HealthResponse, ReviewDecisionRequest, ReviewResponse
from app.security import authorize

try:
    from langsmith import trace as ls_trace
    LANGSMITH_AVAILABLE = bool(LANGCHAIN_API_KEY)
except ImportError:
    ls_trace = None
    LANGSMITH_AVAILABLE = False

app = FastAPI(title="Healthcare LangGraph Agent", version="0.1.0")
memory = MemoryStore()
reviews = HitlStore()


def _process_request(request: InvokeRequest, trace_id: str, bypass_review: bool = False) -> InvokeResponse:
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

    if not bypass_review and (request.context.get("break_glass") or request.context.get("human_review_required") or request.attributes.get("risk_level") == "high"):
        review_id = reviews.create_review({"request": request.model_dump(), "trace_id": trace_id})
        audit_event("human_review_requested", trace_id, {"review_id": review_id, "tenant_id": request.tenant_id})
        return InvokeResponse(
            output=f"Human review required. review_id={review_id}",
            status="pending_human_review",
            policy_decision="review",
            trace_id=trace_id,
            review_id=review_id,
        )

    sanitized_input = sanitize_for_model(request.message)

    started = time.perf_counter()
    run_config = {
        "run_name": f"invoke-{trace_id[:8]}",
        "tags": [request.tenant_id, request.role, request.purpose_of_use],
        "metadata": {
            "trace_id": trace_id,
            "tenant_id": request.tenant_id,
            "user_id": request.user_id,
            "role": request.role,
        },
    }
    result = graph.invoke({"messages": [("user", sanitized_input)]}, config=run_config)
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
            "model_used": getattr(result["messages"][-1], "response_metadata", {}).get("selected_model", "unknown") if result.get("messages") else "unknown",
        },
    )

    return InvokeResponse(
        output=output,
        status="success",
        policy_decision="allow",
        trace_id=trace_id,
    )


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

    return _process_request(request, trace_id, bypass_review=False)


@app.post("/reviews/{review_id}/decision", response_model=ReviewResponse)
def decide_review(review_id: str, decision: ReviewDecisionRequest):
    item = reviews.get_review(review_id)
    if not item:
        return ReviewResponse(review_id=review_id, status="not_found", message="Review not found")

    request_payload = item.get("request_json")
    original = InvokeRequest.model_validate_json(request_payload)
    trace_id = item.get("trace_id", str(uuid4()))

    if not decision.approved:
        reviews.update_review(review_id, "rejected", decision.reviewer_id, decision.reason or "rejected")
        audit_event("human_review_rejected", trace_id, {"review_id": review_id, "reviewer_id": decision.reviewer_id})
        return ReviewResponse(review_id=review_id, status="rejected", message="Request rejected by reviewer")

    reviews.update_review(review_id, "approved", decision.reviewer_id, decision.reason or "approved")
    response = _process_request(original, trace_id, bypass_review=True)
    return ReviewResponse(review_id=review_id, status=response.status, message=response.output)
