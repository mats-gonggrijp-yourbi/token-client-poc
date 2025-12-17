param projectAlias string
param logAnalyticsCustomerId string
param logAnalyticsWorkspaceName string
@allowed([
  'stg'
  'prd'
])
param environmentAlias string
param addressPrefix string
var acaSubnetName string = 'sn-${projectAlias}-server-${environmentAlias}-weu'

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2025-07-01' existing = {
  name: logAnalyticsWorkspaceName
}
var logAnalyticsPrimarySharedKey = logAnalyticsWorkspace.listKeys().primarySharedKey


resource vnet 'Microsoft.Network/virtualNetworks@2025-01-01' existing = {
  name: 'vnet-${projectAlias}-${environmentAlias}-weu'
}

resource subnet 'Microsoft.Network/virtualNetworks/subnets@2025-01-01' = {
  name: acaSubnetName
  parent: vnet
  properties: {
    addressPrefix: addressPrefix
    delegations: []
  }
}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: 'cae-${projectAlias}-${environmentAlias}-weu'
  location: resourceGroup().location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsPrimarySharedKey
      }
    }
    zoneRedundant: false
    vnetConfiguration: {
      infrastructureSubnetId: subnet.id
      internal: true
    }
  }
}

output id string = containerAppEnvironment.id
output name string = containerAppEnvironment.name
output domain string = containerAppEnvironment.properties.defaultDomain
output staticIp string = containerAppEnvironment.properties.staticIp
