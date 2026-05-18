#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE:=default}"
: "${AWS_REGION:=us-east-1}"
: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${ECR_REPO:=healthcare-langgraph-agent}"
: "${ECS_TASK_FAMILY:=healthcare-langgraph-agent}"

AWS="aws --profile ${AWS_PROFILE} --region ${AWS_REGION}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

${AWS} ecr describe-repositories --repository-names "${ECR_REPO}" >/dev/null 2>&1 || \
  ${AWS} ecr create-repository --repository-name "${ECR_REPO}" >/dev/null

${AWS} ecr get-login-password | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "${ECR_REPO}:latest" "${ROOT_DIR}"
docker tag "${ECR_REPO}:latest" "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"
docker push "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"

echo "Image pushed. Register task definition using aws/ecs-task-definition.json after replacing placeholders."
