import type { IdentityProviderType } from '@/types/identity-provider';
import type { FieldDescriptor } from './connectorFields';

export const IDENTITY_PROVIDER_FIELDS: Record<IdentityProviderType, FieldDescriptor[]> = {
  azure_entra_id: [
    { name: 'tenant_id', label: 'Tenant ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true, secret: false },
    { name: 'client_id', label: 'Client ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true, secret: false },
    { name: 'client_secret', label: 'Client Secret', type: 'password', placeholder: '', required: true, secret: true },
  ],
  aws_iam: [
    { name: 'access_key_id', label: 'Access Key ID', type: 'text', placeholder: 'AKIAIOSFODNN7EXAMPLE', required: true, secret: false },
    { name: 'secret_access_key', label: 'Secret Access Key', type: 'password', placeholder: '', required: true, secret: true },
    { name: 'region', label: 'Region', type: 'text', placeholder: 'us-east-1', required: true, secret: false },
  ],
  gcp: [
    { name: 'project_id', label: 'Project ID', type: 'text', placeholder: 'my-project-123', required: true, secret: false },
    { name: 'service_account_json', label: 'Service Account JSON', type: 'password', placeholder: '', required: true, secret: true },
  ],
  okta: [
    { name: 'domain', label: 'Okta Domain', type: 'text', placeholder: 'dev-123456.okta.com', required: true, secret: false },
    { name: 'api_token', label: 'API Token', type: 'password', placeholder: '', required: true, secret: true },
  ],
};
