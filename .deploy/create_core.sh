#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <ENVIRONMENT> <GITHUB_ACCESS_TOKEN> <ADMIN_KEY> <SQL_CATALOG_PASSWORD>"
  exit 1
fi

ENVIRONMENT="$1"
GITHUB_ACCESS_TOKEN="$2"
ADMIN_KEY="$3"
SQL_CATALOG_PASSWORD="$4"

echo "Deploying environment: $ENVIRONMENT"

# Run deployment
az deployment group create \
  --resource-group "ybi-webhook-client-$ENVIRONMENT" \
  --template-file "./bicep/main.bicep" \
  --parameters \
    projectAlias="wc" \
    environment="$ENVIRONMENT" \
    githubAccessToken="$GITHUB_ACCESS_TOKEN" \
    adminKey="$ADMIN_KEY" \
    sqlCatalogPassword="$SQL_CATALOG_PASSWORD" \
    sqlCatalogUrl="ybisql.public.cda17043cf16.database.windows.net" \
    sqlCatalogPort="3342" \
    sqlCatalogUsername="ybi_sql_admin" \
  --debug
