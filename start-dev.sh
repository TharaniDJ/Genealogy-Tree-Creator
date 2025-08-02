#!/bin/bash
echo "Starting Genealogy Tree Creator in Development Mode..."
echo "This will enable hot reload and mount source code volumes"
echo ""
docker-compose -f docker-compose.dev.yml up --build
