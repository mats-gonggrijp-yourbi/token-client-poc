
param projectAlias string
param containerAppEnvironmentId string
param containerRegistryLoginServer string
@allowed([
  'stg'
  'prd'
])
param environmentAlias string
param githubIdentityPrincipalId string
param gitHubIdentityId string
param imageName string
@secure()
param postgresPassword string
param postgresUsername string
param postgresUrl string
param postgresPort string

resource serverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: 'id-${projectAlias}-server-${environmentAlias}-weu'
}

resource server 'Microsoft.App/containerApps@2025-07-01' = {
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${serverIdentity.id}': {}
    }
  }
  kind: 'containerapps'
  location: resourceGroup().location
  name: 'ca-${projectAlias}-server-${environmentAlias}-weu'
  properties: {
    configuration: {
      secrets: [
        {
          name: 'postgres-password'
          value: postgresPassword
        }
      ]
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
          identity: serverIdentity.id 
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
              value: environmentAlias
            }
            {
              name: 'POSTGRES_PASSWORD'
              secretRef: 'postgres-password'
            }
            {
              name: 'POSTGRES_URL'
              value: postgresUrl
            }
            {
              name: 'POSTGRES_PORT'
              value: postgresPort
            }
            {
              name: 'POSTGRES_USERNAME'
              value: postgresUsername
            }
          ]
          image: '${containerRegistryLoginServer}/${imageName}'
          name: 'ca-${projectAlias}-server-${environmentAlias}-weu'
          probes: []
          resources: {
            cpu: 1
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

var serverContributorRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '358470bc-b998-42bd-ab17-a7e34c199c0f'
)

resource gitHubServerContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(server.id, gitHubIdentityId, serverContributorRoleId)
  scope: server
  properties: {
    principalId: githubIdentityPrincipalId
    roleDefinitionId: serverContributorRoleId
    principalType: 'ServicePrincipal'
  }
}
