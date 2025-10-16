/**
 * PM2 ecosystem file to run all backend FastAPI services from the repository root.
 * Each app uses either `uv` (uv) shim or directly `uvicorn` as used in the Dockerfiles.
 * Adjust `interpreter` to a specific python path if you want to use a virtualenv.
 */
module.exports = {
  apps: [
    {
      name: 'family-tree-service',
      cwd: './backend/family-tree-service',
      script: 'uv',
      args: 'run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload',
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        ENV: 'development'
      }
    },
    {
      name: 'language-tree-service',
      cwd: './backend/language-tree-service',
      script: 'uv',
      args: 'run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload',
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        ENV: 'development'
      }
    },
    {
      name: 'species-tree-service',
      cwd: './backend/species-tree-service',
      script: 'uv',
      // docker-compose maps species service to port 8002; align with that
      args: 'run uvicorn app.main:app --host 0.0.0.0 --port 8002',
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        ENV: 'development'
      }
    },
    {
      name: 'user-service',
      cwd: './backend/user-service',
      // user-service Dockerfile runs `uvicorn` directly; we call python -m uvicorn to be safe
      script: 'python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8003',
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1',
        ENV: 'development'
      }
    },
    {
      name: 'api-gateway',
      cwd: './backend/api-gateway',
      script: 'python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8080',
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1',
        ENV: 'development'
      }
    },
    {
      name: 'frontend',
      cwd: './frontend',
      // Use pnpm dev for development; for production run `pnpm build` then `pnpm start` (next start)
      script: 'pnpm',
      args: 'dev',
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'development'
      }
    }
  ]
};
