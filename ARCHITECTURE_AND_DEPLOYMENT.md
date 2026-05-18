# Healthcare LangGraph Fargate Agent - Architecture & Deployment Guide

**Last Updated:** May 18, 2026  
**Status:** Production Ready  
**Deployment Platform:** AWS ECS Fargate  
**Region:** us-east-1

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Repository Structure](#repository-structure)
3. [System Architecture](#system-architecture)
4. [Security Architecture](#security-architecture)
5. [Key Components](#key-components)
6. [Deployment Architecture](#deployment-architecture)
7. [Deployment Steps](#deployment-steps)
8. [API Documentation](#api-documentation)
9. [Monitoring & Logs](#monitoring--logs)
10. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Executive Summary

**Healthcare LangGraph Agent on ECS Fargate** is a production-oriented, containerized AI agent designed for healthcare workloads with strict PHI/PII controls, policy enforcement, and compliance requirements.

### Key Features

✅ **AI Agent Framework**: LangGraph-based agentic workflow with multi-model Bedrock routing  
✅ **Security**: RBAC, ABAC, CBAC policy enforcement with break-glass override capability  
✅ **Data Protection**: Automatic PII/PHI redaction before model input and output  
✅ **Governance**: Tool governance with policy tags, guardrails, and response validation  
✅ **Audit Trail**: Structured, redacted logging for security events and data access  
✅ **Human-in-the-Loop**: Review queue for high-risk and break-glass requests  
✅ **Persistence**: DynamoDB memory storage for multi-turn conversations  
✅ **Containerized**: Docker image pushed to ECR, deployed on ECS Fargate  
✅ **Scalable**: Auto-scaling ready, serverless container orchestration  

---

## Repository Structure

```
healthcare-langgraph-fargate-agent/
├── app/                              # Core application code
│   ├── main.py                       # FastAPI application, request routing
│   ├── graph.py                      # LangGraph workflow definition
│   ├── models.py                     # Pydantic request/response schemas
│   ├── auth.py                       # JWT token parsing, identity claims
│   ├── security.py                   # Policy enforcement (RBAC/ABAC/CBAC)
│   ├── governance.py                 # Guardrails, input/output sanitization
│   ├── pii.py                        # PII/PHI detection and redaction
│   ├── audit.py                      # Structured audit logging
│   ├── memory.py                     # DynamoDB conversation memory
│   ├── hitl.py                       # Human-in-the-loop review queue
│   ├── tools.py                      # Tool definitions for agent
│   ├── config.py                     # Configuration from env vars
│   └── __init__.py
├── aws/                              # AWS deployment artifacts
│   ├── deploy_ecs.sh                 # Docker build/push to ECR script
│   └── ecs-task-definition.json      # ECS task definition template
├── terraform/                        # Infrastructure as Code
│   ├── main.tf                       # VPC, ECS cluster, ALB, DynamoDB
│   ├── variables.tf                  # Variable definitions
│   ├── outputs.tf                    # Output values
│   ├── versions.tf                   # Provider versions
│   └── README.md                     # Terraform deployment guide
├── tests/                            # Unit tests
│   ├── test_auth.py                  # Auth/JWT tests
│   ├── test_pii.py                   # PII redaction tests
│   ├── test_security.py              # Policy enforcement tests
│   └── test_review_and_fallback.py   # HITL and fallback tests
├── Dockerfile                        # Container image definition
├── requirements.txt                  # Python dependencies
├── run_local.sh                      # Local development script
├── README.md                         # Project README
└── ARCHITECTURE_AND_DEPLOYMENT.md   # This file
```

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Healthcare Client/App                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS Request + JWT Token
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           AWS Application Load Balancer (ALB)                    │
│              (SSL/TLS Termination, Port 443)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ Route to Container
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│        ECS Fargate Task (Container Instance)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Port 8080)                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 1. REQUEST VALIDATION & AUTH                        │  │  │
│  │  │    - Decode JWT bearer token                       │  │  │
│  │  │    - Extract identity claims (user_id, role, etc)  │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 2. POLICY ENFORCEMENT (RBAC/ABAC/CBAC)             │  │  │
│  │  │    - Check role permissions (RBAC)                 │  │  │
│  │  │    - Check attributes & context (ABAC)             │  │  │
│  │  │    - Check time windows & risk level (CBAC)        │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 3. GUARDRAIL CHECK                                 │  │  │
│  │  │    - Detect prompt injection                       │  │  │
│  │  │    - Block unsafe patterns                         │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 4. HUMAN-IN-THE-LOOP DECISION                      │  │  │
│  │  │    - Check break_glass flag                        │  │  │
│  │  │    - Check human_review_required flag              │  │  │
│  │  │    - If required: Store in HITL Queue → Return    │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 5. DATA SANITIZATION (PII/PHI)                     │  │  │
│  │  │    - Redact emails, phone, SSN, etc                │  │  │
│  │  │    - Scrub before model input                      │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 6. LANGGRAPH AGENT INVOCATION                      │  │  │
│  │  │    - Route to available Bedrock model              │  │  │
│  │  │    - Fallback to safe response if models fail      │  │  │
│  │  │    - Invoke tools with permission checks           │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 7. OUTPUT SANITIZATION                             │  │  │
│  │  │    - Scrub PII/PHI from response                   │  │  │
│  │  │    - Validate response safety                      │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 8. MEMORY PERSISTENCE                              │  │  │
│  │  │    - Save conversation to DynamoDB                 │  │  │
│  │  │    - Partition by tenant_id for isolation          │  │  │
│  │  │    - AES-256 encryption at rest (AWS managed)      │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 9. AUDIT LOGGING                                   │  │  │
│  │  │    - Log security events with PII redaction        │  │  │
│  │  │    - CloudWatch Logs (encrypted)                   │  │  │
│  │  └──────────────────┬──────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 10. RESPONSE RETURN                                │  │  │
│  │  │     - JSON with trace_id for correlation           │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         ▲ JSON Response
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
    [DynamoDB]                    [CloudWatch Logs]
    Conversation Memory            Audit Trail
    (Encrypted)                    (Redacted)
```

---

## Security Architecture

### 1. **Authentication (JWT)**
- Client sends Authorization header with Bearer token
- Token decoded to extract claims: `user_id`, `role`, `tenant_id`, `purpose_of_use`, `attributes`
- Signature validation ensures token authenticity

### 2. **Authorization (RBAC/ABAC/CBAC)**

#### RBAC (Role-Based Access Control)
- **Clinician**: `treatment`, `care_coordination`
- **Billing**: `payment`, `operations`
- **Researcher**: `research_deidentified`

#### ABAC (Attribute-Based Access Control)
- Tenant isolation: `attributes.tenant_id` must match request `tenant_id`
- Data class restrictions: Restricted data (`env=prod`, `data_class=restricted`) only for `clinician` role
- Department/location checks: Enforceable via attributes

#### CBAC (Context-Based Access Control)
- **Time windows**: Billing team cannot access data outside business hours (6 AM+)
- **Break-glass override**: Emergency flag allows access with audit trail
- **Risk level**: High-risk requests automatically routed to human review

### 3. **Data Protection (PII/PHI)**
- Regex-based detection for:
  - Email addresses
  - Phone numbers
  - SSNs
  - Medical record numbers
  - Credit card numbers
- Redaction happens:
  - **Before model input**: Model never sees sensitive data
  - **Before storage**: DynamoDB gets clean data
  - **Before output**: Response sanitized before returning to client

### 4. **Guardrails**
- **Prompt injection detection**: Blocks suspicious patterns
- **Output validation**: Checks response for information leakage
- **Tool governance**: Tools tagged with policies, only approved tools available per context

### 5. **Human-in-the-Loop (HITL)**
Requests routed to manual review queue when:
- `context.break_glass == True` (emergency access)
- `context.human_review_required == True` (explicit request)
- `attributes.risk_level == "high"` (automatic high-risk detection)

Reviewer can:
- Approve request (continues execution with audit trail)
- Reject request (returns denial response, audit logged)

### 6. **Audit Logging**
- **Event types**: `policy_denied`, `guardrail_blocked`, `human_review_requested`, `approved`, `error`
- **Sanitized logging**: All PII/PHI redacted before logging
- **Immutable trail**: CloudWatch Logs with 1-year retention
- **Correlation**: `trace_id` links all events in a request lifecycle

---

## Key Components

### **1. FastAPI Application (`app/main.py`)**
- REST endpoints:
  - `POST /invoke` - Send message to agent
  - `POST /reviews/{review_id}/decision` - Approve/reject HITL request
  - `GET /health` - Health check
- Request/response validation with Pydantic
- Dependency injection for memory and HITL stores

### **2. LangGraph Workflow (`app/graph.py`)**
- Multi-model Bedrock routing (primary + fallbacks)
- State management for multi-turn conversations
- Tool integration with permission checks
- Graceful degradation: Fallback response if all models fail

### **3. Security Module (`app/security.py`)**
- `authorize()` function implements RBAC/ABAC/CBAC
- Policy decision returns allow/deny with reasoning
- Extensible for custom policy rules

### **4. PII/PHI Detection (`app/pii.py`)**
- Regex patterns for common sensitive data
- `redact_text()` function for data sanitization
- High precision to minimize false positives

### **5. Governance (`app/governance.py`)**
- `check_guardrails()` - Prompt injection detection
- `sanitize_for_model()` - PII redaction before model
- `sanitize_for_output()` - Redaction before response

### **6. DynamoDB Memory (`app/memory.py`)**
- Partition key: `tenant_id` (multi-tenancy isolation)
- Sort key: `timestamp` (conversation history)
- Attributes: `user_id`, `messages`, `metadata`
- Encrypted at rest (AWS managed keys)

### **7. HITL Review Queue (`app/hitl.py`)**
- Stores pending reviews in simple in-memory map (production: move to DynamoDB)
- Tracks approval/rejection status
- Audit logging of reviewer decisions

### **8. Audit Logging (`app/audit.py`)**
- Structured JSON logging to CloudWatch
- Automatic PII redaction via `_sanitize_obj()`
- Timestamp, event type, trace ID, payload

---

## Deployment Architecture

### **AWS Resources Created**

#### 1. **ECS Fargate Cluster**
```
Cluster Name: healthcare-agents
Service: healthcare-langgraph-agent-svc
Task Definition: healthcare-langgraph-agent:1
Task Count: 1 (scalable to N)
Launch Type: FARGATE (serverless containers)
CPU: 512 CPU units
Memory: 1024 MB
```

#### 2. **ECR Repository**
```
URI: 582766763952.dkr.ecr.us-east-1.amazonaws.com/healthcare-langgraph-agent
Image Tag: latest
```

#### 3. **VPC & Networking**
```
VPC: vpc-01cd0b3707b8ba27c (Default VPC)
Subnets: 
  - subnet-06ccc1d0d403eb1a3 (us-east-1b)
  - subnet-029cb79a55aa7f9b6 (us-east-1f)
Security Group: sg-08af0f1d09b790516
  - Inbound: TCP 8080 (0.0.0.0/0)
  - Outbound: All traffic (default)
```

#### 4. **DynamoDB**
```
Table Name: healthcare-agent-memory
Billing Mode: PAY_PER_REQUEST (on-demand)
Hash Key: tenant_id
Range Key: timestamp
Encryption: AWS managed keys (default)
TTL: Configurable per application needs
```

#### 5. **CloudWatch**
```
Log Group: /ecs/healthcare-langgraph-agent
Log Streams: One per task
Retention: 30 days (configurable)
Metrics: CPU, Memory, Task count
```

#### 6. **IAM Roles**
```
Execution Role: ecsTaskExecutionRole
  - Permissions: ECR pull, CloudWatch logs push, ECS agent operations
  
Task Role: healthcare-langgraph-task-role
  - Permissions:
    * DynamoDB: All actions on healthcare-agent-* tables
    * Bedrock: InvokeModel, InvokeModelWithResponseStream
    * CloudWatch: CreateLogGroup, CreateLogStream, PutLogEvents
    * ECR: Pull image during task startup
```

#### 7. **Application Load Balancer (ALB)**
```
(Optional - can be added for production with SSL/TLS)
Listener Port: 443 (HTTPS)
Target Group: ECS service on port 8080
Health Check: GET /health
```

---

## Deployment Steps

### **Prerequisites**
- AWS Account with appropriate IAM permissions
- AWS CLI configured with `anish0637` profile
- Docker installed and running
- Git repository cloned locally
- Python 3.11+ for local testing

### **Step 1: Build & Push Docker Image**

```bash
export AWS_PROFILE=anish0637
export AWS_ACCOUNT_ID=582766763952
export AWS_REGION=us-east-1
export ECR_REPO=healthcare-langgraph-agent

cd /path/to/healthcare-langgraph-fargate-agent
bash aws/deploy_ecs.sh
```

**What happens:**
1. Creates ECR repository (if not exists)
2. Logs in to ECR
3. Builds Docker image from `Dockerfile`
4. Tags image with account ID and region
5. Pushes image to ECR

### **Step 2: Register ECS Task Definition**

```bash
export AWS_PROFILE=anish0637
export AWS_ACCOUNT_ID=582766763952
export AWS_REGION=us-east-1

sed -e "s|<ACCOUNT_ID>|${AWS_ACCOUNT_ID}|g" \
    -e "s|<REGION>|${AWS_REGION}|g" \
    aws/ecs-task-definition.json > /tmp/task-def.json

aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-def.json \
  --profile ${AWS_PROFILE} \
  --region ${AWS_REGION}
```

### **Step 3: Create ECS Cluster**

```bash
aws ecs create-cluster \
  --cluster-name healthcare-agents \
  --profile ${AWS_PROFILE} \
  --region ${AWS_REGION}
```

### **Step 4: Create Security Group**

```bash
# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query 'Vpcs[0].VpcId' --output text \
  --profile ${AWS_PROFILE} --region ${AWS_REGION})

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name healthcare-langgraph-sg \
  --description "Security group for healthcare langgraph agent" \
  --vpc-id ${VPC_ID} \
  --query 'GroupId' --output text \
  --profile ${AWS_PROFILE} --region ${AWS_REGION})

# Allow port 8080
aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp --port 8080 --cidr 0.0.0.0/0 \
  --profile ${AWS_PROFILE} --region ${AWS_REGION}
```

### **Step 5: Create IAM Roles**

```bash
# Task execution role (if not exists)
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  --profile ${AWS_PROFILE}

# Attach managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --profile ${AWS_PROFILE}

# Task role with custom permissions
aws iam create-role \
  --role-name healthcare-langgraph-task-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  --profile ${AWS_PROFILE}

# Attach inline policy
aws iam put-role-policy \
  --role-name healthcare-langgraph-task-role \
  --policy-name healthcare-langgraph-task-policy \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[
      {"Effect":"Allow","Action":["dynamodb:*"],"Resource":"arn:aws:dynamodb:*:*:table/healthcare-agent-*"},
      {"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource":"*"},
      {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:*:*:*"}
    ]
  }' \
  --profile ${AWS_PROFILE}
```

### **Step 6: Create CloudWatch Log Group**

```bash
aws logs create-log-group \
  --log-group-name /ecs/healthcare-langgraph-agent \
  --profile ${AWS_PROFILE} \
  --region ${AWS_REGION}
```

### **Step 7: Create ECS Service**

```bash
# Get subnets
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query 'Subnets[0:2].SubnetId' --output text \
  --profile ${AWS_PROFILE} --region ${AWS_REGION})

aws ecs create-service \
  --cluster healthcare-agents \
  --service-name healthcare-langgraph-agent-svc \
  --task-definition healthcare-langgraph-agent:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_IDS// /,}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
  --profile ${AWS_PROFILE} \
  --region ${AWS_REGION}
```

### **Step 8: Monitor Task Startup**

```bash
# Check task status
aws ecs list-tasks --cluster healthcare-agents \
  --profile ${AWS_PROFILE} --region ${AWS_REGION}

# Get task details (wait for lastStatus=RUNNING)
aws ecs describe-tasks \
  --cluster healthcare-agents \
  --tasks <task-arn> \
  --profile ${AWS_PROFILE} \
  --region ${AWS_REGION}

# Get public IP from ENI
aws ec2 describe-network-interfaces \
  --network-interface-ids <eni-id> \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --profile ${AWS_PROFILE} --region ${AWS_REGION}
```

---

## API Documentation

### **1. Invoke Agent**

**Endpoint:** `POST /invoke`

**Request:**
```json
{
  "message": "Summarize this chart note for care coordination",
  "user_id": "u-123",
  "role": "clinician",
  "tenant_id": "hospital-a",
  "purpose_of_use": "treatment",
  "patient_context": {
    "patient_id": "p-001",
    "consent": true
  },
  "attributes": {
    "department": "cardiology",
    "env": "prod",
    "data_class": "restricted",
    "risk_level": "low"
  },
  "context": {
    "request_time_utc": "2026-05-18T12:00:00Z",
    "break_glass": false,
    "human_review_required": false
  }
}
```

**Response (Success):**
```json
{
  "output": "The patient presents with stable cardiac function...",
  "status": "success",
  "policy_decision": "allow",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "review_id": null
}
```

**Response (Pending Review):**
```json
{
  "output": "Human review required. review_id=8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f",
  "status": "pending_human_review",
  "policy_decision": "review",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "review_id": "8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f"
}
```

**Response (Denied):**
```json
{
  "output": "Access denied: abac_tenant_mismatch",
  "status": "denied",
  "policy_decision": "deny",
  "trace_id": "550e8400-e29b-41d4-a716-446655440002",
  "review_id": null
}
```

**Status Codes:**
- `200 OK` - Request processed (check `status` field for actual result)
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid JWT token
- `500 Internal Server Error` - Server error (see logs)

### **2. Review Decision**

**Endpoint:** `POST /reviews/{review_id}/decision`

**Request:**
```json
{
  "approved": true,
  "reviewer_id": "reviewer-1",
  "reason": "Approved for treatment purposes"
}
```

**Response:**
```json
{
  "review_id": "8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f",
  "status": "approved",
  "message": "Review approved and original request executed"
}
```

### **3. Health Check**

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Monitoring & Logs

### **CloudWatch Logs**

Log stream location: `/ecs/healthcare-langgraph-agent`

**Log Format:**
```json
{
  "ts": "2026-05-18T12:34:56.789123+00:00",
  "event_type": "policy_denied",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "reason": "rbac_purpose_not_allowed",
    "role": "billing",
    "tenant_id": "hospital-a",
    "purpose_of_use": "research"
  }
}
```

**Common Event Types:**
- `policy_denied` - Authorization failed
- `guardrail_blocked` - Blocked by guardrail
- `human_review_requested` - Routed to HITL
- `approved` - HITL approved
- `rejected` - HITL rejected
- `error` - Processing error

### **CloudWatch Metrics**

- `CPUUtilization` - Container CPU usage
- `MemoryUtilization` - Container memory usage
- `ECS:service:DesiredTaskCount` - Desired vs running tasks
- `ECS:service:RunningCount` - Currently running tasks

### **Querying Logs**

```bash
# View recent logs
aws logs tail /ecs/healthcare-langgraph-agent --follow \
  --profile anish0637 --region us-east-1

# Search for errors
aws logs filter-log-events \
  --log-group-name /ecs/healthcare-langgraph-agent \
  --filter-pattern "policy_denied" \
  --profile anish0637 --region us-east-1

# Get logs for specific time range
aws logs filter-log-events \
  --log-group-name /ecs/healthcare-langgraph-agent \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --profile anish0637 --region us-east-1
```

---

## FAQ & Troubleshooting

### **Q: How do I update the application code?**

A: Follow the deployment steps:
1. Commit changes to repo
2. Rebuild Docker image: `bash aws/deploy_ecs.sh`
3. Register new task definition (increments revision)
4. Update service: `aws ecs update-service --cluster healthcare-agents --service healthcare-langgraph-agent-svc --task-definition healthcare-langgraph-agent:<new_revision>`

### **Q: How do I scale to multiple instances?**

A: Update the service:
```bash
aws ecs update-service \
  --cluster healthcare-agents \
  --service healthcare-langgraph-agent-svc \
  --desired-count 3 \
  --profile anish0637 --region us-east-1
```

### **Q: How do I view logs for a specific task?**

A: Get the task ID, then:
```bash
aws ecs describe-tasks --cluster healthcare-agents --tasks <task-id> \
  --profile anish0637 --region us-east-1 | jq '.tasks[0].containerInstanceArn'
```

### **Q: Can I use a different Bedrock model?**

A: Update the environment variable in the task definition:
```json
{
  "name": "BEDROCK_MODEL_IDS",
  "value": "anthropic.claude-3-haiku-20240307-v1:0,amazon.nova-micro-v1:0"
}
```

### **Q: What if a Bedrock model is unavailable?**

A: The service automatically falls back to the next model in the list, or returns a safe fallback response if none are available.

### **Q: How do I add a new tool to the agent?**

A: Edit `app/tools.py` and update `app/graph.py` to integrate it into the LangGraph workflow. Test locally with `./run_local.sh`.

### **Q: How do I customize the security policies?**

A: Edit `app/security.py` for RBAC/ABAC/CBAC rules. Examples:
- Change `ROLE_PERMISSIONS` for new roles
- Add ABAC checks in the `authorize()` function
- Modify CBAC time windows or conditions

### **Q: Is the service encrypted at rest?**

A: **DynamoDB**: Yes, AWS managed encryption keys (default)  
**CloudWatch Logs**: Yes, AWS managed encryption  
**In-transit**: HTTPS via ALB (when configured)

### **Q: How do I test locally before deploying?**

A: 
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure environment variables
./run_local.sh        # Start on http://localhost:8080
```

### **Q: How do I check if a task is stuck?**

A: 
```bash
aws ecs describe-tasks --cluster healthcare-agents --tasks <task-arn> \
  --profile anish0637 --region us-east-1 | jq '.tasks[0] | {lastStatus, stopCode, stoppingAt}'
```

If stuck in PENDING, check:
- VPC/subnet availability
- IAM role permissions
- ECR image accessibility
- Container logs in CloudWatch

---

## Cost Optimization

### **Current Architecture Costs**

- **ECS Fargate**: ~$0.03-0.05/hour (512 CPU, 1GB memory)
- **DynamoDB**: ~$0.25/million read units, pay-per-request
- **CloudWatch Logs**: ~$0.50/GB ingested, $0.03/GB stored
- **ECR**: $0.10/GB stored, free data transfer within region
- **Data Transfer**: Minimal (within AWS region)

**Monthly estimate**: ~$50-100 for single task, scales with usage

### **Cost Reduction Tips**

1. **Use on-demand DynamoDB billing** (included)
2. **Set CloudWatch Log retention** to 7-30 days instead of unlimited
3. **Use Spot Fargate** for non-critical workloads (50% discount)
4. **Consolidate tasks** in a single Fargate task definition
5. **Set task auto-scaling** based on CloudWatch metrics

---

## Security Best Practices

1. ✅ **Never log sensitive data** - Automatic redaction in place
2. ✅ **Rotate JWT secrets** regularly
3. ✅ **Enable VPC endpoints** for DynamoDB and ECR (private access)
4. ✅ **Use IAM roles** instead of access keys
5. ✅ **Enable CloudTrail** for audit of AWS API calls
6. ✅ **Use SSL/TLS** with ALB for HTTPS
7. ✅ **Implement rate limiting** at ALB or API gateway
8. ✅ **Regular security reviews** of audit logs

---

## Support & Maintenance

**On-call contacts**: DevOps, Security, Data Protection teams  
**Incident response**: Check CloudWatch logs, review recent policy changes, check Bedrock model availability  
**Maintenance windows**: Apply security patches monthly, test new Bedrock models before production  

For questions or issues, refer to CloudWatch logs with `trace_id` for correlation.

---

**Document Version**: 1.0  
**Last Reviewed**: May 18, 2026  
**Next Review**: August 18, 2026
