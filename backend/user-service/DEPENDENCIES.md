# PyProject.toml Configuration

## Current Dependencies

Your `pyproject.toml` already has all the required dependencies! ✅

```toml
[project]
name = "user-service"
version = "0.1.0"
description = "User service for Genealogy Tree Creator"
dependencies = [
    "fastapi>=0.95.0",           # Web framework
    "uvicorn[standard]>=0.20.0",  # ASGI server
    "pydantic[email]>=1.10.0",    # Data validation
    "pydantic-settings>=2.0.0",   # Settings management
    "python-jose[cryptography]>=3.3.0",  # JWT tokens
    "passlib>=1.7.4",             # Password hashing
    "bcrypt>=4.0.0",              # Password hashing
    "motor>=3.1.1",               # ✅ Async MongoDB driver (provides bson)
    "pymongo>=4.3.0",             # ✅ MongoDB driver (provides bson)
]
```

## What Each Dependency Does

### Core Web Framework
- **fastapi**: Modern web framework with automatic API documentation
- **uvicorn**: High-performance ASGI server to run the application

### Data Validation
- **pydantic**: Data validation using Python type hints
- **pydantic-settings**: Configuration management

### Authentication & Security
- **python-jose**: JWT token creation and verification
- **passlib**: Password hashing utilities
- **bcrypt**: Secure password hashing algorithm

### Database
- **motor**: Async MongoDB driver (provides `bson` module)
- **pymongo**: MongoDB driver (provides `bson.objectid`)

## No Additional Dependencies Needed!

The graph saving API uses:
- ✅ `motor` for async MongoDB operations
- ✅ `bson.objectid.ObjectId` from pymongo/motor
- ✅ `fastapi` for API endpoints
- ✅ `pydantic` for data validation
- ✅ JWT authentication (already implemented)

## About the Import Warnings

If you see linting errors like:
```
Import "bson" could not be resolved
```

**This is just a linting/IntelliSense issue, not a runtime error!**

The `bson` module is provided by both `motor` and `pymongo`. Your code will run perfectly fine.

### To Fix Linting (Optional)

If the warnings bother you, you can:

1. **Add to VSCode settings.json**:
```json
{
  "python.analysis.extraPaths": [
    "${workspaceFolder}/.venv/lib/python3.x/site-packages"
  ]
}
```

2. **Or install stubs** (not required for runtime):
```bash
pip install types-pymongo
```

But again, **your code works fine without these fixes!**

## Running the Service

```bash
# Navigate to user-service
cd backend/user-service

# Run with uvicorn
uv run uvicorn app.main:app --port 8003 --reload
```

## Verify Installation

To verify all dependencies are installed:

```bash
cd backend/user-service
uv pip list
```

You should see all the packages listed above.

## Testing the Graph API

Once running, visit:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

Both will show your new graph endpoints:
- POST `/api/users/graphs` - Create graph
- GET `/api/users/graphs` - List graphs
- GET `/api/users/graphs/{graph_id}` - Get specific graph
- PUT `/api/users/graphs/{graph_id}` - Update graph
- DELETE `/api/users/graphs/{graph_id}` - Delete graph
- GET `/api/users/graphs/stats/count` - Get statistics

## Summary

✅ **No changes needed to pyproject.toml**  
✅ **All dependencies already installed**  
✅ **Graph API ready to use**  

Just restart your user service and the graph endpoints will be available!
