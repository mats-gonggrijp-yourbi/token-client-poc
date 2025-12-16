@description('Abbreviated name of stack')
param stackName string
@description('Specifies the deployment environment')
@allowed([
  'development'
  'staging'
  'production'
])
param environment string

resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'uami-${stackName}-server-${environment}'
}

resource processorIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'uami-${stackName}-processor-${environment}'
}

var acrRoleIdPull = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)

// Reference to existing Container Registry which is created by deployment script.
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' existing = {
  name: 'cr${stackName}${environment}'
}

resource serverAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, serverIdentity.id, acrRoleIdPull)
  scope: containerRegistry
  properties: {
    principalId: serverIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPull
  }
}

// Assign processor to Acr with `pull` role.
resource processorAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, processorIdentity.id, acrRoleIdPull)
  scope: containerRegistry
  properties: {
    principalId: processorIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPull
  }
}

// Built-in AcrPush role definition
var acrRoleIdPush = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8311e382-0749-4cb8-b61a-304f252e45ec' // AcrPush
)


// Reference to existing UAMI of GitHub.
resource gitHubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'uami-${stackName}-github-${environment}'
}

// Assign AcrPush role to Github Actions UAMI
resource acrPushAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, gitHubIdentity.id, 'AcrPushUAMI')
  scope: containerRegistry
  properties: {
    principalId: gitHubIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPush
    principalType: 'ServicePrincipal'
  }
}
