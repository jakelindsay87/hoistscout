# Redis Provisioning Script

This script automatically provisions free Redis instances from multiple providers with automatic fallback support.

## Features

- **Multiple Provider Support**: Upstash (primary), Railway, Aiven, and local Redis
- **Automatic Fallback**: If one provider fails, automatically tries the next
- **Connection Verification**: Built-in connection testing
- **Multiple Output Formats**: Text, JSON, and .env format
- **Comprehensive Testing**: Includes Redis operation tests
- **SSL/TLS Support**: Secure connections by default
- **Error Handling**: Robust error handling with detailed logging

## Supported Providers

### 1. Upstash (Primary - Recommended)
- **Free Tier**: 10,000 commands/day, 256MB storage
- **Features**: Serverless, global replication, SSL/TLS
- **Setup**: 
  ```bash
  export UPSTASH_API_KEY="your-api-key"
  export UPSTASH_EMAIL="your-email"
  ```
- **Get API Key**: https://console.upstash.com/account/api

### 2. Local Redis
- Automatically detects local Redis instances
- No configuration needed
- Checks common ports: 6379 (localhost, 127.0.0.1, redis)

### 3. Railway
- Cloud platform with limited free tier
- Requires manual setup through dashboard
- **Setup**: `export RAILWAY_API_KEY="your-api-key"`
- **Dashboard**: https://railway.app/new

### 4. Aiven
- 30-day free trial available
- Requires manual setup
- **Setup**: `export AIVEN_API_KEY="your-api-key"`
- **Sign up**: https://aiven.io/signup

## Installation

The script automatically installs required dependencies (redis package) if not present.

## Usage

### Basic Usage
```bash
# Auto-provision from any available provider
python scripts/provision_redis.py

# Use specific provider
python scripts/provision_redis.py --provider upstash

# Provision and verify connection
python scripts/provision_redis.py --verify

# Provision, verify, and run tests
python scripts/provision_redis.py --verify --test
```

### Output Formats

#### Standard Output (Default)
```bash
python scripts/provision_redis.py
```

#### Environment Variables (.env format)
```bash
python scripts/provision_redis.py --output-env > redis.env
```

#### JSON Format
```bash
python scripts/provision_redis.py --json > redis.json
```

### Integration with HoistScout

1. **Automatic provisioning**:
   ```bash
   # Provision and save to .env file
   python scripts/provision_redis.py --output-env > backend/.env.redis
   ```

2. **In your application**:
   ```python
   import os
   from redis import Redis
   
   # Load from provisioned URL
   redis_url = os.getenv('REDIS_URL')
   redis_client = Redis.from_url(redis_url)
   ```

3. **Docker Compose Integration**:
   ```yaml
   services:
     backend:
       environment:
         - REDIS_URL=${REDIS_URL}
   ```

## Command Line Options

- `--provider PROVIDER`: Choose specific provider (upstash, railway, aiven, local, auto)
- `--verify`: Verify the connection after provisioning
- `--test`: Run comprehensive Redis operation tests
- `--output-env`: Output in .env format
- `--json`: Output in JSON format
- `--help`: Show help message

## Examples

### Example 1: Quick Setup
```bash
# Set Upstash credentials
export UPSTASH_API_KEY="your-api-key"
export UPSTASH_EMAIL="your-email@example.com"

# Provision and verify
python scripts/provision_redis.py --verify
```

### Example 2: Production Setup
```bash
# Provision, verify, test, and save configuration
python scripts/provision_redis.py --verify --test --output-env > backend/.env.redis

# Source the environment
source backend/.env.redis

# Your Redis is ready to use!
echo $REDIS_URL
```

### Example 3: Development Setup
```bash
# Try local Redis first, fallback to cloud
python scripts/provision_redis.py --provider local --verify
```

## Error Handling

The script includes comprehensive error handling:
- Missing API credentials
- Network failures
- Provider API errors
- Connection timeouts
- Invalid configurations

## Testing

The script includes built-in tests for:
- Basic SET/GET operations
- Key expiration
- List operations
- Hash operations
- Connection stability

Run tests with:
```bash
python scripts/provision_redis.py --test
```

## Troubleshooting

### Upstash Issues
- Ensure API key and email are correct
- Check API key permissions at https://console.upstash.com/account/api
- Verify you haven't exceeded free tier limits

### Local Redis Issues
- Ensure Redis is running: `redis-cli ping`
- Check if Redis is bound to localhost
- Verify no firewall blocking port 6379

### General Issues
- Check network connectivity
- Verify environment variables are set
- Review detailed logs for specific errors

## Security Notes

- All cloud providers use SSL/TLS by default
- Credentials are never logged or exposed
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor usage to stay within free tier limits