#!/bin/bash

if [[ -z "${1}" ]]; then
	exit 1
fi
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_ENV="${1}"

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
docker tag denario-be:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/denario-${AWS_ENV}-be:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/denario-${AWS_ENV}-be:latest

docker tag denario-fe:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/denario-${AWS_ENV}-fe:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/denario-${AWS_ENV}-fe:latest

