# Upstash Redis Setup for HoistScout

This directory contains scripts to set up and manage Upstash Redis for HoistScout production deployment.

## Why Upstash?

Upstash is a serverless Redis service that offers:
- **Generous free tier**: 10,000 commands/day, 256MB storage
- **Global edge caching**: Low latency worldwide
- **Serverless pricing**: Pay only for what you use
- **Built-in SSL/TLS**: Secure by default
- **REST API**: HTTP-based access for serverless environments

## Prerequisites

1. Create an Upstash account at https://console.upstash.com
2. Get your API credentials from https://console.upstash.com/account/api
3. Set environment variables:
   ```bash
   export UPSTASH_EMAIL='your-email@example.com'
   export UPSTASH_API_KEY='your-api-key'
   ```

## Scripts

### 1. setup_upstash_redis.py

Creates a new Upstash Redis database for HoistScout production.

```bash
# Basic usage - creates database and shows credentials
python scripts/setup_upstash_redis.py

# Output as environment variables (for .env file)
python scripts/setup_upstash_redis.py --output-env > redis.env

# Output as JSON
python scripts/setup_upstash_redis.py --json

# Skip connection testing
python scripts/setup_upstash_redis.py --skip-test
```

**Features:**
- Automatically creates a database named 'hoistscout-prod'
- Uses US East region for optimal global latency
- Tests both Redis protocol and REST API connections
- Handles existing databases gracefully
- Provides clear error messages and troubleshooting tips

### 2. example_redis_usage.py

Demonstrates how to use Redis with HoistScout patterns.

```bash
# Using the Redis URL from setup script
python scripts/example_redis_usage.py 'rediss://default:password@endpoint:port'

# Or with environment variable
export REDIS_URL='rediss://default:password@endpoint:port'
python scripts/example_redis_usage.py
```

**Demonstrates:**
- Job queue patterns for scraping tasks
- Caching strategies for website data
- Rate limiting for API protection
- Session storage for user management
- Pub/Sub for real-time updates
- Celery configuration examples

## Render Deployment

After setting up Upstash Redis:

1. **Copy the Redis URL** from the setup script output
2. **Add to Render Environment Variables**:
   - Go to your Render service settings
   - Add `REDIS_URL` with the Upstash Redis URL
   - The URL format: `rediss://default:password@endpoint:port`

3. **Update your application** to use the Redis URL:
   ```python
   # In config.py or settings
   REDIS_URL = os.environ.get('REDIS_URL')
   
   # For Celery
   CELERY_BROKER_URL = REDIS_URL
   CELERY_RESULT_BACKEND = REDIS_URL
   ```

## Free Tier Limits

Upstash free tier includes:
- **10,000 commands/day**: Sufficient for small to medium applications
- **256MB storage**: Good for caching and session data
- **1000 concurrent connections**: Handles multiple workers
- **Global replication**: Available in all regions

## Monitoring Usage

Monitor your Redis usage in the Upstash console:
- https://console.upstash.com
- View daily command count
- Check memory usage
- Monitor performance metrics

## Troubleshooting

### Connection Issues
- Ensure your API credentials are correct
- Check if database is active in Upstash console
- Verify no IP restrictions are set
- Try using REST API if Redis protocol fails

### Quota Exceeded
- Free tier allows 1 database per account
- Delete unused databases in console
- Consider upgrading for more resources

### Performance Tips
- Use connection pooling in production
- Implement proper key expiration
- Monitor command patterns
- Use pipelining for bulk operations

## Support

- Upstash Documentation: https://docs.upstash.com/redis
- Upstash Console: https://console.upstash.com
- HoistScout Issues: Create an issue in the repository