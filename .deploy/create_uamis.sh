#!/usr/bin/env bash
set -euo pipefail

# Require ENVIRONMENT to be passed in
if [ $# -lt 1 ]; then
  echo "Usage: $0 <ENVIRONMENT>"
  exit 1
fi

ENVIRONMENT="$1"

echo ENVIRONMENT

# Run deployment
az deployment group create \
  --resource-group "ybi-webhook-client-$ENVIRONMENT" \
  --template-file "./bicep/uami.bicep" \
  --parameters projectAlias="wc" environment="$ENVIRONMENT" \
  --debug
