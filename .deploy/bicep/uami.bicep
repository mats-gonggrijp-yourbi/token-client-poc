param projectAlias string
@allowed([
  'stg'
  'prd'
])
param environmentAlias string

resource githubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  location: resourceGroup().location
  name: 'id-${projectAlias}-gith-${environmentAlias}-weu'
}

resource githubFederatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = {
  name: 'fed-${projectAlias}-weu'
  parent: githubIdentity
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:Your-BI/token-client:environmentAlias:${environmentAlias}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

output githubIdentityTenantId string = githubIdentity.properties.tenantId
output githubIdentityClientId string = githubIdentity.properties.clientId
output githubIdentitySubscriptionId string = subscription().subscriptionId
