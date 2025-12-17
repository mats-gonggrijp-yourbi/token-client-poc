#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 5 ]; then
  echo "Usage: $0 <ENVIRONMENT> <POSTGRES_PASSWORD> <POSTGRES_URL> <ADDRESS_PREFIX> <IMAGE_NAME>"
  exit 1
fi

ENVIRONMENT="$1"
POSTGRES_PASSWORD="$2"
POSTGRES_URL="$3"
ADDRESS_PREFIX="$4"
IMAGE_NAME="$5"

echo "Deploying environment: $ENVIRONMENT"

# Run deployment
az deployment group create \
  --resource-group "rg-tc-$ENVIRONMENT-weu" \
  --template-file "./bicep/main.bicep" \
  --parameters \
    projectAlias="tc" \
    environmentAlias="$ENVIRONMENT" \
    addressPrefix="$ADDRESS_PREFIX" \
    postgresPassword="$POSTGRES_PASSWORD" \
    postgresUrl="$POSTGRES_URL" \
    postgresPort="3342" \
    postgresUsername="ybi_postgresql_admin_$ENVIRONMENT" \
    imageName="$IMAGE_NAME" \
  --debug
