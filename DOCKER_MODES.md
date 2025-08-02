# Docker Deployment Modes

This project supports two distinct Docker deployment modes to accommodate different development and production needs.

## 🔧 Development Mode

### Features
- **Hot Reload**: Automatic application restart when code changes
- **Volume Mounting**: Source code is mounted into containers for live editing
- **Debug Logging**: Enhanced logging for development debugging
- **Development Dependencies**: Includes development tools and packages
- **Faster Startup**: No optimization build process

### How to Use

#### Windows
```cmd
start-dev.bat
```

#### Linux/Mac
```bash
./start-dev.sh
```

#### Manual Command
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### What Happens
1. **Backend Services**: FastAPI runs with `--reload` flag for auto-restart
2. **Frontend**: Next.js runs in development mode with hot module replacement
3. **Volume Mounts**: Your local code changes are immediately reflected in containers
4. **Debug Environment**: All services run with debug-level logging

## 🚀 Production Mode

### Features
- **Optimized Build**: Minified and optimized application bundles
- **Health Checks**: Container health monitoring
- **Production Dependencies**: Only essential runtime dependencies
- **Security**: Non-root user execution where applicable
- **Performance**: Optimized for runtime performance

### How to Use

#### Windows
```cmd
start-prod.bat
```

#### Linux/Mac
```bash
./start-prod.sh
```

#### Manual Commands
```bash
# Using production-specific compose file
docker-compose -f docker-compose.prod.yml up --build

# Using default compose file (defaults to production)
docker-compose up --build
```

### What Happens
1. **Backend Services**: FastAPI runs in production mode without reload
2. **Frontend**: Next.js builds optimized static assets and runs in production mode
3. **No Volume Mounts**: Code is copied into images during build time
4. **Health Checks**: All services include health check endpoints

## 📊 Mode Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **Startup Time** | Fast | Slower (build process) |
| **Image Size** | Larger | Smaller |
| **Code Changes** | Live reload | Requires rebuild |
| **Performance** | Good | Optimized |
| **Debugging** | Full access | Limited |
| **Dependencies** | All (dev + prod) | Production only |
| **Security** | Development-focused | Production-hardened |

## 🔄 Switching Between Modes

### From Development to Production
1. Stop development containers: `docker-compose -f docker-compose.dev.yml down`
2. Start production containers: `docker-compose -f docker-compose.prod.yml up --build`

### From Production to Development
1. Stop production containers: `docker-compose -f docker-compose.prod.yml down`
2. Start development containers: `docker-compose -f docker-compose.dev.yml up --build`

## 🐛 Troubleshooting

### Development Mode Issues
- **Port conflicts**: Ensure ports 3000, 8000-8002 are available
- **Volume mounting**: On Windows, ensure Docker Desktop has access to your drive
- **Hot reload not working**: Check that volume mounts are configured correctly

### Production Mode Issues
- **Build failures**: Check that all dependencies are properly specified
- **Health check failures**: Ensure applications start correctly and expose health endpoints
- **Performance issues**: Monitor container resource usage

## 📝 File Structure

```
├── docker-compose.yml          # Default (production mode)
├── docker-compose.dev.yml      # Development mode
├── docker-compose.prod.yml     # Production mode (explicit)
├── start-dev.bat/.sh          # Development mode scripts
├── start-prod.bat/.sh         # Production mode scripts
├── start-all.bat/.sh          # Legacy scripts (production mode)
└── DOCKER_MODES.md            # This documentation
```

## 🎯 Best Practices

### Development
- Use development mode for active coding and testing
- Regularly test your changes in production mode before deployment
- Keep development dependencies separate from production dependencies

### Production
- Always test production builds before deployment
- Use production mode for staging and production environments
- Monitor application performance and resource usage

### General
- Use `.env` files for environment-specific configuration
- Keep Docker images updated with security patches
- Regularly clean up unused Docker images and volumes
