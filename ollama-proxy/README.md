# Ollama Proxy

A lightweight proxy service for Ollama LLM integration.

## Build Instructions

### Using Docker Compose (Recommended)
From the repository root:
```bash
docker-compose build ollama-proxy
```

### Manual Docker Build
From the repository root, use the root-context Dockerfile:
```bash
docker build -f ollama-proxy/Dockerfile.root-context -t hoistscout-ollama-proxy .
```

Or use the build script from within the ollama-proxy directory:
```bash
cd ollama-proxy
./build.sh
```

### Build Context Notes
- The default `Dockerfile` expects the build context to be the `ollama-proxy` directory
- The `Dockerfile.root-context` expects the build context to be the repository root
- The docker-compose.yml is configured to use the correct context automatically

## Environment Variables
- `PORT`: Port to run the service on (default: 8080)
- `MOCK_MODE`: Enable mock mode for testing (default: true)
- `EXTERNAL_OLLAMA_URL`: URL of the Ollama instance to proxy to
- `OLLAMA_PROXY_API_KEY`: API key for authentication (optional)