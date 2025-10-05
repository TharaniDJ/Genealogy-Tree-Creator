# Species Tree Service

A FastAPI service for exploring taxonomic relationships and species hierarchies.

## Features

- Extract taxonomic information from Wikipedia
- Expand taxonomic trees using Wikidata SPARQL queries
- Get taxonomic relationships in tuple format (parent_taxon, has_child, child_taxon)

## Endpoints

- `GET /taxonomy/{scientific_name}` - Get complete taxonomic hierarchy for a species
- `GET /expand/{taxon_name}/{rank}` - Expand taxonomic tree from a given taxon and rank

## Running the Service

```bash
# Install dependencies
uv sync

# Run the service
uv run uvicorn app.main:app --reload --port 8003
```

## Docker

```bash
# Build
docker build -t species-tree-service .

# Run
docker run -p 8003:8003 species-tree-service
```