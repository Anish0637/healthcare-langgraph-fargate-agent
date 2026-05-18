import importlib
import sys
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage


@dataclass
class FakeHitlStore:
    items: dict = field(default_factory=dict)

    def create_review(self, payload: dict) -> str:
        review_id = "review-123"
        self.items[review_id] = {
            "review_id": review_id,
            "trace_id": payload["trace_id"],
            "request_json": __import__("json").dumps(payload["request"]),
        }
        return review_id

    def get_review(self, review_id: str):
        return self.items.get(review_id)

    def update_review(self, review_id: str, status: str, reviewer_id: str, decision_reason: str = ""):
        self.items.setdefault(review_id, {})
        self.items[review_id].update(
            {
                "status": status,
                "reviewer_id": reviewer_id,
                "decision_reason": decision_reason,
            }
        )


class FakeMemoryStore:
    def __init__(self):
        self.saved = []

    def save(self, **kwargs):
        self.saved.append(kwargs)


class FakeGraph:
    def __init__(self, output: str = "approved response"):
        self.output = output

    def invoke(self, payload):
        return {"messages": [AIMessage(content=self.output)]}


def _load_main(monkeypatch):
    import app.hitl as hitl_module
    import app.memory as memory_module

    monkeypatch.setattr(hitl_module, "HitlStore", FakeHitlStore)
    monkeypatch.setattr(memory_module, "MemoryStore", FakeMemoryStore)
    sys.modules.pop("app.main", None)
    return importlib.import_module("app.main")


def test_human_review_is_queued_for_high_risk_request(monkeypatch):
    main = _load_main(monkeypatch)

    monkeypatch.setattr(main, "authorize", lambda **kwargs: type("Decision", (), {"allow": True, "reason": "ok", "decision": "allow"})())
    monkeypatch.setattr(main, "check_guardrails", lambda message: (True, "ok"))
    monkeypatch.setattr(main, "sanitize_for_model", lambda message: message)
    monkeypatch.setattr(main, "sanitize_for_output", lambda message: message)

    request = main.InvokeRequest(
        message="review this high risk request",
        user_id="user-1",
        role="clinician",
        tenant_id="tenant-1",
        purpose_of_use="treatment",
        attributes={"risk_level": "high"},
        context={},
        patient_context={},
    )

    response = main._process_request(request, trace_id="trace-1")

    assert response.status == "pending_human_review"
    assert response.review_id == "review-123"
    assert "Human review required" in response.output


def test_review_approval_resumes_processing(monkeypatch):
    main = _load_main(monkeypatch)

    monkeypatch.setattr(main, "authorize", lambda **kwargs: type("Decision", (), {"allow": True, "reason": "ok", "decision": "allow"})())
    monkeypatch.setattr(main, "check_guardrails", lambda message: (True, "ok"))
    monkeypatch.setattr(main, "sanitize_for_model", lambda message: message)
    monkeypatch.setattr(main, "sanitize_for_output", lambda message: message)
    monkeypatch.setattr(main, "graph", FakeGraph(output="approved response"))

    request = main.InvokeRequest(
        message="normal request",
        user_id="user-1",
        role="clinician",
        tenant_id="tenant-1",
        purpose_of_use="treatment",
        attributes={},
        context={},
        patient_context={},
    )

    review_id = "review-123"
    main.reviews.items[review_id] = {
        "review_id": review_id,
        "trace_id": "trace-2",
        "request_json": request.model_dump_json(),
    }

    response = main.decide_review(
        review_id,
        main.ReviewDecisionRequest(approved=True, reviewer_id="reviewer-1", reason="approved"),
    )

    assert response.review_id == review_id
    assert response.status == "success"
    assert response.message == "approved response"


def test_graph_falls_back_when_models_fail(monkeypatch):
    import app.graph as graph_module

    class ExplodingModel:
        model = "exploding"

        def invoke(self, messages):
            raise RuntimeError("boom")

    monkeypatch.setattr(graph_module, "_MODELS", [ExplodingModel()])

    result = graph_module.assistant({"messages": [HumanMessage(content="help") ]})

    assert result["messages"][-1].content == "Fallback response: help"