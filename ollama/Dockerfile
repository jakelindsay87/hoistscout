FROM ollama/ollama:0.1.40

# The base image's entrypoint handles model pulling via OLLAMA_MODELS env var
# and defaults to 'ollama serve'.
# It also includes curl, so no need to install it separately.

EXPOSE 11434

# Health check to ensure Ollama API is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:11434/api/tags || exit 1

# CMD is inherited from the base image (which is 'ollama serve') 