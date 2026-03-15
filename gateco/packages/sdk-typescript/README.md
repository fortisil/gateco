# @gateco/sdk

TypeScript SDK for the Gateco API. Zero runtime dependencies -- uses native `fetch`.

## Installation

```bash
npm install @gateco/sdk
```

Requires Node.js >= 18.0.0.

## Quick Start

```typescript
import { GatecoClient } from "@gateco/sdk";

const client = new GatecoClient({
  baseUrl: "https://api.gateco.dev",
});

// Authenticate
await client.login("user@example.com", "password");

// List connectors
const page = await client.connectors.list();
console.log(page.items);

// Execute a permission-gated retrieval
const retrieval = await client.retrievals.execute({
  principalId: "user-123",
  connectorId: "conn-456",
  query: "quarterly revenue",
  topK: 10,
});
console.log(retrieval.outcomes);

// Clean up
client.close();
```

## API Key Authentication

```typescript
const client = new GatecoClient({
  baseUrl: "https://api.gateco.dev",
  apiKey: "your-api-key",
});

// No login needed -- API key is sent with every request
const connectors = await client.connectors.list();
```

## Pagination

```typescript
// Single page
const page = await client.connectors.list(1, 20);
console.log(page.items, page.total, page.totalPages);

// Iterate all pages
for await (const connector of client.connectors.listAll()) {
  console.log(connector.name);
}
```

## Error Handling

```typescript
import { GatecoClient, NotFoundError, RateLimitError } from "@gateco/sdk";

try {
  await client.connectors.get("nonexistent-id");
} catch (err) {
  if (err instanceof NotFoundError) {
    console.log("Connector not found");
  } else if (err instanceof RateLimitError) {
    console.log(`Rate limited, retry after ${err.retryAfter}s`);
  }
}
```

## Resource Namespaces

| Namespace | Description |
|-----------|-------------|
| `client.auth` | Login, signup, refresh, logout |
| `client.connectors` | Connector CRUD, test, bind, config, coverage |
| `client.ingest` | Single document and batch ingestion |
| `client.retrievals` | Execute, list, get secured retrievals |
| `client.policies` | Policy CRUD, activate, archive |

## Development

```bash
npm install
npm run build       # Compile TypeScript
npm test            # Run tests
npm run typecheck   # Type check without emit
```
