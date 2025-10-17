# Quick Start Guide - Graph Saving API

## 🚀 What Was Added

A complete graph saving system for storing and managing:
- 🌳 **Family Trees** - Family relationships and genealogy data
- 🗣️ **Language Trees** - Language relationships and linguistic data
- 🦎 **Species Trees** - Taxonomic/species classification data

## 📁 New Files Created

```
backend/user-service/
├── app/
│   ├── models/
│   │   └── graph.py              # Pydantic models for graph data
│   ├── api/
│   │   ├── graph_crud.py         # Database operations
│   │   └── graph_routes.py       # API endpoints
│   └── main.py                   # Updated to include graph routes
├── GRAPH_API_README.md          # Complete API documentation
├── DEPENDENCIES.md              # Dependency information
└── QUICKSTART.md                # This file
```

## ⚡ Start Using in 3 Steps

### Step 1: Restart User Service

```bash
# Stop the current user-service task if running
# Then restart it:

cd backend/user-service
uv run uvicorn app.main:app --port 8003 --reload
```

### Step 2: Test with Swagger UI

Open in browser: http://localhost:8003/docs

You'll see new endpoints under the "graphs" tag:
- `POST /api/users/graphs`
- `GET /api/users/graphs`
- `GET /api/users/graphs/{graph_id}`
- `PUT /api/users/graphs/{graph_id}`
- `DELETE /api/users/graphs/{graph_id}`
- `GET /api/users/graphs/stats/count`

### Step 3: Try It Out!

1. **Login** to get your JWT token (use existing `/api/users/login`)
2. **Click "Authorize"** button in Swagger UI
3. **Paste your token** (the value from `access_token`)
4. **Try creating a graph** using the POST endpoint

## 📝 Example: Save a Language Tree

### Frontend Code (TypeScript/React)

```typescript
// After user creates/explores a language tree in your frontend:

const saveLanguageTree = async () => {
  // Get the relationships from your language tree state
  const relationships = buildRelationshipsPayload(); // Your existing function
  
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('http://localhost:8003/api/users/graphs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        graph_name: 'Indo-European Languages',
        graph_type: 'language',
        depth_usage: true,
        depth: 3,
        graph_data: relationships, // Your array of language relationships
        description: 'My custom language tree'
      })
    });
    
    if (response.ok) {
      const savedGraph = await response.json();
      alert(`Graph saved! ID: ${savedGraph.id}`);
    } else {
      const error = await response.json();
      alert(`Error: ${error.detail}`);
    }
  } catch (error) {
    console.error('Failed to save graph:', error);
  }
};
```

### Load Saved Graphs

```typescript
const loadSavedGraphs = async (graphType: string) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(
    `http://localhost:8003/api/users/graphs?graph_type=${graphType}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  const graphs = await response.json();
  console.log('Saved graphs:', graphs);
  
  // Display in a dropdown or list for user to select
  return graphs;
};

