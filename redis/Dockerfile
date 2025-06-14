FROM redis:7-alpine

# Create redis user and directories
RUN mkdir -p /data && \
    chmod 770 /data

# Use default Redis configuration
EXPOSE 6379

# Run Redis server
CMD ["redis-server"]