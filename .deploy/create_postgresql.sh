#!/usr/bin/environmentAlias bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <environmentAlias> <adminPassword> <addressPrefix>"
  exit 1
fi

environmentAlias="$1"
adminPassword="$2"
addressPrefix="$3"

az deployment group create \
  --debug  \
  --resource-group "rg-tc-$environmentAlias-weu" \
  --template-file "./bicep/postgresql.bicep" \
  --parameters \
    projectAlias="tc" \
    environmentAlias="$environmentAlias" \
    adminPassword="$adminPassword" \
    addressPrefix="$addressPrefix" \