const loadSpecificGraph = async (graphId: string) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(
    `http://localhost:8003/api/users/graphs/${graphId}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  const graph = await response.json();
  
  // Use graph.graph_data to rebuild your tree visualization
  return graph;
};
```

## 🔧 Integration Points

### Language Tree (`language_tree/page.tsx`)

Add a save button in your UI:

```typescript
const handleSaveGraph = async () => {
  const graphName = prompt('Enter a name for this language tree:');
  if (!graphName) return;
  
  const relationships = buildRelationshipsPayload(); // Your existing function
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8003/api/users/graphs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      graph_name: graphName,
      graph_type: 'language',
      depth_usage: depth > 0,
      depth: depth,
      graph_data: relationships,
      description: `Language tree for ${language}`
    })
  });
  
  if (response.ok) {
    alert('Graph saved successfully!');
  }
};
```

### Taxonomy/Species Tree (`taxonomy_tree/page.tsx`)

```typescript
const handleSaveGraph = async () => {
  const graphName = prompt('Enter a name for this taxonomy tree:');
  if (!graphName) return;
  
  // Extract tuples from your current graph state
  const tuples = extractTuplesFromGraph(nodes, edges);
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8003/api/users/graphs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      graph_name: graphName,
      graph_type: 'species',
      depth_usage: false,
      graph_data: tuples,
      description: `Taxonomy tree for ${scientificName}`
    })
  });
  
  if (response.ok) {
    alert('Graph saved successfully!');
  }
};

// Helper function to extract tuples
const extractTuplesFromGraph = (nodes, edges) => {
  return edges.map(edge => {
    const parentNode = nodes.find(n => n.id === edge.source);
    const childNode = nodes.find(n => n.id === edge.target);
    
    return {
      parent_taxon: {
        rank: parentNode?.data.rank || '',
        name: parentNode?.data.label || ''
      },
      has_child: true,
      child_taxon: {
        rank: childNode?.data.rank || '',
        name: childNode?.data.label || ''
      }
    };
  });
};
```

### Family Tree (`family_tree/page.tsx`)

```typescript
const handleSaveGraph = async () => {
  const graphName = prompt('Enter a name for this family tree:');
  if (!graphName) return;
  
  // Extract relationships from websocket data
  const familyRelationships = websocketData
    .filter(msg => msg.type === 'relationship')
    .map(msg => msg.data);
  
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8003/api/users/graphs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      graph_name: graphName,
      graph_type: 'family',
      depth_usage: true,
      depth: searchDepth,
      graph_data: familyRelationships,
      description: `Family tree for ${searchQuery}`
    })
  });
  
  if (response.ok) {
    alert('Graph saved successfully!');
  }
};
```

## 🎯 Next Steps

### 1. Add UI Components

Add save/load buttons to each tree page:

```tsx
// Add to your toolbar/control panel
<button
  onClick={handleSaveGraph}
  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
>
  💾 Save Graph
</button>

<button
  onClick={handleLoadGraph}
  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
>
  📂 Load Graph
</button>
```

### 2. Create a "My Graphs" Page

Create a new page to list all saved graphs:

```typescript
// app/my-graphs/page.tsx
const MyGraphsPage = () => {
  const [graphs, setGraphs] = useState([]);
  
  useEffect(() => {
    loadGraphs();
  }, []);
  
  const loadGraphs = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('http://localhost:8003/api/users/graphs', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setGraphs(data);
  };
  
  return (
    <div>
      <h1>My Saved Graphs</h1>
      {graphs.map(graph => (
        <div key={graph.id}>
          <h3>{graph.graph_name}</h3>
          <p>Type: {graph.graph_type}</p>
          <p>Nodes: {graph.nodes_count}</p>
          <p>Updated: {new Date(graph.updated_at).toLocaleDateString()}</p>
          <button onClick={() => loadGraph(graph.id)}>Load</button>
          <button onClick={() => deleteGraph(graph.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
};
```

### 3. Add MongoDB Indexes (Optional but Recommended)

For better performance, run these commands in MongoDB:

```javascript
// Connect to MongoDB
mongo

// Use your database
use genealogy_db  // or whatever your DB name is

// Create indexes
db.graphs.createIndex(
  { user_id: 1, graph_name: 1, graph_type: 1 },
  { unique: true }
)

db.graphs.createIndex(
  { user_id: 1, updated_at: -1 }
)
```

## 📚 Documentation

- **Complete API docs**: See `GRAPH_API_README.md`
- **Dependencies info**: See `DEPENDENCIES.md`
- **Interactive docs**: http://localhost:8003/docs (when service is running)

## ✅ Checklist

- [ ] User service restarted with new endpoints
- [ ] Tested creating a graph via Swagger UI
- [ ] Tested listing graphs
- [ ] Added save button to language tree frontend
- [ ] Added save button to taxonomy tree frontend
- [ ] Added save button to family tree frontend
- [ ] Created "My Graphs" page (optional)
- [ ] Added MongoDB indexes (optional)

## 🐛 Troubleshooting

**Q: I see "Import bson could not be resolved" in my editor**  
A: This is just a linting warning. The code works fine! `bson` is provided by `motor` and `pymongo`.

**Q: Getting 401 Unauthorized**  
A: Make sure you're logged in and passing the JWT token in the Authorization header.

**Q: Graph name already exists error**  
A: Each user can only have one graph with a specific name per type. Use a different name or update the existing graph.

**Q: Can't see the new endpoints**  
A: Make sure you restarted the user service after adding the new files.

## 🎉 You're Done!

Your graph saving API is now ready to use. Start integrating it into your frontend pages to allow users to save and load their trees!
