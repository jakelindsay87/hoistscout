#!/bin/bash
# Setup script for running HoistScout with Ollama locally

echo "=== HoistScout with Ollama Setup ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "1. Pulling Ollama image..."
docker pull ollama/ollama:latest

echo ""
echo "2. Starting Ollama service..."
docker run -d --name hoistscout-ollama \
    -p 11434:11434 \
    -v ollama_data:/root/.ollama \
    --restart unless-stopped \
    ollama/ollama:latest

# Wait for Ollama to start
echo ""
echo "3. Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running!"
else
    echo "⚠️  Ollama may still be starting up..."
fi

echo ""
echo "4. Pulling llama3.1 model (this may take a few minutes)..."
docker exec hoistscout-ollama ollama pull llama3.1

echo ""
echo "5. Testing Ollama..."
curl -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.1",
        "prompt": "Extract tender title from: Government seeks IT services for cloud migration project. Budget $500k",
        "stream": false
    }' | jq -r '.response' 2>/dev/null || echo "Test completed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Ollama is running at: http://localhost:11434"
echo ""
echo "To use with HoistScout, set these environment variables:"
echo "  export OLLAMA_BASE_URL=http://localhost:11434"
echo "  export OLLAMA_MODEL=llama3.1"
echo ""
echo "Or add to your .env file:"
echo "  OLLAMA_BASE_URL=http://localhost:11434"
echo "  OLLAMA_MODEL=llama3.1"
echo ""
echo "To stop Ollama:"
echo "  docker stop hoistscout-ollama"
echo ""
echo "To remove Ollama:"
echo "  docker rm -f hoistscout-ollama"