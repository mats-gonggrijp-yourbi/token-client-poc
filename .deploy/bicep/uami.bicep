// Variables
param projectName string
@allowed([
  'stg'
  'prd'
])
param environment string

// User Assigned Managed Identity (UAMI) for GitHub.
resource githubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  location: resourceGroup().location
  name: 'uami-${projectName}-github-${environment}'
}

// Federated credential for GitHub repo `webhook-client`.
// The access is bound by the environment.
// This means that `main` repo can only push to development etc.
resource githubFederatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = {
  name: 'fed-${projectName}-${resourceGroup().location}'
  parent: githubIdentity
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:Your-BI/webhook-client:environment:${environment}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

// Creation of User-Assigned Managed Identity (UAMI) for both apps.
// This UAMI is provisioned explicitly before to avoid dependency cycles.
resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  location: resourceGroup().location
  name: 'uami-${projectName}-server-${environment}'
}

// These outputs are used for GitHub Actions secrets.
// These have to be created there, which is specified in the deploy guide.
output githubIdentityTenantId string = githubIdentity.properties.tenantId
output githubIdentityClientId string = githubIdentity.properties.clientId
output githubIdentitySubscriptionId string = subscription().subscriptionId
