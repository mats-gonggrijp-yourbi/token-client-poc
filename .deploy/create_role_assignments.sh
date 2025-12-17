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
  --resource-group "rg-tc-$ENVIRONMENT-weu" \
  --template-file "./bicep/assign_roles.bicep" \
  --parameters projectAlias="tc" environmentAlias="$ENVIRONMENT" \
  --debug