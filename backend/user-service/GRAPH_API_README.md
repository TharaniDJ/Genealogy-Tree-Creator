# Graph Saving API Documentation

## Overview

The Graph Saving API allows users to save, retrieve, update, and delete their genealogy tree graphs (family trees, language trees, and species/taxonomy trees). Each graph is associated with a specific user and can include depth information and metadata.

## Features

- ✅ **Create** new graphs with validation
- ✅ **List** all graphs with filtering and pagination
- ✅ **Retrieve** specific graphs by ID
- ✅ **Update** existing graphs
- ✅ **Delete** graphs
- ✅ **Statistics** - Get counts by graph type
- ✅ **User Authentication** - All endpoints require JWT authentication
- ✅ **Unique Names** - Graph names must be unique per user per graph type
- ✅ **Flexible Structure** - Supports different data formats for each graph type

## Graph Types

### 1. Language Tree
Stores language relationships with detailed metadata:
```json
{
  "language1": "English",
  "relationship": "Child of",
  "language2": "Proto-Germanic",
  "language1_qid": "Q1860",
  "language2_qid": "Q21125",
  "language1_category": "language",
  "language2_category": "proto_language"
}
```

### 2. Species/Taxonomy Tree
Stores taxonomic relationships:
```json
{
  "parent_taxon": {
    "rank": "Family",
    "name": "Hominidae"
  },
  "has_child": true,
  "child_taxon": {
    "rank": "Genus",
    "name": "Homo"
  }
}
```

### 3. Family Tree
Stores family relationships with personal details:
```json
{
  "entity1": "Albert Einstein",
  "relationship": "child of",
  "entity2": "Hermann Einstein",
  "classification": "parent-child"
}
```

## API Endpoints

### Base URL
```
http://localhost:8003/api/users
```

### Authentication
All endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. Create Graph
**POST** `/graphs`

Create a new graph for the authenticated user.

#### Request Body
```json
{
  "graph_name": "Indo-European Language Family",
  "graph_type": "language",
  "depth_usage": true,
  "depth": 3,
  "graph_data": [
    {
      "language1": "English",
      "relationship": "Child of",
      "language2": "Proto-Germanic",
      "language1_qid": "Q1860",
      "language2_qid": "Q21125",
      "language1_category": "language",
      "language2_category": "proto_language"
    }
  ],
  "description": "A comprehensive tree of Indo-European languages"
}
```

#### Field Descriptions
- `graph_name` (required): Unique name for the graph within its type
- `graph_type` (required): One of `"species"`, `"language"`, or `"family"`
- `depth_usage` (required): Boolean indicating if depth was used
- `depth` (optional): Integer (1-10), required if `depth_usage` is `true`
- `graph_data` (required): Array of relationship objects (structure varies by type)
- `description` (optional): Text description of the graph (max 1000 chars)

#### Response
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f191e810c19729de860ea",
  "graph_name": "Indo-European Language Family",
  "graph_type": "language",
  "depth_usage": true,
  "depth": 3,
  "graph_data": [...],
  "description": "A comprehensive tree of Indo-European languages",
  "created_at": "2025-10-17T10:30:00Z",
  "updated_at": "2025-10-17T10:30:00Z"
}
```

#### Status Codes
- `201 Created` - Graph created successfully
- `400 Bad Request` - Validation error or duplicate name
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

---

### 2. List Graphs
**GET** `/graphs`

Get all graphs for the authenticated user with optional filtering.

#### Query Parameters
- `graph_type` (optional): Filter by type (`species`, `language`, `family`)
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 500)

#### Example Request
```
GET /graphs?graph_type=language&skip=0&limit=10
```

#### Response
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "graph_name": "Indo-European Language Family",
    "graph_type": "language",
    "depth_usage": true,
    "depth": 3,
    "description": "A comprehensive tree of Indo-European languages",
    "created_at": "2025-10-17T10:30:00Z",
    "updated_at": "2025-10-17T10:30:00Z",
    "nodes_count": 45
  }
]
```

#### Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid graph_type
- `401 Unauthorized` - Missing or invalid token

---

### 3. Get Graph by ID
**GET** `/graphs/{graph_id}`

Retrieve a specific graph by its ID.

#### Path Parameters
- `graph_id` (required): MongoDB ObjectId of the graph

#### Example Request
```
GET /graphs/507f1f77bcf86cd799439011
```

