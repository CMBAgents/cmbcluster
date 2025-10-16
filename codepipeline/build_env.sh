#!/usr/bin/env bash
echo "DEV_MODE=false" > .env
echo "DEBUG=false" >> .env
echo "API_URL=http://localhost:8000" >> .env
echo "FRONTEND_URL=http://localhost:8501" >> .env


#echo "SSH_KEY=${PWD}/.ssh/id_aws_cb_deploy_ed25519" >> .env

# mkdir .ssh/
# chmod 700 .ssh
# echo "${GITHUB_SSH_PRIV_KEY}" >.ssh/id_aws_cb_deploy_ed25519
# chmod 600 .ssh/id_aws_cb_deploy_ed25519
