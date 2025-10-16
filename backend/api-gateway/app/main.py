from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from app.core.config import settings
from jose import jwt, JWTError

app = FastAPI(title='API Gateway')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use localhost for local development (not Docker service names)
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
    if not path.startswith('auth') and (service != 'users'):
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
