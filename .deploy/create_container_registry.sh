#!/usr/bin/env bash
set -euo pipefail

# Require ENVIRONMENT to be passed in
if [ $# -lt 1 ]; then
  echo "Usage: $0 <ENVIRONMENT>"
  exit 1
fi

ENVIRONMENT="$1"

# Run deployment
az deployment group create \
  --resource-group "ybi-webhook-client-$ENVIRONMENT" \
  --template-file "./bicep/container_registry.bicep" \
  --parameters projectAlias="wc" environment="$ENVIRONMENT" \
  --debug
