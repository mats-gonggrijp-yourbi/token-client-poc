param projectAlias string
@allowed([
  'stg'
  'prd'
])
param environmentAlias string

resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectAlias}-server-${environmentAlias}-weu'
}

var acrRoleIdPull = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)


resource containerRegistry 'Microsoft.ContainerRegistry/registries@2024-11-01-preview' existing = {
  name: 'cr${projectAlias}${environmentAlias}weu'
}

resource serverAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, serverIdentity.id, acrRoleIdPull)
  scope: containerRegistry
  properties: {
    principalId: serverIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPull
  }
}


var acrRoleIdPush = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8311e382-0749-4cb8-b61a-304f252e45ec' 
)



resource gitHubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectAlias}-gith-${environmentAlias}-weu'
}


resource acrPushAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, gitHubIdentity.id, 'AcrPushUAMI')
  scope: containerRegistry
  properties: {
    principalId: gitHubIdentity.properties.principalId
    roleDefinitionId: acrRoleIdPush
    principalType: 'ServicePrincipal'
  }
}
