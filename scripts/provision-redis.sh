#!/bin/bash
# Redis Provisioning Wrapper Script
# Simplifies Redis provisioning for HoistScout

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
PROVIDER="auto"
OUTPUT_FORMAT="text"
VERIFY=false
TEST=false

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --provider PROVIDER    Provider to use (upstash|railway|aiven|local|auto)"
    echo "  -o, --output FORMAT        Output format (text|env|json)"
    echo "  -v, --verify               Verify connection after provisioning"
    echo "  -t, --test                 Run Redis operation tests"
    echo "  -s, --save FILE            Save configuration to file"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                         # Auto-provision with any provider"
    echo "  $0 -p upstash -v           # Use Upstash and verify"
    echo "  $0 -o env -s redis.env     # Save as .env file"
    echo "  $0 -p local -t             # Use local Redis and test"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--provider)
            PROVIDER="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -v|--verify)
            VERIFY=true
            shift
            ;;
        -t|--test)
            TEST=true
            shift
            ;;
        -s|--save)
            SAVE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Build command
CMD="python ${SCRIPT_DIR}/provision_redis.py"

# Add provider
if [ "$PROVIDER" != "auto" ]; then
    CMD="$CMD --provider $PROVIDER"
fi

# Add verify flag
if [ "$VERIFY" = true ]; then
    CMD="$CMD --verify"
fi

# Add test flag
if [ "$TEST" = true ]; then
    CMD="$CMD --test"
fi

# Add output format
case $OUTPUT_FORMAT in
    env)
        CMD="$CMD --output-env"
        ;;
    json)
        CMD="$CMD --json"
        ;;
esac

# Print header
echo -e "${GREEN}🔧 HoistScout Redis Provisioning${NC}"
echo "================================"

# Check for existing Redis URL
if [ ! -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}ℹ️  Existing REDIS_URL found: $REDIS_URL${NC}"
    echo ""
fi

# Run provisioning
if [ ! -z "$SAVE_FILE" ]; then
    echo -e "${GREEN}Provisioning Redis and saving to: $SAVE_FILE${NC}"
    $CMD > "$SAVE_FILE"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Configuration saved to: $SAVE_FILE${NC}"
        
        # Show how to use it
        if [[ "$SAVE_FILE" == *.env ]]; then
            echo ""
            echo "To use this configuration:"
            echo "  source $SAVE_FILE"
            echo "  echo \$REDIS_URL"
        fi
    else
        echo -e "${RED}❌ Failed to provision Redis${NC}"
        exit 1
    fi
else
    # Run without saving
    $CMD
fi

# Additional help for integration
if [ $? -eq 0 ] && [ "$OUTPUT_FORMAT" = "text" ] && [ -z "$SAVE_FILE" ]; then
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Save configuration: $0 -o env -s backend/.env.redis"
    echo "2. Load in your app: source backend/.env.redis"
    echo "3. Use in Docker: docker-compose --env-file backend/.env.redis up"
fi