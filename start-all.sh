#!/bin/bash

echo "==============================================="
echo "   Genealogy Tree Creator - Full Stack Startup"
echo "==============================================="
echo

echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker and make sure it's running."
    exit 1
fi

echo "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose."
    exit 1
fi

echo
echo "Building and starting all services..."
echo "This may take a few minutes on first run..."
echo

# Build and start all services
docker-compose up --build

echo
echo "==============================================="
echo "Services should now be running on:"
echo "==============================================="
echo "Frontend:           http://localhost:3000"
echo "Family Tree API:     http://localhost:8000"
echo "Language Tree API:   http://localhost:8001"
echo "Species Tree API:    http://localhost:8002"
echo "==============================================="
