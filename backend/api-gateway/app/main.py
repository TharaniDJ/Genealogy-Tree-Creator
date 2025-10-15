from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from app.core.config import settings
from jose import jwt, JWTError

app = FastAPI(title='API Gateway')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_MAP = {
    "family": "http://family-tree-service:8000",
    "language": "http://language-tree-service:8001",
    "species": "http://species-tree-service:8002",
    "users": "http://user-service:8003",
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

    # Validate token for protected routes (simple rule: all except public auth endpoints)
    if not path.startswith('auth') and service != 'users':
        user = verify_token(headers.get('authorization'))
        if user is None:
            raise HTTPException(status_code=401, detail='Unauthorized')

    async with httpx.AsyncClient() as client:
        body = await request.body()
        resp = await client.request(request.method, url, content=body, headers=headers, params=request.query_params)
    # Try to return JSON if possible, otherwise return plain text
    try:
        content = resp.json()
    except Exception:
        content = resp.text
    return JSONResponse(status_code=resp.status_code, content=content)


@app.get('/')
async def root():
    return {"message": "API Gateway running"}
