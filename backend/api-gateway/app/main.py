from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from websockets.client import connect as ws_connect
from websockets.exceptions import WebSocketException, ConnectionClosed
import asyncio
from app.core.config import settings
from jose import jwt, JWTError

app = FastAPI(title='API Gateway')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000','https://genealogy-tree-creator.vercel.app','https://genealogy-tree-creator-git-main-dasun-pramodyas-projects.vercel.app','https://genealogy-tree-creator-74k14uffn-dasun-pramodyas-projects.vercel.app'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use localhost for local devel opment (not Docker service names)
BACKEND_MAP = {
    "family": "http://localhost:8000/api/family",
    "language": "http://localhost:8001/api/language",
    "species": "http://localhost:8002/api/species",
    "users": "http://localhost:8003/api/users",
}


def verify_token(auth_header: str | None):
    if not auth_header:
        return None
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


@app.api_route('/api/{service}/{path:path}', methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(service: str, path: str, request: Request):
    target = BACKEND_MAP.get(service)
    if not target:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{target}/{path}"
    headers = dict(request.headers)
    print(service, path)
    # Validate token for protected routes (simple rule: all except public auth endpoints)
    is_public_endpoint = (
        service == 'users' and (path.startswith('login') or path.startswith('register') or path.startswith('auth'))
    )
    
    if not is_public_endpoint:
        print("Validating token...")
        user = verify_token(headers.get('authorization'))
        if user is None:
            raise HTTPException(status_code=401, detail='Unauthorized')

    body = await request.body()
    print(f"[PROXY] Service: {service}, Path: {path}")
    print(f"[PROXY] Method: {request.method}")
    print(f"[PROXY] Forwarding to: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.request(
                request.method, 
                url, 
                content=body, 
                headers=headers, 
                params=request.query_params
            )
        
        # Try to return JSON if possible, otherwise return plain text
        try:
            content = resp.json()
        except Exception:
            content = resp.text
            
        return JSONResponse(status_code=resp.status_code, content=content)
        
    except httpx.ConnectError as e:
        print(f"[PROXY ERROR] Cannot connect to service '{service}' at {target}")
        print(f"[PROXY ERROR] Details: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service '{service}' is unavailable. Make sure it's running on {target}"
        )
    except httpx.ReadTimeout:
        print(f"[PROXY ERROR] Service '{service}' timed out after 30 seconds")
        raise HTTPException(
            status_code=504, 
            detail=f"Service '{service}' took too long to respond"
        )
    except Exception as e:
        print(f"[PROXY ERROR] Unexpected error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error communicating with service '{service}': {str(e)}"
        )


@app.get('/')
async def root():
    return {"message": "API Gateway running"}


# WebSocket proxy endpoint without additional path
@app.websocket('/api/{service}/ws')
async def websocket_proxy_simple(service: str, websocket: WebSocket):
    """
    Proxy WebSocket connections to backend services (with authentication)
    For endpoints like /api/family/ws
    """
    # Accept the connection first to be able to send close messages
    await websocket.accept()
    
    # Verify authentication token from query parameters
    token = websocket.query_params.get('token')
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required: No token provided")
        return
    
    # Verify the token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token: No user ID")
            return
        print(f"WebSocket authenticated for user: {user_id}")
    except JWTError as e:
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return
    except Exception as e:
        await websocket.close(code=1008, reason=f"Authentication error: {str(e)}")
        return
    
    # Map service to WebSocket URL
    ws_map = {
        "language": "ws://localhost:8001/ws",
        "family": "ws://localhost:8000/ws",
        "species": "ws://localhost:8002/ws",
    }
    
    backend_ws_base = ws_map.get(service)
    if not backend_ws_base:
        await websocket.close(code=1008, reason=f"Service '{service}' not found")
        return
    
    backend_ws_url = backend_ws_base
    
    backend_ws = None
    try:
        # Connect to the backend WebSocket
        backend_ws = await ws_connect(backend_ws_url)
        
        # Create tasks to forward messages in both directions
        async def forward_to_backend():
            try:
                while True:
                    # Receive from frontend
                    data = await websocket.receive_text()
                    # Send to backend
                    await backend_ws.send(data)
            except WebSocketDisconnect:
                print(f"Frontend WebSocket disconnected for {service}")
            except Exception as e:
                print(f"Error forwarding to backend: {e}")
        
        async def forward_to_frontend():
            try:
                while True:
                    # Receive from backend
                    data = await backend_ws.recv()
                    # Send to frontend (handle both text and binary data)
                    if isinstance(data, bytes):
                        await websocket.send_bytes(data)
                    else:
                        await websocket.send_text(str(data))
            except ConnectionClosed:
                print(f"Backend WebSocket closed for {service}")
            except Exception as e:
                print(f"Error forwarding to frontend: {e}")
        
        # Run both forwarding tasks concurrently
        await asyncio.gather(
            forward_to_backend(),
            forward_to_frontend(),
            return_exceptions=True
        )
        
    except WebSocketException as e:
        print(f"WebSocket error connecting to backend {backend_ws_url}: {e}")
        await websocket.close(code=1011, reason=f"Backend service error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in WebSocket proxy: {e}")
        await websocket.close(code=1011, reason=f"Internal error: {str(e)}")
    finally:
        if backend_ws:
            await backend_ws.close()


# WebSocket proxy endpoints with additional path
@app.websocket('/api/{service}/ws/{path:path}')
async def websocket_proxy(service: str, path: str, websocket: WebSocket):
    """
    Proxy WebSocket connections to backend services (with authentication)
    """
    # Accept the connection first to be able to send close messages
    await websocket.accept()
    
    # Verify authentication token from query parameters
    # WebSocket connections can't send custom headers easily, so we use query params
    token = websocket.query_params.get('token')
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required: No token provided")
        return
    
    # Verify the token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token: No user ID")
            return
        print(f"WebSocket authenticated for user: {user_id}")
    except JWTError as e:
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return
    except Exception as e:
        await websocket.close(code=1008, reason=f"Authentication error: {str(e)}")
        return
    
    # Map service to WebSocket URL
    ws_map = {
        "language": "ws://localhost:8001/ws",
        "family": "ws://localhost:8000/ws",
        "species": "ws://localhost:8002/ws",
    }
    
    backend_ws_base = ws_map.get(service)
    if not backend_ws_base:
        await websocket.close(code=1008, reason=f"Service '{service}' not found")
        return
    
    backend_ws_url = f"{backend_ws_base}/{path}"
    
    backend_ws = None
    try:
        # Connect to the backend WebSocket
        backend_ws = await ws_connect(backend_ws_url)
        
        # Create tasks to forward messages in both directions
        async def forward_to_backend():
            try:
                while True:
                    # Receive from frontend
                    data = await websocket.receive_text()
                    # Send to backend
                    await backend_ws.send(data)
            except WebSocketDisconnect:
                print(f"Frontend WebSocket disconnected for {service}/{path}")
            except Exception as e:
                print(f"Error forwarding to backend: {e}")
        
        async def forward_to_frontend():
            try:
                while True:
                    # Receive from backend
                    data = await backend_ws.recv()
                    # Send to frontend (handle both text and binary data)
                    if isinstance(data, bytes):
                        await websocket.send_bytes(data)
                    else:
                        await websocket.send_text(str(data))
            except ConnectionClosed:
                print(f"Backend WebSocket closed for {service}/{path}")
            except Exception as e:
                print(f"Error forwarding to frontend: {e}")
        
        # Run both forwarding tasks concurrently
        await asyncio.gather(
            forward_to_backend(),
            forward_to_frontend(),
            return_exceptions=True
        )
        
    except WebSocketException as e:
        print(f"WebSocket error connecting to backend {backend_ws_url}: {e}")
        await websocket.close(code=1011, reason=f"Backend service error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in WebSocket proxy: {e}")
        await websocket.close(code=1011, reason=f"Internal error: {str(e)}")
    finally:
        if backend_ws:
            await backend_ws.close()
