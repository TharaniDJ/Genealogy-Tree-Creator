# Genealogy FastAPI Backend

This project is a FastAPI application that gathers genealogical relationship data from Wikipedia APIs based on user input and specified depth. The application communicates with the frontend using WebSockets for real-time updates.

## Project Structure

```
genealogy-fastapi-backend
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── websocket.py
│   │   └── routes.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── websocket_manager.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── wikipedia_service.py
│   │   └── genealogy_service.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── genealogy.py
│   │   └── websocket_models.py
│   └── utils
│       ├── __init__.py
│       └── helpers.py
├── tests
│   ├── __init__.py
│   ├── test_genealogy_service.py
│   └── test_websocket.py
├── pyproject.toml
├── uv.lock
├── .env
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd genealogy-fastapi-backend
   ```

2. Install dependencies using uv:
   ```
   uv sync
   ```

   This will automatically create a virtual environment and install all dependencies defined in `pyproject.toml`.

## Usage

1. Set up your environment variables in the `.env` file. You may need to include API keys and other configuration settings.

2. Run the FastAPI application:
   ```
   uv run uvicorn app.main:app --reload
   ```

   Or activate the virtual environment and run directly:
   ```
   uv run fastapi dev app/main.py
   ```

3. Access the API documentation at `http://127.0.0.1:8000/docs`.

## WebSocket Communication

The application supports real-time communication with the frontend through WebSockets. The WebSocket implementation is located in `app/api/websocket.py`.

## Testing

To run the tests, use:
```
uv run pytest
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.