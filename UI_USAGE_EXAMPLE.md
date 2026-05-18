# Agent UI Usage Example

Last updated: 18 May 2026

This guide shows how to use the deployed Healthcare LangGraph Agent from a browser UI.

## 1. Open The API UI

Current live endpoint:
http://13.223.229.249:8080

Swagger UI:
http://13.223.229.249:8080/docs

Health check:
http://13.223.229.249:8080/health

Expected health response:
{
  "status": "ok"
}

## 2. Invoke The Agent From UI

1. Open /docs in the browser.
2. Find POST /invoke.
3. Click Try it out.
4. Paste the example payload below.
5. Click Execute.
6. Review output, status, policy_decision, trace_id.

Example request payload (success path):
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
    "data_class": "restricted"
  },
  "context": {
    "request_time_utc": "2026-05-18T12:00:00Z"
  }
}

Typical success response:
{
  "output": "...agent summary...",
  "status": "success",
  "policy_decision": "allow",
  "trace_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "review_id": null
}

## 3. Test A Denied Policy Case

Use this payload to trigger RBAC deny:
{
  "message": "Can I use this patient data for treatment?",
  "user_id": "u-456",
  "role": "researcher",
  "tenant_id": "hospital-a",
  "purpose_of_use": "treatment",
  "patient_context": {
    "patient_id": "p-001",
    "consent": true
  },
  "attributes": {
    "env": "prod"
  },
  "context": {
    "request_time_utc": "2026-05-18T12:00:00Z"
  }
}

Expected behavior:
- status: denied
- policy_decision: deny
- output includes rbac_purpose_not_allowed

## 4. Test Human Review Required Case

Use this payload to trigger review queue:
{
  "message": "Emergency access to full chart",
  "user_id": "u-789",
  "role": "clinician",
  "tenant_id": "hospital-a",
  "purpose_of_use": "treatment",
  "patient_context": {
    "patient_id": "p-001",
    "consent": true
  },
  "attributes": {
    "risk_level": "high",
    "env": "prod"
  },
  "context": {
    "request_time_utc": "2026-05-18T12:00:00Z",
    "break_glass": true
  }
}

Expected behavior:
- status: pending_human_review
- policy_decision: review
- review_id returned

## 5. Approve Or Reject A Review

In Swagger UI, use POST /reviews/{review_id}/decision.

Example approve payload:
{
  "approved": true,
  "reviewer_id": "reviewer-1",
  "reason": "Approved for emergency treatment"
}

Example reject payload:
{
  "approved": false,
  "reviewer_id": "reviewer-1",
  "reason": "Insufficient justification"
}

## 6. Notes For Production Use

- Current access uses ECS task public IP, which can change after redeploy.
- For stable URL, place ECS service behind ALB and Route 53 DNS.
- If JWT is enabled later, pass Authorization header in Swagger.

## 7. Quick Troubleshooting

If /docs opens but /invoke fails:
1. Check /health first.
2. Verify ECS service running count is 1.
3. Check CloudWatch logs group:
   /ecs/healthcare-langgraph-agent
4. Redeploy service if tasks are cycling.
