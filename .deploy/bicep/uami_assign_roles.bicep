param projectName string
@allowed([
  'stg'
  'prd'
])
param environment string


// Get the server (token client) identity
resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectName}-server-${environment}-weu'
}

var acrRoleIdPull = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)

// Reference to existing Container Registry which is created by deployment script.
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' existing = {
  name: 'cr${projectName}${environment}weu'
}

resource serverAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, serverIdentity.id, acrRoleIdPull)
  scope: containerRegistry
  properties: {
    principalId: serverIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPull
  }
}

// Built-in AcrPush role definition
var acrRoleIdPush = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8311e382-0749-4cb8-b61a-304f252e45ec' // AcrPush
)


// Get the github identity
resource gitHubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectName}-gith-${environment}-weu'
}

// Assign it AcrPush 
resource acrPushAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, gitHubIdentity.id, 'AcrPushUAMI')
  scope: containerRegistry
  properties: {
    principalId: gitHubIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPush
    principalType: 'ServicePrincipal'
  }
}
