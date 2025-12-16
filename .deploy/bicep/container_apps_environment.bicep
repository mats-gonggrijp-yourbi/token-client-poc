// Variables
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

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}
var logAnalyticsPrimarySharedKey = logAnalyticsWorkspace.listKeys().primarySharedKey


resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' existing = {
  name: 'vnet-${projectAlias}-${environmentAlias}-weu'
}

@description('Name of environment')
param environment string

resource acaSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = {
  name: acaSubnetName
  parent: vnet
  properties: {
    addressPrefix: addressPrefix
    delegations: [
      {
        name: 'aca-delegation'
        properties: {
          serviceName: 'Microsoft.Web/serverFarms'
        }
      }
    ]
  }
}

// Creation of Container App Environment resource.
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: 'cae-${projectAlias}-${environment}-weu'
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
      infrastructureSubnetId: acaSubnet.id
    }
  }
}

output id string = containerAppEnvironment.id
output name string = containerAppEnvironment.name
output domain string = containerAppEnvironment.properties.defaultDomain
output staticIp string = containerAppEnvironment.properties.staticIp
