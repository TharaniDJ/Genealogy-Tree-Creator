# Species Tree Service

A FastAPI backend service for exploring biological taxonomy and evolutionary relationships between species, including animals, plants, fungi, and other organisms. This service provides APIs to retrieve taxonomic hierarchies, evolutionary relationships, and detailed information about species using Wikidata and Wikipedia.

## Features

- **Taxonomic Relationships**: Get parent-child relationships in biological taxonomy
- **Species Details**: Retrieve detailed information about species including classification, habitat, conservation status
- **Evolutionary Trees**: Explore phylogenetic relationships and common ancestors
- **Real-time Updates**: WebSocket support for real-time species tree exploration
- **Depth Control**: Configurable depth for exploring taxonomic hierarchies

## API Endpoints

### REST Endpoints

- `GET /relationships/{species_name}/{depth}` - Get taxonomic relationships for a given species and depth
- `GET /info/{species_name}` - Get detailed information about a specific species
- `GET /taxonomy/{species_name}` - Get complete taxonomic classification
- `GET /` - Health check endpoint

### WebSocket Endpoints

- `WS /ws/relationships` - Real-time species relationship exploration
- `WS /ws/taxonomy` - Real-time taxonomic tree exploration

## Usage

### Getting Species Relationships

```bash
curl "http://localhost:8002/relationships/Panthera%20leo/2"
```

### Getting Species Information

```bash
curl "http://localhost:8002/info/Panthera%20leo"
```

### Getting Taxonomic Classification

```bash
curl "http://localhost:8002/taxonomy/Panthera%20leo"
```

## Running the Service

```bash
# Install dependencies
uv install

# Run the development server
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Data Sources

This service uses:
- **Wikidata**: For structured taxonomic and biological data
- **Wikipedia**: For species information and validation
- **Tree of Life Web Project**: For phylogenetic relationships

## Supported Taxa

- Animals (Kingdom Animalia)
- Plants (Kingdom Plantae)
- Fungi (Kingdom Fungi)
- Bacteria (Kingdom Bacteria)
- Archaea (Kingdom Archaea)
- Protists (various kingdoms)
