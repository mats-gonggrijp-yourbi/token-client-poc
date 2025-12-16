param projectName string = 'tc'  // token client
@allowed([
  'stg'
  'prd'
])
param environment string

// Get the existing id references
resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectName}-server-${environment}weu'
}


resource gitHubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectName}-github-${environment}-weu'
}


resource containerRegistry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' existing = {
  name: 'cr${projectName}${environment}weu'
}

// Creates Log Analytics Workspace.
module logAnalyticsWorkspace 'log_analytics_workspace.bicep' = {
  params: {
    environment: environment
    stackName: projectName
  }
}

// Creates Container Apps Environment required for Container Apps.
module containerAppsEnvironment 'container_apps_environment.bicep' = {
  params: {
    environment: environment
    logAnalyticsCustomerId: logAnalyticsWorkspace.outputs.customerId
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
    stackName: projectName
  }
}

// Creates Container Apps server and processor.
module containerApps 'container_apps.bicep' = {
  params: {
    projectName: projectName
    containerAppEnvironmentId: containerAppsEnvironment.outputs.id
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    environment: environment
    serverIdentityId: serverIdentity.id
    gitHubIdentityId: gitHubIdentity.id
    githubIdentityPrincipalId: gitHubIdentity.properties.principalId
  }
}
