import time
from typing import TypedDict, Annotated
from uuid import uuid4

import boto3
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

try:
    from langchain_aws import ChatBedrockConverse
except ImportError:  # pragma: no cover
    ChatBedrockConverse = None

from app.config import AWS_PROFILE, AWS_REGION, BEDROCK_MODEL_ID, SYSTEM_PROMPT


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class FallbackModel:
    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        return AIMessage(content=f"Fallback response: {last_user.content if last_user else 'No input'}")


def _build_model():
    if ChatBedrockConverse is None:
        return FallbackModel()
    try:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        client = session.client("bedrock-runtime")
        return ChatBedrockConverse(model=BEDROCK_MODEL_ID, client=client, region_name=AWS_REGION)
    except Exception:
        return FallbackModel()


_MODEL = _build_model()


def assistant(state: AgentState) -> AgentState:
    msgs = state["messages"]
    response = _MODEL.invoke([SystemMessage(content=SYSTEM_PROMPT), *msgs])
    return {"messages": [response]}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("assistant", assistant)
    g.add_edge(START, "assistant")
    g.add_edge("assistant", END)
    return g.compile()


graph = build_graph()
