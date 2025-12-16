// Variables
param stackName string
param logAnalyticsCustomerId string
param logAnalyticsWorkspaceName string

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}
var logAnalyticsPrimarySharedKey = logAnalyticsWorkspace.listKeys().primarySharedKey

@description('Name of environment')
param environment string

// Creation of Container App Environment resource.
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: 'cae-${stackName}-${environment}-${resourceGroup().location}'
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
    vnetConfiguration: {}
  }
}

output id string = containerAppEnvironment.id
output name string = containerAppEnvironment.name
output domain string = containerAppEnvironment.properties.defaultDomain
output staticIp string = containerAppEnvironment.properties.staticIp
