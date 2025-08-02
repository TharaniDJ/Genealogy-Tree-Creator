# Genealogy Tree Creator

A comprehensive tree visualization platform that explores relationships across different domains: **family genealogy**, **language families**, and **biological taxonomy**. This platform provides interactive tree visualizations and real-time data exploration through modern web technologies.

## 🌟 Features

### Three Tree Services
1. **Family Tree Service** (Port 8000) - Explore genealogical relationships and family histories
2. **Language Tree Service** (Port 8001) - Discover language families and linguistic relationships  
3. **Species Tree Service** (Port 8002) - Navigate biological taxonomy and evolutionary relationships

### Core Capabilities
- **Interactive Tree Visualization** - Dynamic, zoomable tree representations
- **Real-time Data Fetching** - Live updates via WebSocket connections
- **Multi-depth Exploration** - Configurable depth for relationship discovery
- **Rich Metadata** - Detailed information about each entity (people, languages, species)
- **Cross-platform** - Web-based interface accessible on any device

## 🏗️ Architecture

```
┌─────────────────┐
│    Frontend     │ ← Next.js + React + TypeScript
│   (Port 3000)   │
└─────────────────┘
         │
    ┌────┴────┐
    │ API     │
    │ Gateway │
    └────┬────┘
         │
    ┌────┴──────────────────────────┐
    │                               │
┌───▼────┐  ┌──────────┐  ┌────────▼──┐
│Family  │  │Language  │  │Species    │
│Tree    │  │Tree      │  │Tree       │
│(8000)  │  │(8001)    │  │(8002)     │
└────────┘  └──────────┘  └───────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with `pnpm`
- **Docker & Docker Compose** (optional)

### Option 1: Docker Compose (Recommended)

#### Development Mode (Hot Reload)
```bash
# Clone the repository
git clone https://github.com/TharaniDJ/Genealogy-Tree-Creator.git
cd Genealogy-Tree-Creator

# Start in development mode with hot reload
docker-compose -f docker-compose.dev.yml up --build
# OR use the convenience script:
# Windows: start-dev.bat
# Linux/Mac: ./start-dev.sh

# Access the application
# Frontend: http://localhost:3000 (with hot reload)
# Family API: http://localhost:8000 (with auto-reload)
# Language API: http://localhost:8001 (with auto-reload)
# Species API: http://localhost:8002 (with auto-reload)
```

#### Production Mode (Optimized Build)
```bash
# Start in production mode
docker-compose -f docker-compose.prod.yml up --build
# OR use the default compose file:
docker-compose up --build
# OR use the convenience script:
# Windows: start-prod.bat
# Linux/Mac: ./start-prod.sh

# Access the application
# Frontend: http://localhost:3000 (optimized build)
# Family API: http://localhost:8000
# Language API: http://localhost:8001
# Species API: http://localhost:8002
```

### Docker Modes Comparison

| Feature | Development Mode | Production Mode |
|---------|------------------|-----------------|
| **Hot Reload** | ✅ Enabled | ❌ Disabled |
| **Code Changes** | 🔄 Live updates | 🔄 Requires rebuild |
| **Volume Mounts** | ✅ Source code mounted | ❌ Code copied to image |
| **Build Time** | ⚡ Faster (dev dependencies) | 🐌 Slower (optimized build) |
| **Image Size** | 📦 Larger (includes dev tools) | 📦 Smaller (production only) |
| **Performance** | 🐌 Good (debug mode) | ⚡ Optimized |
| **Debugging** | 🔍 Full debug capabilities | 🔍 Limited debugging |

### Option 2: Manual Setup

#### Backend Services

```bash
# Family Tree Service
cd backend/family-tree-service
uv sync
uv run python run.py  # Runs on port 8000

# Language Tree Service  
cd ../language-tree-service
uv sync
uv run python run.py  # Runs on port 8001

# Species Tree Service
cd ../species-tree-service  
uv sync
uv run python run.py  # Runs on port 8002
```

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev  # Runs on port 3000
```

## 📋 API Documentation

### Family Tree Service (Port 8000)
- `GET /relationships/{person_name}/{depth}` - Get family relationships
- `GET /info/{person_name}` - Get person details  
- `WS /ws/relationships` - Real-time family tree exploration

### Language Tree Service (Port 8001)
- `GET /relationships/{language_name}/{depth}` - Get language family relationships
- `GET /info/{language_name}` - Get language details
- `WS /ws/relationships` - Real-time language tree exploration

### Species Tree Service (Port 8002)
- `GET /relationships/{species_name}/{depth}` - Get taxonomic relationships
- `GET /info/{species_name}` - Get species details
- `GET /taxonomy/{species_name}` - Get complete taxonomic classification
- `WS /ws/relationships` - Real-time species tree exploration
- `WS /ws/taxonomy` - Real-time taxonomic classification

## 🔧 Usage Examples

### Family Tree
```bash
# Get family relationships for a person
curl "http://localhost:8000/relationships/Albert%20Einstein/2"

# Get personal details
curl "http://localhost:8000/info/Albert%20Einstein"
```

### Language Tree
```bash
# Get language family relationships
curl "http://localhost:8001/relationships/English/2"

# Get language information
curl "http://localhost:8001/info/Spanish"
```

### Species Tree
```bash
# Get taxonomic relationships
curl "http://localhost:8002/relationships/Panthera%20leo/2"

# Get species information
curl "http://localhost:8002/info/Panthera%20leo"

# Get taxonomic classification
curl "http://localhost:8002/taxonomy/Panthera%20leo"
```

## 🌐 Data Sources

- **Wikidata** - Structured data for all three domains
- **Wikipedia** - Supplementary information and validation
- **SPARQL Queries** - Advanced relationship discovery

## 🛠️ Development

### Project Structure
```
Genealogy-Tree-Creator/
├── backend/
│   ├── family-tree-service/     # FastAPI service for genealogy
│   ├── language-tree-service/   # FastAPI service for languages  
│   └── species-tree-service/    # FastAPI service for biology
├── frontend/                    # Next.js React application
├── docker-compose.yml          # Multi-service orchestration
└── README.md
```

### Adding New Features
1. **Backend**: Add endpoints to the appropriate service
2. **Frontend**: Update components and API calls
3. **WebSocket**: Implement real-time features for live updates

### Testing
```bash
# Test individual services
cd backend/family-tree-service && python test_service.py
cd backend/language-tree-service && python test_service.py  
cd backend/species-tree-service && python test_service.py
```

## 🔮 Future Enhancements

- **Graph Database Integration** - Neo4j for complex relationship queries
- **Caching Layer** - Redis for improved performance
- **Authentication** - User accounts and saved trees
- **Export Features** - PDF, SVG, and other format exports
- **Mobile App** - React Native companion app
- **AI Integration** - Smart relationship discovery and suggestions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for exploring the interconnected nature of our world through family, language, and species relationships.**
