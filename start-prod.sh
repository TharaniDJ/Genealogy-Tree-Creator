#!/bin/bash
echo "Starting Genealogy Tree Creator in Production Mode..."
echo "This will build optimized containers without hot reload"
echo ""
docker-compose -f docker-compose.prod.yml up --build
