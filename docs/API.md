# API Reference

Complete REST API documentation for CMBCluster.

## Base URL

```
http://localhost:8000          # Development
https://api.your-domain.com    # Production
```

## Authentication

All endpoints except `/health` and `/auth/*` require authentication via JWT token in session cookie.

```bash
# Get token (set in session cookie automatically)
curl -X POST http://localhost:8000/auth/login

# Include cookies in subsequent requests
curl -b cookies.txt http://localhost:8000/environments
```

## Response Format

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Not authenticated |
| 403 | Forbidden - No permission |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Server Error - Internal error |
| 503 | Service Unavailable - Temporarily down |

---

## Endpoints

### Authentication (`/auth`)

#### `POST /auth/login`
Start Google OAuth flow.

**Response:**
```json
{
  "status": "success",
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "message": "Redirect to auth_url to login"
}
```

#### `GET /auth/callback`
OAuth callback endpoint (called by Google, not by client).

**Query Parameters:**
- `code` - Authorization code from Google
- `state` - CSRF protection state

**Response:**
Redirects to dashboard with JWT token in secure cookie.

#### `GET /auth/logout`
Logout and clear session.

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

#### `GET /users/me`
Get current authenticated user info.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "user-123",
    "email": "user@example.com",
    "role": "user",
    "subscription_tier": "free",
    "created_at": "2024-01-01T00:00:00Z",
    "max_uptime_minutes": 60,
    "auto_shutdown_enabled": true
  }
}
```

---

### Environments (`/environments`)

#### `POST /environments`
Create a new user environment pod.

**Body:**
```json
{
  "image": "borisbolliet/cmbagent-ui:latest",
  "application_id": "app-123",
  "config": {
    "name": "My Research Env",
    "description": "Analysis workspace"
  }
}
```

**Response:**
```json
{
  "status": "created",
  "data": {
    "env_id": "env-abc123",
    "pod_name": "user-123-env-abc123",
    "status": "creating",
    "created_at": "2024-01-15T10:30:00Z",
    "url": "http://localhost:8501"
  }
}
```

#### `GET /environments`
Get current user's active environment.

**Response:**
```json
{
  "status": "success",
  "data": {
    "active": true,
    "environment": {
      "env_id": "env-abc123",
      "pod_name": "user-123-env-abc123",
      "status": "running",
      "created_at": "2024-01-15T10:30:00Z",
      "url": "http://localhost:8501"
    }
  }
}
```

#### `GET /environments/list`
List all user's environments (multi-environment support).

**Response:**
```json
{
  "status": "success",
  "data": {
    "environments": [
      {
        "env_id": "env-abc123",
        "pod_name": "user-123-env-abc123",
        "status": "running",
        "created_at": "2024-01-15T10:30:00Z",
        "url": "http://localhost:8501"
      },
      {
        "env_id": "env-def456",
        "pod_name": "user-123-env-def456",
        "status": "stopped",
        "created_at": "2024-01-14T15:20:00Z",
        "url": null
      }
    ]
  }
}
```

#### `GET /environments/{env_id}/info`
Get detailed environment info including uptime.

**Path Parameters:**
- `env_id` - Environment ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "environment": {...},
    "uptime_minutes": 45,
    "max_uptime_minutes": 60,
    "auto_shutdown_enabled": true,
    "time_until_shutdown_minutes": 15,
    "subscription_tier": "free"
  }
}
```

#### `DELETE /environments`
Delete a user's environment.

**Query Parameters:**
- `env_id` (optional) - Specific environment to delete, latest if not provided

**Response:**
```json
{
  "status": "deleted",
  "message": "Environment deleted successfully"
}
```

#### `POST /environments/heartbeat`
Send heartbeat to keep environment alive (optional).

**Response:**
```json
{
  "status": "success",
  "message": "Heartbeat received"
}
```

---

### Environment Variables (`/user-env-vars`)

#### `GET /user-env-vars`
List all environment variables for current user.

**Response:**
```json
{
  "status": "success",
  "data": {
    "env_vars": [
      {
        "key": "API_KEY",
        "value": "***encrypted***",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "key": "DATABASE_URL",
        "value": "***encrypted***",
        "created_at": "2024-01-14T15:20:00Z"
      }
    ]
  }
}
```

#### `POST /user-env-vars`
Add or update an environment variable.

