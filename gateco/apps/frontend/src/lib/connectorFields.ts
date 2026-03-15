import type { ConnectorType } from '@/types/connector';

export interface SearchConfigFieldDescriptor {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select';
  placeholder: string;
  required: boolean;
  options?: string[];
}

export const SEARCH_CONFIG_FIELDS: Record<ConnectorType, SearchConfigFieldDescriptor[]> = {
  pgvector: [
    { name: 'table_name', label: 'Table or view name', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'vector_column', label: 'Vector column', type: 'text', placeholder: 'embedding', required: true },
    { name: 'id_column', label: 'ID column', type: 'text', placeholder: 'id', required: true },
    { name: 'content_column', label: 'Content column', type: 'text', placeholder: 'content', required: false },
    { name: 'metric', label: 'Distance metric', type: 'select', placeholder: 'cosine', required: false, options: ['cosine', 'l2', 'inner_product'] },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  supabase: [
    { name: 'table_name', label: 'Table or view name', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'vector_column', label: 'Vector column', type: 'text', placeholder: 'embedding', required: true },
    { name: 'id_column', label: 'ID column', type: 'text', placeholder: 'id', required: true },
    { name: 'content_column', label: 'Content column', type: 'text', placeholder: 'content', required: false },
    { name: 'metric', label: 'Distance metric', type: 'select', placeholder: 'cosine', required: false, options: ['cosine', 'l2', 'inner_product'] },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  neon: [
    { name: 'table_name', label: 'Table or view name', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'vector_column', label: 'Vector column', type: 'text', placeholder: 'embedding', required: true },
    { name: 'id_column', label: 'ID column', type: 'text', placeholder: 'id', required: true },
    { name: 'content_column', label: 'Content column', type: 'text', placeholder: 'content', required: false },
    { name: 'metric', label: 'Distance metric', type: 'select', placeholder: 'cosine', required: false, options: ['cosine', 'l2', 'inner_product'] },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  pinecone: [
    { name: 'index_name', label: 'Index name', type: 'text', placeholder: 'my-index', required: true },
    { name: 'namespace', label: 'Namespace', type: 'text', placeholder: 'default', required: false },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  qdrant: [
    { name: 'collection_name', label: 'Collection name', type: 'text', placeholder: 'documents', required: true },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '768', required: false },
  ],
  weaviate: [
    { name: 'class_name', label: 'Class name', type: 'text', placeholder: 'Document', required: true },
    { name: 'properties', label: 'Properties (comma-separated)', type: 'text', placeholder: 'content', required: false },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  milvus: [
    { name: 'collection_name', label: 'Collection name', type: 'text', placeholder: 'documents', required: true },
    { name: 'vector_field', label: 'Vector field', type: 'text', placeholder: 'embedding', required: false },
    { name: 'output_fields', label: 'Output fields (comma-separated)', type: 'text', placeholder: 'content', required: false },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '384', required: false },
  ],
  opensearch: [
    { name: 'index_name', label: 'Index name', type: 'text', placeholder: 'vectors', required: true },
    { name: 'vector_field', label: 'Vector field', type: 'text', placeholder: 'embedding', required: true },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
  chroma: [
    { name: 'collection_name', label: 'Collection name', type: 'text', placeholder: 'documents', required: true },
    { name: 'expected_dimension', label: 'Expected dimension', type: 'number', placeholder: '1536', required: false },
  ],
};

export type IngestionConfigFieldDescriptor = SearchConfigFieldDescriptor;

export const INGESTION_CONFIG_FIELDS: Record<ConnectorType, IngestionConfigFieldDescriptor[]> = {
  pgvector: [
    { name: 'target_table', label: 'Target table', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'id_field', label: 'ID field', type: 'text', placeholder: 'id', required: false },
    { name: 'content_field', label: 'Content field', type: 'text', placeholder: 'content', required: false },
    { name: 'upsert_mode', label: 'Upsert mode', type: 'select', placeholder: 'insert', required: false, options: ['insert', 'upsert'] },
  ],
  supabase: [
    { name: 'target_table', label: 'Target table', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'id_field', label: 'ID field', type: 'text', placeholder: 'id', required: false },
    { name: 'content_field', label: 'Content field', type: 'text', placeholder: 'content', required: false },
    { name: 'upsert_mode', label: 'Upsert mode', type: 'select', placeholder: 'insert', required: false, options: ['insert', 'upsert'] },
  ],
  neon: [
    { name: 'target_table', label: 'Target table', type: 'text', placeholder: 'embeddings', required: true },
    { name: 'id_field', label: 'ID field', type: 'text', placeholder: 'id', required: false },
    { name: 'content_field', label: 'Content field', type: 'text', placeholder: 'content', required: false },
    { name: 'upsert_mode', label: 'Upsert mode', type: 'select', placeholder: 'insert', required: false, options: ['insert', 'upsert'] },
  ],
  pinecone: [
    { name: 'target_index', label: 'Target index', type: 'text', placeholder: 'my-index', required: true },
    { name: 'namespace', label: 'Namespace', type: 'text', placeholder: 'default', required: false },
  ],
  qdrant: [
    { name: 'target_collection', label: 'Target collection', type: 'text', placeholder: 'documents', required: true },
  ],
  weaviate: [],
  milvus: [],
  opensearch: [],
  chroma: [],
};

export interface FieldDescriptor {
  name: string;
  label: string;
  type: 'text' | 'number' | 'password';
  placeholder: string;
  required: boolean;
  secret: boolean;
}

export const CONNECTOR_FIELDS: Record<ConnectorType, FieldDescriptor[]> = {
  pgvector: [
    { name: 'host', label: 'Host', type: 'text', placeholder: 'db.example.com', required: true, secret: false },
    { name: 'port', label: 'Port', type: 'number', placeholder: '5432', required: true, secret: false },
    { name: 'database', label: 'Database', type: 'text', placeholder: 'vectors', required: true, secret: false },
    { name: 'user', label: 'User', type: 'text', placeholder: 'postgres', required: false, secret: false },
    { name: 'password', label: 'Password', type: 'password', placeholder: '', required: false, secret: true },
    { name: 'schema', label: 'Schema', type: 'text', placeholder: 'public', required: false, secret: false },
  ],
  pinecone: [
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: '', required: true, secret: true },
    { name: 'index_name', label: 'Index Name (optional filter)', type: 'text', placeholder: 'my-index', required: false, secret: false },
  ],
  opensearch: [
    { name: 'host', label: 'Endpoint URL', type: 'text', placeholder: 'https://...', required: true, secret: false },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: '', required: true, secret: true },
    { name: 'index_name', label: 'Index Name', type: 'text', placeholder: 'my-index', required: false, secret: false },
  ],
  supabase: [
    { name: 'host', label: 'Database Host', type: 'text', placeholder: 'db.abc123.supabase.co', required: true, secret: false },
    { name: 'port', label: 'Port', type: 'number', placeholder: '5432', required: false, secret: false },
    { name: 'database', label: 'Database', type: 'text', placeholder: 'postgres', required: false, secret: false },
    { name: 'user', label: 'User', type: 'text', placeholder: 'postgres', required: false, secret: false },
    { name: 'password', label: 'Password', type: 'password', placeholder: '', required: true, secret: true },
    { name: 'schema', label: 'Schema', type: 'text', placeholder: 'public', required: false, secret: false },
  ],
  neon: [
    { name: 'connection_string', label: 'Connection String', type: 'password', placeholder: 'postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/dbname?sslmode=require', required: true, secret: true },
    { name: 'schema', label: 'Schema', type: 'text', placeholder: 'public', required: false, secret: false },
  ],
  weaviate: [
    { name: 'host', label: 'Cluster URL', type: 'text', placeholder: 'https://my-cluster.weaviate.network', required: true, secret: false },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: '', required: true, secret: true },
    { name: 'class_name', label: 'Class Name (optional filter)', type: 'text', placeholder: 'Document', required: false, secret: false },
  ],
  qdrant: [
    { name: 'host', label: 'Host URL', type: 'text', placeholder: 'https://xyz.cloud.qdrant.io:6333', required: true, secret: false },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: '', required: false, secret: true },
    { name: 'collection_name', label: 'Collection (optional filter)', type: 'text', placeholder: 'my-collection', required: false, secret: false },
  ],
  milvus: [
    { name: 'host', label: 'Host', type: 'text', placeholder: 'https://in01-xyz.aws.vectordb.zillizcloud.com', required: true, secret: false },
    { name: 'port', label: 'Port', type: 'number', placeholder: '19530', required: false, secret: false },
    { name: 'token', label: 'Token', type: 'password', placeholder: 'user:password or API token', required: false, secret: true },
    { name: 'collection_name', label: 'Collection (optional filter)', type: 'text', placeholder: 'my-collection', required: false, secret: false },
  ],
  chroma: [
    { name: 'host', label: 'Host URL', type: 'text', placeholder: 'http://localhost:8000', required: true, secret: false },
    { name: 'api_key', label: 'API Key', type: 'password', placeholder: '', required: false, secret: true },
    { name: 'tenant', label: 'Tenant', type: 'text', placeholder: 'default_tenant', required: false, secret: false },
    { name: 'database', label: 'Database', type: 'text', placeholder: 'default_database', required: false, secret: false },
  ],
};
