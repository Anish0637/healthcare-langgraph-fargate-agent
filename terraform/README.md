# Terraform Deployment

## Usage

```bash
cd terraform
terraform init
terraform plan -var="container_image=<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-langgraph-agent:latest"
terraform apply -var="container_image=<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-langgraph-agent:latest"
```

This creates:
- VPC + public subnets
- ALB + target group + listener
- ECS Cluster + Fargate Service
- DynamoDB memory table with TTL
- IAM task execution and task roles
- CloudWatch log group

## Notes

- This is a production-oriented starter, not a complete hardened baseline.
- For stricter healthcare controls, add:
  - Private subnets + NAT or VPC endpoints
  - WAF and Shield
  - KMS CMKs and stricter key policies
  - Secrets Manager for all secrets
  - OIDC auth at ALB/API gateway edge
  - Immutable audit sinks and SIEM forwarding