**Body:**
```json
{
  "key": "API_KEY",
  "value": "secret-value-here"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "key": "API_KEY",
    "value": "***encrypted***",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### `DELETE /user-env-vars/{key}`
Delete an environment variable.

**Path Parameters:**
- `key` - Variable name

**Response:**
```json
{
  "status": "success",
  "message": "Environment variable deleted"
}
```

---

### Files (`/user-files`)

#### `POST /user-files/upload`
Upload file to workspace.

**Request:**
```bash
curl -X POST http://localhost:8000/user-files/upload \
  -F "file=@myfile.csv"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "filename": "myfile.csv",
    "size_bytes": 1024,
    "path": "/workspace/myfile.csv",
    "uploaded_at": "2024-01-15T10:30:00Z"
  }
}
```

#### `GET /user-files`
List files in workspace.

**Response:**
```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "filename": "myfile.csv",
        "size_bytes": 1024,
        "path": "/workspace/myfile.csv",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### `GET /user-files/{filename}`
Download file from workspace.

**Path Parameters:**
- `filename` - File to download

**Response:**
File binary content with appropriate media type.

#### `DELETE /user-files/{filename}`
Delete file from workspace.

**Path Parameters:**
- `filename` - File to delete

**Response:**
```json
{
  "status": "success",
  "message": "File deleted successfully"
}
```

---

### Activity (`/activity`)

#### `GET /activity`
Get user activity log.

**Query Parameters:**
- `limit` (optional, default 50) - Number of records to return

**Response:**
```json
{
  "status": "success",
  "data": {
    "activities": [
      {
        "id": "activity-123",
        "user_id": "user-123",
        "action": "environment_created",
        "details": "Created environment env-abc123",
        "timestamp": "2024-01-15T10:30:00Z",
        "status": "success"
      },
      {
        "id": "activity-124",
        "user_id": "user-123",
        "action": "file_uploaded",
        "details": "Uploaded myfile.csv",
        "timestamp": "2024-01-15T10:25:00Z",
        "status": "success"
      }
    ]
  }
}
```

---

### Health & Status (`/health`)

#### `GET /health`
Check API health status (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600.25,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /`
Root endpoint (no authentication required).

**Response:**
```json
{
  "service": "CMBCluster API",
  "version": "1.0.0",
  "status": "healthy",
  "docs": "/docs"
}
```

---

## Admin Endpoints (`/admin`)

*Requires admin role*

#### `GET /admin/users`
List all users in the system.

**Response:**
```json
{
  "status": "success",
  "data": {
    "users": [
      {
        "id": "user-123",
        "email": "user@example.com",
        "role": "user",
        "subscription_tier": "free",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### `GET /admin/environments`
List all environments in the system.

**Response:**
```json
{
  "status": "success",
  "data": {
    "environments": [
      {
        "env_id": "env-abc123",
        "user_id": "user-123",
        "pod_name": "user-123-env-abc123",
        "status": "running",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### `GET /admin/activity`
Get all activity logs.

**Query Parameters:**
- `limit` (optional, default 100)
- `user_id` (optional) - Filter by user

**Response:**
Same as `/activity` but with all users' activities.

---

## Error Examples

### Missing Authentication
```json
{
  "detail": "Not authenticated",
  "error_code": "UNAUTHORIZED"
}
```

### Invalid Request
```json
{
  "detail": "Invalid environment ID format",
  "error_code": "BAD_REQUEST"
}
```

### Resource Not Found
```json
{
  "detail": "Environment not found",
  "error_code": "NOT_FOUND"
}
```

### Rate Limited
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMITED"
}
```

---

## Code Examples

### Python (httpx)
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000", follow_redirects=True)

# Create environment
response = client.post("/environments", json={
    "image": "borisbolliet/cmbagent-ui:latest"
})
print(response.json())

# Get user info
response = client.get("/users/me")
print(response.json())

# Upload file
with open("data.csv", "rb") as f:
    response = client.post("/user-files/upload", files={"file": f})
print(response.json())
```

### JavaScript/TypeScript
```typescript
async function createEnvironment() {
  const response = await fetch('http://localhost:8000/environments', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image: 'borisbolliet/cmbagent-ui:latest'
    })
  });
  return response.json();
}

async function getUserInfo() {
  const response = await fetch('http://localhost:8000/users/me', {
    credentials: 'include'
  });
  return response.json();
}
```

### cURL
```bash
# Create environment
curl -X POST http://localhost:8000/environments \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"image":"borisbolliet/cmbagent-ui:latest"}'

# Get user info
curl -X GET http://localhost:8000/users/me \
  -b cookies.txt

# Upload file
curl -X POST http://localhost:8000/user-files/upload \
  -F "file=@myfile.csv" \
  -b cookies.txt
```

---

## Rate Limiting

Default limits (configurable):
- Authentication: 10 attempts/hour per IP
- API requests: 60 requests/minute per user
- File upload: 100MB per file, 1GB per user

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1705325400
```

When rate limited:
```json
{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "error_code": "RATE_LIMITED"
}
```