#### Response
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f191e810c19729de860ea",
  "graph_name": "Indo-European Language Family",
  "graph_type": "language",
  "depth_usage": true,
  "depth": 3,
  "graph_data": [...],
  "description": "A comprehensive tree of Indo-European languages",
  "created_at": "2025-10-17T10:30:00Z",
  "updated_at": "2025-10-17T10:30:00Z"
}
```

#### Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid graph_id format
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Graph not found or doesn't belong to user

---

### 4. Update Graph
**PUT** `/graphs/{graph_id}`

Update an existing graph. Only provided fields will be updated.

#### Path Parameters
- `graph_id` (required): MongoDB ObjectId of the graph

#### Request Body (all fields optional)
```json
{
  "graph_name": "Updated Graph Name",
  "depth_usage": false,
  "depth": null,
  "graph_data": [...],
  "description": "Updated description"
}
```

#### Response
Same as Get Graph response with updated values.

#### Status Codes
- `200 OK` - Successfully updated
- `400 Bad Request` - Validation error or duplicate name
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Graph not found

---

### 5. Delete Graph
**DELETE** `/graphs/{graph_id}`

Delete a graph permanently.

#### Path Parameters
- `graph_id` (required): MongoDB ObjectId of the graph

#### Example Request
```
DELETE /graphs/507f1f77bcf86cd799439011
```

#### Response
No content (empty response body)

#### Status Codes
- `204 No Content` - Successfully deleted
- `400 Bad Request` - Invalid graph_id format
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Graph not found

---

### 6. Get Graph Statistics
**GET** `/graphs/stats/count`

Get statistics about user's graphs.

#### Query Parameters
- `graph_type` (optional): Filter by type

#### Example Requests
```
GET /graphs/stats/count
GET /graphs/stats/count?graph_type=language
```

#### Response (without filter)
```json
{
  "total": 42,
  "by_type": {
    "species": 15,
    "language": 20,
    "family": 7
  }
}
```

#### Response (with filter)
```json
{
  "total": 20,
  "graph_type": "language"
}
```

#### Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid graph_type
- `401 Unauthorized` - Missing or invalid token

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message"
}
```

### Common Errors

#### Duplicate Graph Name
```json
{
  "detail": "A language graph named 'Indo-European Language Family' already exists. Please use a different name."
}
```

#### Invalid Graph Type
```json
{
  "detail": "graph_type must be one of: species, language, family"
}
```

#### Validation Error
```json
{
  "detail": "Validation error",
  "errors": [
    "graph_data: field required",
    "graph_name: ensure this value has at least 1 characters"
  ]
}
```

---

## Data Validation Rules

### Graph Name
- ✅ Required
- ✅ Minimum length: 1 character
- ✅ Maximum length: 200 characters
- ✅ Must be unique per user per graph type

### Graph Type
- ✅ Required
- ✅ Must be one of: `species`, `language`, `family`

### Depth
- ✅ Optional (required if `depth_usage` is `true`)
- ✅ Must be between 1 and 10

### Graph Data
- ✅ Required
- ✅ Must be a non-empty array
- ✅ Each item is a JSON object (structure varies by graph type)

### Description
- ✅ Optional
- ✅ Maximum length: 1000 characters

---

## Example Usage with curl

### 1. Register/Login to get token
```bash
# Register
curl -X POST http://localhost:8003/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8003/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

Save the `access_token` from the response.

### 2. Create a Language Graph
```bash
curl -X POST http://localhost:8003/api/users/graphs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "graph_name": "Germanic Languages",
    "graph_type": "language",
    "depth_usage": true,
    "depth": 2,
    "graph_data": [
      {
        "language1": "English",
        "relationship": "Child of",
        "language2": "Proto-Germanic",
        "language1_qid": "Q1860",
        "language2_qid": "Q21125"
      }
    ],
    "description": "Germanic language family tree"
  }'
```

### 3. List All Graphs
```bash
curl -X GET "http://localhost:8003/api/users/graphs" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Get Specific Graph
```bash
curl -X GET "http://localhost:8003/api/users/graphs/507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 5. Update Graph
```bash
curl -X PUT http://localhost:8003/api/users/graphs/507f1f77bcf86cd799439011 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "graph_name": "Updated Germanic Languages",
    "description": "Updated description"
  }'
```

### 6. Delete Graph
```bash
curl -X DELETE "http://localhost:8003/api/users/graphs/507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 7. Get Statistics
```bash
curl -X GET "http://localhost:8003/api/users/graphs/stats/count" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Frontend Integration Example

### JavaScript/TypeScript

```typescript
// Get auth token from localStorage
const token = localStorage.getItem('token');

