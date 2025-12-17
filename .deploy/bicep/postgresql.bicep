param projectAlias string
@allowed([
  'stg'
  'prd'
])
param environmentAlias string

@secure()
param adminPassword string
param addressPrefix string

var dbName string = 'psql-${projectAlias}-${environmentAlias}-weu' 
var subnetName string = 'snet-${projectAlias}-back-${environmentAlias}-weu' 
var vnetName string = 'vnet-${projectAlias}-${environmentAlias}-weu'

resource vnet 'Microsoft.Network/virtualNetworks@2024-10-01' existing = {
  name: vnetName
}

resource subnet 'Microsoft.Network/virtualNetworks/subnets@2024-10-01' = {
    parent: vnet
    name: subnetName
    properties: {
      addressPrefix: addressPrefix
      delegations: [
        {
          name: 'pgsql-delegation'
          properties: {
            serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
          }
        }
      ]
      privateEndpointNetworkPolicies: 'Disabled'
      privateLinkServiceNetworkPolicies: 'Disabled'
    }
}

resource postgresPrivateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' existing = {
  name: 'pl-${projectAlias}-back-${environmentAlias}-weu.postgres.database.azure.com'
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers@2025-01-01-preview' = {
  name: dbName
  location: 'westeurope'
  sku: {
    name: 'Standard_D2ds_v5'
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '17'
    administratorLogin: 'ybi_postgresql_admin_${environmentAlias}'
    administratorLoginPassword: adminPassword
    availabilityZone: '1'
    storage: {
      iops: 240
      tier: 'P6'
      storageSizeGB: 64
      autoGrow: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: subnet.id
      privateDnsZoneArmResourceId: postgresPrivateDnsZone.id
      publicNetworkAccess: 'Disabled'
    }
    dataEncryption: {
      type: 'SystemManaged'
    }
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Enabled'
      tenantId: '8712cdc8-96b8-4c05-90ae-0e3d0c98e3d7'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    replicationRole: 'Primary'
  }
  tags: {
    project_name: projectAlias
    environmentAlias: environmentAlias
    region: 'westeurope'
    owner_email: 'mats.gonggrijp@yourbi.nl'
    project_service: 'backend'
    repo_url: 'https://github.com/Your-BI/token-client'
  }
}
