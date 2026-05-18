from datetime import datetime, timezone
from functools import lru_cache

import boto3

from app.config import AWS_PROFILE, AWS_REGION, KNOWLEDGE_BASE_ID, KNOWLEDGE_BASE_MAX_RESULTS, KNOWLEDGE_BASE_ENABLED


def get_utc_time(_: dict | None = None) -> str:
    return datetime.now(timezone.utc).isoformat()


def patient_risk_score(args: dict) -> str:
    age = int(args.get("age", 50))
    chronic = int(args.get("chronic_conditions", 0))
    score = min(100, age + chronic * 10)
    return f"risk_score={score}"


@lru_cache(maxsize=1)
def _bedrock_agent_runtime_client():
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return session.client("bedrock-agent-runtime")


def retrieve_from_knowledge_base(args: dict) -> str:
    """
    Retrieve relevant clinical context from a Bedrock Knowledge Base using RAG.
    args: {"query": str, "knowledge_base_id": str (optional override)}
    Returns: concatenated text of top matching passages.
    """
    if not KNOWLEDGE_BASE_ENABLED:
        return "Knowledge Base not configured (set KNOWLEDGE_BASE_ID env var)."

    query = args.get("query", "")
    kb_id = args.get("knowledge_base_id", KNOWLEDGE_BASE_ID)

    if not query:
        return "No query provided for knowledge base retrieval."

    try:
        client = _bedrock_agent_runtime_client()
        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": KNOWLEDGE_BASE_MAX_RESULTS}
            },
        )
        results = response.get("retrievalResults", [])
        if not results:
            return "No relevant documents found in knowledge base."

        passages = []
        for i, r in enumerate(results, 1):
            content = r.get("content", {}).get("text", "")
            score = r.get("score", 0)
            source = r.get("location", {}).get("s3Location", {}).get("uri", "unknown")
            passages.append(f"[{i}] (score={score:.3f}, source={source})\n{content}")

        return "\n\n".join(passages)

    except Exception as exc:
        return f"Knowledge base retrieval failed: {exc}"


TOOLS = {
    "get_utc_time": get_utc_time,
    "patient_risk_score": patient_risk_score,
    "retrieve_from_knowledge_base": retrieve_from_knowledge_base,
}
