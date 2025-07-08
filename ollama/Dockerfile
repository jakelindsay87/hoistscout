# Dockerfile for Ollama on Render
FROM ollama/ollama:latest

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create startup script
RUN echo '#!/bin/bash\n\
ollama serve &\n\
SERVER_PID=$!\n\
echo "Waiting for Ollama to start..."\n\
sleep 10\n\
echo "Pulling llama3.1 model..."\n\
ollama pull llama3.1 || echo "Model pull failed, continuing anyway"\n\
echo "Ollama ready!"\n\
wait $SERVER_PID' > /start.sh && chmod +x /start.sh

# Expose port
EXPOSE 11434

# Use the startup script
CMD ["/start.sh"]