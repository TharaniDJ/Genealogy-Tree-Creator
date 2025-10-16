# API Gateway Integration for Graph Saving

## Overview
The frontend now routes **all API requests through the API Gateway** (port 8080) instead of directly calling individual backend services. This provides centralized authentication, logging, and service routing.

## Changes Made

### 1. Language Tree Service (`frontend/app/language_tree/page.tsx`)

Updated all graph-related API calls to use the API Gateway:

**Before:**
```typescript
const apiBase = process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8003';
```

**After:**
```typescript
const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
```

### 2. API Gateway (`backend/api-gateway/app/main.py`)

Fixed authentication logic to properly validate tokens for user service endpoints:

**Before:**
```python
if not path.startswith('auth') and (service != 'users'):
    # Token validation skipped for user service
```

**After:**
```python
if not path.startswith('auth'):
    # Token validation applied to all services except auth endpoints
```

## API Routing

All frontend requests now follow this pattern:

```
Frontend → API Gateway (8080) → Backend Service (8000/8001/8002/8003)
```

### Graph API Endpoints (via Gateway)

| Endpoint | Method | Routes To | Purpose |
|----------|--------|-----------|---------|
| `http://localhost:8080/api/users/graphs` | POST | user-service:8003 | Save new graph |
| `http://localhost:8080/api/users/graphs?graph_type=language` | GET | user-service:8003 | List saved graphs |
| `http://localhost:8080/api/users/graphs/{id}` | GET | user-service:8003 | Load specific graph |
| `http://localhost:8080/api/users/graphs/{id}` | PUT | user-service:8003 | Update graph |
| `http://localhost:8080/api/users/graphs/{id}` | DELETE | user-service:8003 | Delete graph |

## Authentication Flow

1. **Frontend** sends request with `Authorization: Bearer <token>` header
2. **API Gateway** validates JWT token using shared SECRET_KEY
3. If valid, **Gateway** forwards request to appropriate backend service
4. **Backend service** validates token again (defense in depth)
5. Response flows back through gateway to frontend

## Environment Variables

### Recommended Setup

Create a `.env.local` file in the `frontend/` directory:

```env
# API Gateway URL (default: http://localhost:8080)
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8080

# Optional: Override for production
# NEXT_PUBLIC_API_GATEWAY_URL=https://your-domain.com/api
```

### Fallback Behavior

If environment variable is not set, the code falls back to:
- `http://localhost:8080` (API Gateway)

## Testing the Integration

### 1. Start All Services

```bash
# Terminal 1: API Gateway
cd backend/api-gateway
uv run uvicorn app.main:app --port 8080 --reload

# Terminal 2: User Service
cd backend/user-service
uv run uvicorn app.main:app --port 8003 --reload

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 2. Test Graph Saving

1. Login to the application
2. Navigate to Language Tree page
3. Create a language tree
4. Click "Save Graph" button
5. Enter a graph name
6. Check API Gateway terminal for logs:
   ```
   [PROXY] Service: users, Path: graphs
   [PROXY] Method: POST
   [PROXY] Forwarding to: http://localhost:8003/api/users/graphs
   ```

### 3. Test Graph Loading

1. Click "Load Graph" button
2. Verify list appears
3. Check gateway logs for:
   ```
   [PROXY] Service: users, Path: graphs
   [PROXY] Method: GET
   [PROXY] Forwarding to: http://localhost:8003/api/users/graphs?graph_type=language
   ```

## Benefits of API Gateway

✅ **Centralized Authentication** - Single point for token validation
✅ **Service Abstraction** - Frontend doesn't need to know backend URLs
✅ **Monitoring & Logging** - All requests logged in one place
✅ **Rate Limiting** - Can be added at gateway level
✅ **CORS Management** - Single CORS configuration
✅ **Microservices Ready** - Easy to add/change backend services

## Future Improvements

1. **Add request logging middleware** for detailed analytics
2. **Implement rate limiting** per user/endpoint
3. **Add response caching** for frequently accessed data
4. **WebSocket support** for real-time updates (already implemented!)
5. **Service health checks** at gateway level
6. **Request/response transformation** if needed

## Troubleshooting

### Error: "Service 'users' is unavailable"

**Cause:** User service is not running
**Solution:** 
```bash
cd backend/user-service
uv run uvicorn app.main:app --port 8003 --reload
```

### Error: "401 Unauthorized"

**Cause:** Token validation failing
**Solution:**
1. Check you're logged in
2. Verify SECRET_KEY matches in gateway and user-service
3. Check token hasn't expired (default: 30 minutes)

### Error: "Connection refused to localhost:8080"

**Cause:** API Gateway is not running
**Solution:**
```bash
cd backend/api-gateway
uv run uvicorn app.main:app --port 8080 --reload
```

## Code Changes Summary

### Files Modified

1. ✅ `frontend/app/language_tree/page.tsx`
   - Changed 4 API calls to use gateway URL
   - Updated `handleSaveGraph()`
   - Updated `loadSavedGraphs()`
   - Updated `handleLoadGraph()`
   - Updated `handleDeleteGraph()`

2. ✅ `backend/api-gateway/app/main.py`
   - Fixed authentication logic
   - Now validates tokens for user service endpoints
   - Removed exception for 'users' service

### No Changes Required

- ❌ Backend services (no changes needed)
- ❌ Database models (no changes needed)
- ❌ Authentication logic (no changes needed)

## Next Steps

Apply the same pattern to:
1. **Taxonomy Tree** (species graphs)
2. **Family Tree** (family graphs)

Both should use:
```typescript
const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
```

---

**Last Updated:** October 17, 2025
**Author:** GitHub Copilot
**Status:** ✅ Complete and Tested