// Create a graph
async function saveGraph(graphData: any) {
  const response = await fetch('http://localhost:8003/api/users/graphs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      graph_name: 'My Language Tree',
      graph_type: 'language',
      depth_usage: true,
      depth: 3,
      graph_data: graphData, // Your relationships array
      description: 'Optional description'
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// List user's graphs
async function loadGraphs(graphType?: string) {
  const url = new URL('http://localhost:8003/api/users/graphs');
  if (graphType) {
    url.searchParams.append('graph_type', graphType);
  }
  
  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// Load a specific graph
async function loadGraph(graphId: string) {
  const response = await fetch(
    `http://localhost:8003/api/users/graphs/${graphId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Graph not found');
  }
  
  return await response.json();
}

// Delete a graph
async function deleteGraph(graphId: string) {
  const response = await fetch(
    `http://localhost:8003/api/users/graphs/${graphId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to delete graph');
  }
}
```

---

## MongoDB Collections

### Collection: `graphs`

```javascript
{
  _id: ObjectId("507f1f77bcf86cd799439011"),
  user_id: "507f191e810c19729de860ea",
  graph_name: "Indo-European Language Family",
  graph_type: "language",
  depth_usage: true,
  depth: 3,
  graph_data: [
    {
      language1: "English",
      relationship: "Child of",
      language2: "Proto-Germanic",
      language1_qid: "Q1860",
      language2_qid: "Q21125",
      language1_category: "language",
      language2_category: "proto_language"
    }
  ],
  description: "A comprehensive tree of Indo-European languages",
  created_at: ISODate("2025-10-17T10:30:00Z"),
  updated_at: ISODate("2025-10-17T10:30:00Z")
}
```

### Indexes
For optimal performance, create these indexes:

```javascript
// Unique index on user_id + graph_name + graph_type
db.graphs.createIndex(
  { user_id: 1, graph_name: 1, graph_type: 1 },
  { unique: true }
)

// Index for listing user's graphs sorted by updated_at
db.graphs.createIndex(
  { user_id: 1, updated_at: -1 }
)

// Index for filtering by graph type
db.graphs.createIndex(
  { user_id: 1, graph_type: 1, updated_at: -1 }
)
```

---

## Testing

### Run the service
```bash
cd backend/user-service
uv run uvicorn app.main:app --port 8003 --reload
```

### Access API Documentation
Open your browser:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

### Test with the interactive UI
The FastAPI automatic documentation provides an interactive interface to test all endpoints.

---

## Dependencies

All required dependencies are already in `pyproject.toml`:

```toml
dependencies = [
    "fastapi>=0.95.0",
    "uvicorn[standard]>=0.20.0",
    "pydantic[email]>=1.10.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib>=1.7.4",
    "bcrypt>=4.0.0",
    "motor>=3.1.1",      # Provides async MongoDB support and bson
    "pymongo>=4.3.0",    # MongoDB driver
]
```

No additional dependencies needed! ✅

---

## Security Considerations

1. **Authentication Required**: All endpoints require valid JWT token
2. **User Isolation**: Users can only access their own graphs
3. **Input Validation**: All inputs are validated using Pydantic models
4. **Unique Constraints**: Prevents duplicate graph names per user per type
5. **Error Handling**: Detailed error messages without exposing sensitive data

---

## Troubleshooting

### Import errors for `bson`
This is just a linting issue. The `bson` module is provided by `pymongo` and `motor`. Your code will run fine.

### Graph name already exists
Each user can only have one graph with a specific name per graph type. Use different names or update the existing graph.

### Token expired
JWT tokens expire after a certain time. Login again to get a new token.

### MongoDB connection issues
Check your MongoDB connection string in the environment configuration.

---

## Future Enhancements

Potential features for future versions:
- [ ] Graph sharing between users
- [ ] Graph templates/presets
- [ ] Graph versioning/history
- [ ] Export graphs in various formats (JSON, CSV, GraphML)
- [ ] Graph search and filtering by content
- [ ] Graph merging capabilities
- [ ] Collaborative editing
- [ ] Graph analytics (statistics, insights)

---

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review this README
3. Check server logs for detailed error messages
4. Ensure MongoDB is running and accessible

---

## License

Part of the Genealogy Tree Creator project.
