param projectAlias string
param environmentAlias string

var logAnalyticsWorkspaceName = 'log-${projectAlias}-${environmentAlias}-weu'
var appInsightsName = 'appi-${projectAlias}-${environmentAlias}-weu'


resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: resourceGroup().location
  properties: {
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
  }
}


resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: resourceGroup().location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}


output name string = logAnalyticsWorkspace.name
output customerId string = logAnalyticsWorkspace.properties.customerId

