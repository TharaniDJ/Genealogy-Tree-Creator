PM2 run instructions (development)

This repo includes `ecosystem.config.js` to run all backend FastAPI services with PM2.

PowerShell (Windows) - run from repository root:

# Install pm2 globally with Node.js installed
npm i -g pm2

# From project root
# If you use a Python virtualenv, activate it first: `& .\\venv\\Scripts\\Activate.ps1`
# Then start all services with PM2
pm2 start ecosystem.config.js

# Useful pm2 commands
pm2 ls
pm2 logs
pm2 stop ecosystem.config.js
pm2 restart ecosystem.config.js

Notes:
- The ecosystem file assumes `uv` (uv) is available for services that use it. If you don't have `uv` installed, install it into the virtualenv with `pip install uv` or change the `script` to `python -m uvicorn`.
- For `user-service` the config uses `python -m uvicorn` to match the Dockerfile which runs `uvicorn` directly.
- To run with a specific Python interpreter, change `script` for Python processes to the full path of the python executable (e.g. `C:\\path\\to\\venv\\Scripts\\python.exe`).

API gateway and frontend
- The PM2 ecosystem now includes `api-gateway` (port 8080) and `frontend` (Next.js dev server on port 3000).
- Ports follow `docker-compose.yml` mapping: family=8000, language=8001, species=8002, user=8003, gateway=8080, frontend=3000.

Authentication / JWT notes
- The API Gateway validates JWTs issued by the `user-service`. To ensure the gateway can verify tokens, make sure the `SECRET_KEY` and `ALGORITHM` match between the services.
- I added `backend/api-gateway/.env` with the same `SECRET_KEY` used by `user-service` in this repo for development. In production, use a secure, shared secret stored in a proper secret manager.

Frontend notes:
- Development: PM2 runs `pnpm dev` for the frontend. Make sure `pnpm` is installed globally or available in your PATH. Alternatively use `npm run dev` if you prefer.
- Production: Build and run the production server with:
  1) `pnpm build`
  2) `pnpm start` (PM2 can run `pnpm start` instead of `pnpm dev`)

Example PowerShell commands (repo root):

```powershell
# Start everything (backend + gateway + frontend dev)
pm2 start ecosystem.config.js

# If you only want the backend and gateway (no frontend dev server):
pm2 start ecosystem.config.js --only "family-tree-service,language-tree-service,species-tree-service,user-service,api-gateway"
```

Port collisions:
- I aligned the PM2 ports with `docker-compose.yml`. Some Dockerfiles used 8003 for species; docker-compose maps species to 8002 and user to 8003. The PM2 file follows docker-compose to match the API gateway and frontend expectations. If you want to instead follow Dockerfile ports, tell me and I will change them.
