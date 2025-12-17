@allowed([
  'stg'
  'prd'
])
param environmentAlias string
param projectAlias string
param addressPrefix string

var vnetName string = 'vnet-${projectAlias}-${environmentAlias}-weu'
var DNSDomainName string = 'pl-${projectAlias}-back-${environmentAlias}-weu.postgres.database.azure.com'

resource vnet 'Microsoft.Network/virtualNetworks@2024-10-01' = {
  location: resourceGroup().location
  name: vnetName
  tags: {
    project_name: projectAlias
    environmentAlias: environmentAlias
    region: resourceGroup().location
    owner_email: 'mats.gonggrijp@yourbi.nl'
    project_service: 'back'
    repo_url: 'NOT-YET-CREATED'
  }
  properties: {
    addressSpace: {
      addressPrefixes: [addressPrefix]
    }
    enableDdosProtection: false
    enableVmProtection: false
    encryption: {
      enabled: true
      enforcement: 'AllowUnencrypted'
    }
    flowTimeoutInMinutes: 30
    privateEndpointVNetPolicies: 'Basic'
  }
}

resource privateDNSZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: DNSDomainName
  location: 'global'
}

resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDNSZone
  name: 'vnet-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}
