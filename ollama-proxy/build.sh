#!/bin/bash

# Build script for ollama-proxy
# This script handles the correct build context for the Dockerfile

echo "Building ollama-proxy Docker image..."

# Change to the ollama-proxy directory to use it as build context
cd "$(dirname "$0")"

# Build the Docker image
docker build -t hoistscout-ollama-proxy:latest .

echo "Build completed. Image tagged as hoistscout-ollama-proxy:latest"