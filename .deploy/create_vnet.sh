  #!/usr/bin/environmentAlias bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <environmentAlias> <addressPrefix>"
  exit 1
fi

environmentAlias="$1"
addressPrefix="$2"

az deployment group create \
  --debug \
  --resource-group "rg-tc-$environmentAlias-weu" \
  --template-file "./bicep/virtual_network.bicep" \
  --parameters \
    environmentAlias="$environmentAlias" \
    projectAlias="tc" \
    addressPrefix="$addressPrefix" 
