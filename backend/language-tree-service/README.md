# Language Tree Service

A FastAPI backend service for exploring language family relationships and linguistic trees. The service now relies on Wikipedia infobox parsing combined with an LLM-powered normalisation step to infer parent/child relationships between languages.

## Features

- **Language Relationships**: Extract parent-child relationships directly from Wikipedia infobox data.
- **LLM Normalisation**: Gemini turns mixed infobox/text signals into a clean hierarchy of `Child of` edges.
- **Real-time Updates**: WebSocket support streams incremental relationships to the client.
- **Depth Input (placeholder)**: The API accepts a depth parameter for future expansion, but the current pipeline operates on a single page.

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

## Configuration

Set an API key for Google Generative AI before starting the service:

```
set GOOGLE_GENAI_API_KEY=your_api_key_here
```

On PowerShell:

```
$env:GOOGLE_GENAI_API_KEY="your_api_key_here"
```

If the key is not provided the service will fall back to heuristic infobox parsing, but relationship quality may be limited.

## Data Sources

This service now uses:
- **Wikipedia**: Pulls infoboxes and relevant article sections via the MediaWiki API.
- **Google Gemini**: Optional LLM step to merge and normalise the extracted relationships.

> **Note:** Former Wikidata-powered endpoints such as distribution maps and detailed language info are currently placeholders while the new pipeline is being integrated.
