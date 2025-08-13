# CMBCluster API Client

This package provides a strictly-typed TypeScript client for the CMBCluster API. It is generated from the OpenAPI schema and uses `openapi-fetch` for making HTTP requests.

## Installation

This is a private package intended for use within the monorepo. Ensure dependencies are installed at the root of the project.

## Usage

The primary export is `createApiClient`, a factory function that returns a configured `openapi-fetch` client.

### Initialization

Initialize the client with the base URL of the API and the user's authentication token.

```typescript
import createApiClient from './api';

const apiClient = createApiClient({
  baseUrl: 'http://localhost:8000', // Or your production API URL
  token: 'your-auth-token',
});
```

### Making API Calls

You can use the client to make type-safe requests to the API endpoints. The types for paths, parameters, and responses are all generated from the OpenAPI schema.

#### Example: Fetching User Information

```typescript
async function fetchUserInfo() {
  const { data, error } = await apiClient.GET('/users/me');

  if (error) {
    console.error('Error fetching user:', error);
    // Handle the error appropriately
    return;
  }

  // `data` is fully typed according to the OpenAPI schema
  console.log('User Info:', data);
}
```


### Error Handling

The client returns an `error` object if the request fails (e.g., network error, non-2xx response). The `error` object contains details about the failure. You should always check for the presence of the `error` object before using the `data`.

```typescript
async function getEnvironments() {
  const { data, error } = await apiClient.GET('/environments');

  if (error) {
    // Log the error for debugging
    console.error('API Error:', error);

    // Show a user-friendly message
    alert(`Failed to fetch environments: ${error.message}`);
    return;
  }

  // Process the data
  console.log(data);
}
```

### Using a Wrapper

To make the client more robust and easier to use, you can create a wrapper that handles token management and base URL configuration automatically.

Create a file, for example `apps/web/lib/api-client.ts`:

```typescript
import createApiClient, { ApiClient } from '@cmb/sdk';
import { getAuthToken } from './auth'; // Your function to get the auth token

let client: ApiClient | null = null;

export function getApiClient(): ApiClient {
  if (client) {
    return client;
  }

  const token = getAuthToken();
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  client = createApiClient({ baseUrl, token });
  return client;
}
```

Now, in your components, you can simply import and use `getApiClient()`:

```typescript
import { getApiClient } from '@/lib/api-client';

async function fetchMyData() {
  const api = getApiClient();
  const { data, error } = await api.GET('/some/data');
  // ...
}
```
