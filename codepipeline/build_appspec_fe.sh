#!/usr/bin/env bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cat << EOF > appspec.yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "arn:aws:ecs:us-east-1:${AWS_ACCOUNT_ID}:task-definition/genomecentral-${1}-fe:${TASKREV_FE}"
        LoadBalancerInfo:
          ContainerName: "fe"
          ContainerPort: 3000
        PlatformVersion: "LATEST"
EOF
