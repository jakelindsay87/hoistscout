FROM ollama/ollama:0.1.40

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create startup script
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Start Ollama in the background\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to start..."\n\
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do\n\
  sleep 1\n\
done\n\
\n\
# Pull the model if not already present\n\
echo "Checking for mistral model..."\n\
if ! ollama list | grep -q "mistral:7b-q4_K_M"; then\n\
  echo "Pulling mistral:7b-q4_K_M model..."\n\
  ollama pull mistral:7b-q4_K_M\n\
fi\n\
\n\
# Keep the service running\n\
wait $OLLAMA_PID' > /start.sh && chmod +x /start.sh

EXPOSE 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:11434/api/tags || exit 1

# Run the startup script
CMD ["/start.sh"] 