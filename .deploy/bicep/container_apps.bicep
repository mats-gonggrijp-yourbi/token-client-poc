// Parameters
param projectName string
param containerAppEnvironmentId string
param containerRegistryLoginServer string
param serverIdentityId string
@allowed([
  'stg'
  'prd'
])
param environment string
param githubIdentityPrincipalId string
param gitHubIdentityId string

// {resource_alias}-{project_alias}-{project_service_alias}-{environment_alias}-{region_alias}-{ybi_key}-{instance_number

param imageName string = 'token-client:latest'

resource serverUami 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectName}-serv-${environment}-weu'
}

// Creation of server resource.
resource server 'Microsoft.App/containerApps@2024-10-02-preview' = {
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${serverIdentityId}': {}
    }
  }
  kind: 'containerapps'
  location: resourceGroup().location
  name: 'ca-${projectName}-server-${environment}-weu'
  properties: {
    configuration: {
      secrets: []
      activeRevisionsMode: 'Single'
      identitySettings: []
      ingress: {
        allowInsecure: false
        external: false
        targetPort: 8080
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        transport: 'Auto'
      }
      maxInactiveRevisions: 100
      registries: [
        {
          server: containerRegistryLoginServer
          identity: serverIdentityId
        }
      ]
    }
    environmentId: containerAppEnvironmentId
    managedEnvironmentId: containerAppEnvironmentId
    template: {
      containers: [
        {
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: serverUami.properties.clientId

            }
          ]
          image: '${containerRegistryLoginServer}/${imageName}'
          imageType: 'ContainerImage'
          name: 'ca-${projectName}-server-${environment}-weu'
          probes: []
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        cooldownPeriod: 300
        maxReplicas: 10
        minReplicas: 1
        pollingInterval: 30
        rules: []
      }
      volumes: []
    }
  }
}

// server contributor role.
var serverContributorRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '358470bc-b998-42bd-ab17-a7e34c199c0f'
)

// Contributor role assignment for GitHub UAMI to server.
// This is needed to force a refresh on the server.
resource gitHubServerContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(server.id, gitHubIdentityId, serverContributorRoleId)
  scope: server
  properties: {
    principalId: githubIdentityPrincipalId
    roleDefinitionId: serverContributorRoleId
    principalType: 'ServicePrincipal'
  }
}
