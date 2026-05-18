import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
DDB_MEMORY_TABLE = os.getenv("DDB_MEMORY_TABLE", "healthcare-agent-memory")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a healthcare assistant. Follow policy and never expose PHI.",
)
