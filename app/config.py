import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
BEDROCK_MODEL_IDS = [m.strip() for m in os.getenv("BEDROCK_MODEL_IDS", BEDROCK_MODEL_ID).split(",") if m.strip()]
DDB_MEMORY_TABLE = os.getenv("DDB_MEMORY_TABLE", "healthcare-agent-memory")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a healthcare assistant. Follow policy and never expose PHI.",
)

# Bedrock Knowledge Base (RAG)
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")  # e.g. "ABCD1234EF"
KNOWLEDGE_BASE_MAX_RESULTS = int(os.getenv("KNOWLEDGE_BASE_MAX_RESULTS", "5"))
KNOWLEDGE_BASE_ENABLED = bool(KNOWLEDGE_BASE_ID)

# LangSmith tracing (set LANGCHAIN_TRACING_V2=true to enable)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "healthcare-langgraph-agent")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
