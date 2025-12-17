param projectAlias string = 'tc'  
@allowed([
  'stg'
  'prd'
])
param environmentAlias string
param containerAppsAddressPrefix string

resource gitHubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectAlias}-github-${environmentAlias}-weu'
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' existing = {
  name: 'cr${projectAlias}${environmentAlias}weu'
}

module logAnalyticsWorkspace 'log_analytics_workspace.bicep' = {
  params: {
    environmentAlias: environmentAlias
    projectAlias: projectAlias
  }
}


module containerAppsEnvironment 'container_apps_environment.bicep' = {
  params: {
    environmentAlias: environmentAlias
    logAnalyticsCustomerId: logAnalyticsWorkspace.outputs.customerId
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
    projectAlias: projectAlias
    addressPrefix: containerAppsAddressPrefix
  }
}


module containerApps 'container_apps.bicep' = {
  params: {
    projectAlias: projectAlias
    containerAppEnvironmentId: containerAppsEnvironment.outputs.id
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    environmentAlias: environmentAlias
    gitHubIdentityId: gitHubIdentity.id
    githubIdentityPrincipalId: gitHubIdentity.properties.principalId
  }
}
