# Language Tree Service

A FastAPI backend service for exploring language family relationships and linguistic trees. This service provides APIs to retrieve language families, language relationships, and detailed information about languages using Wikidata and Wikipedia.

## Features

- **Language Relationships**: Get parent-child relationships between languages
- **Language Details**: Retrieve detailed information about languages including family, speakers, writing systems
- **Real-time Updates**: WebSocket support for real-time language tree exploration
- **Depth Control**: Configurable depth for exploring language family trees

## API Endpoints

### REST Endpoints

- `GET /relationships/{language_name}/{depth}` - Get language relationships for a given language and depth
- `GET /info/{language_name}` - Get detailed information about a specific language
- `GET /` - Health check endpoint

### WebSocket Endpoints

- `WS /ws/relationships` - Real-time language relationship exploration

## Usage

### Getting Language Relationships

```bash
curl "http://localhost:8001/relationships/English/2"
```

### Getting Language Information

```bash
curl "http://localhost:8001/info/English"
```

## Running the Service

```bash
# Install dependencies
uv install

# Run the development server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Data Sources

This service uses:
- **Wikidata**: For structured language family data
- **Wikipedia**: For language information and validation
