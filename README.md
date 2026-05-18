# Healthcare LangGraph Agent on ECS Fargate

Production-oriented starter repository for a containerized LangGraph agent designed for healthcare workloads with PHI/PII controls.

## What this repo includes

- FastAPI + LangGraph agent runtime
- Memory persistence in DynamoDB
- RBAC, ABAC, and CBAC policy enforcement
- Data governance policy checks (purpose, retention, lawful basis placeholders)
- PII/PHI redaction before model/tool usage
- Tool governance with policy tags and allow/deny checks
- Guardrails for unsafe prompt patterns and response leakage checks
- JWT auth with claims-to-policy mapping
- Structured redacted audit logs for security events
- Dockerized app for ECS Fargate
- ECS task definition template + deployment script
- Terraform scaffold for VPC, ECS, ALB, DynamoDB, IAM, CloudWatch

## Security architecture

1. Request enters `/invoke` with identity + context claims.
2. Policy engine evaluates:
   - RBAC: role permissions
   - ABAC: attributes like tenant, sensitivity, environment
   - CBAC: contextual constraints like time windows and break-glass flags
3. Input is redacted for PHI/PII before model/tool usage.
4. Guardrail checks block prompt injection or disallowed actions.
5. Tool governance permits only approved tools for the request context.
6. Response is checked/redacted before returning.
7. Sanitized memory is saved to DynamoDB (encrypted at rest via AWS managed encryption).

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./run_local.sh
```

Health:

```bash
curl -s http://127.0.0.1:8080/health
```

Invoke example:

```bash
curl -s -X POST http://127.0.0.1:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize this chart note for care coordination",
    "user_id": "u-123",
    "role": "clinician",
    "tenant_id": "hospital-a",
    "purpose_of_use": "treatment",
    "patient_context": {"patient_id": "p-001", "consent": true},
    "attributes": {"department": "cardiology", "env": "prod"},
    "context": {"request_time_utc": "2026-05-18T12:00:00Z"}
  }'
```

## ECS Fargate deployment

Set environment variables and deploy:

```bash
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO=healthcare-langgraph-agent
export ECS_CLUSTER=healthcare-agents
export ECS_SERVICE=healthcare-langgraph-agent-svc
export ECS_TASK_FAMILY=healthcare-langgraph-agent
./aws/deploy_ecs.sh
```

## Governance notes

- This is a starter baseline. For production healthcare compliance:
  - Integrate enterprise IdP/JWKS verification
  - Enable KMS CMKs, VPC endpoints, private subnets, WAF
  - Add immutable audit trails and SIEM export
  - Map controls to HIPAA, HITRUST, SOC2 requirements
  - Add DLP and secrets scanning in CI/CD

## JWT and policy mapping

Send bearer token in `Authorization` header. Claims can override request identity fields:

- `sub` or `user_id` -> `user_id`
- `role` -> `role`
- `tenant_id` -> `tenant_id`
- `purpose_of_use` -> `purpose_of_use`
- `attributes`, `context`, `patient_context` (merged)

Set `.env`:

```env
JWT_REQUIRED=true
JWT_SECRET=your-shared-secret
JWT_ALGORITHM=HS256
```

## Terraform quick start

```bash
cd terraform
terraform init
terraform plan -var="container_image=<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-langgraph-agent:latest"
terraform apply -var="container_image=<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-langgraph-agent:latest"
```
