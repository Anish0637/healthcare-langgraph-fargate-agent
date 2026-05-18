import time
from functools import lru_cache
from typing import TypedDict, Annotated

import boto3
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

try:
    from langchain_aws import ChatBedrockConverse
except ImportError:  # pragma: no cover
    ChatBedrockConverse = None

from app.config import AWS_PROFILE, AWS_REGION, BEDROCK_MODEL_IDS, KNOWLEDGE_BASE_ENABLED, KNOWLEDGE_BASE_ID, KNOWLEDGE_BASE_MAX_RESULTS, SYSTEM_PROMPT
from app.tools import retrieve_from_knowledge_base


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class FallbackModel:
    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        return AIMessage(content=f"Fallback response: {last_user.content if last_user else 'No input'}")


def _model_ids() -> list[str]:
    return BEDROCK_MODEL_IDS or []


@lru_cache(maxsize=1)
def _build_models():
    models: list[object] = []
    if ChatBedrockConverse is None:
        return [FallbackModel()]

    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    client = session.client("bedrock-runtime")
    for model_id in _model_ids():
        try:
            models.append(ChatBedrockConverse(model=model_id, client=client, region_name=AWS_REGION))
        except Exception:
            continue

    return models or [FallbackModel()]


_MODELS = _build_models()


def _select_model(preferred: str | None = None) -> object:
    if preferred:
        for model in _MODELS:
            if getattr(model, "model", None) == preferred:
                return model
    return _MODELS[0]


def _invoke_with_fallback(messages: list[BaseMessage], preferred: str | None = None) -> tuple[AIMessage, str, str]:
    ordered = list(_MODELS)
    if preferred:
        ordered.sort(key=lambda m: 0 if getattr(m, "model", None) == preferred else 1)

    for model in ordered:
        try:
            response = model.invoke(messages)
            model_name = getattr(model, "model", "fallback")
            return response, model_name, "primary" if model_name != "fallback" else "fallback"
        except Exception as exc:
            continue

    fallback = FallbackModel().invoke(messages)
    return fallback, "fallback", "fallback"


def _build_rag_context(user_query: str) -> str:
    """Retrieve relevant passages from Bedrock Knowledge Base and format as context."""
    if not KNOWLEDGE_BASE_ENABLED:
        return ""
    context = retrieve_from_knowledge_base({"query": user_query})
    if context.startswith("Knowledge Base not configured") or context.startswith("No relevant") or context.startswith("Knowledge base retrieval failed"):
        return ""
    return f"\n\n--- Relevant Clinical Knowledge ---\n{context}\n--- End Knowledge ---"


def assistant(state: AgentState) -> AgentState:
    msgs = state["messages"]

    # Inject RAG context from Bedrock Knowledge Base into the system prompt
    user_query = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")
    rag_context = _build_rag_context(user_query)
    system_content = SYSTEM_PROMPT + rag_context

    response, model_name, strategy = _invoke_with_fallback([SystemMessage(content=system_content), *msgs])
    if hasattr(response, "response_metadata"):
        response.response_metadata = {
            **getattr(response, "response_metadata", {}),
            "selected_model": model_name,
            "strategy": strategy,
            "rag_used": bool(rag_context),
        }
    return {"messages": [response]}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("assistant", assistant)
    g.add_edge(START, "assistant")
    g.add_edge("assistant", END)
    return g.compile()


graph = build_graph()
