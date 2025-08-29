#!/bin/bash
# Wyoming Piper Voice Test Script (Bash Version)
# 
# This script provides a simple way to test Wyoming Piper TTS without Python dependencies.
# It uses netcat and basic HTTP tools to communicate with the container.
#
# Usage: ./test_voice.sh [HOST] [PORT] [TEXT]
#
# Author: Claude Code

set -e

# Configuration
HOST=${1:-localhost}
PORT=${2:-10200}
TEXT=${3:-"Hello! This is a test of the Wyoming Piper text to speech system using a bash script."}
OUTPUT_FILE="test_output_bash.wav"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo "============================================================"
    echo "     Wyoming Piper GPU Voice Test (Bash Version)"
    echo "============================================================"
}

check_dependencies() {
    local missing_deps=()
    
    # Check for required tools
    if ! command -v nc >/dev/null 2>&1 && ! command -v netcat >/dev/null 2>&1; then
        missing_deps+=("netcat")
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}✗ Missing dependencies: ${missing_deps[*]}${NC}"
        echo "  Install with:"
        echo "    Ubuntu/Debian: sudo apt install netcat-openbsd curl"
        echo "    CentOS/RHEL:   sudo yum install nmap-ncat curl"
        echo "    macOS:         brew install netcat curl"
        return 1
    fi
    
    return 0
}

test_connection() {
    echo -e "${BLUE}🔍 Testing connection to $HOST:$PORT...${NC}"
    
    if timeout 5 bash -c "echo >/dev/tcp/$HOST/$PORT" 2>/dev/null; then
        echo -e "${GREEN}✓ Connection successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to $HOST:$PORT${NC}"
        echo "  Make sure Wyoming Piper container is running:"
        echo "    docker-compose ps"
        echo "    docker-compose logs wyoming-piper"
        return 1
    fi
}

get_env_voice() {
    if [ -f ".env" ]; then
        local voice=$(grep "^PIPER_VOICE=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
        if [ -n "$voice" ]; then
            echo "$voice"
            return 0
        fi
    fi
    echo "en_US-amy-medium"  # default
}

synthesize_with_python_fallback() {
    echo -e "${YELLOW}📝 Text to synthesize: \"$TEXT\"${NC}"
    
    # Try Python script if available
    if [ -f "test_voice.py" ] && command -v python3 >/dev/null 2>&1; then
        echo -e "${BLUE}🐍 Using Python test script...${NC}"
        
        if python3 test_voice.py --host "$HOST" --port "$PORT" --text "$TEXT" --output "$OUTPUT_FILE" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Audio generated successfully${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Python script failed, trying manual method...${NC}"
        fi
    fi
    
    echo -e "${RED}✗ Advanced synthesis not available without Python${NC}"
    echo "  Install Python dependencies: pip install -r requirements-test.txt"
    echo "  Then run: python3 test_voice.py --play"
    return 1
}

play_audio() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Audio file not found: $file${NC}"
        return 1
    fi
    
    echo -e "${BLUE}🔊 Attempting to play audio...${NC}"
    
    # List of audio players to try
    local players=("paplay" "aplay" "ffplay -nodisp -autoexit" "cvlc --play-and-exit --intf dummy" "mpg123" "play")
    
    for player_cmd in "${players[@]}"; do
        local player=$(echo $player_cmd | cut -d' ' -f1)
        if command -v "$player" >/dev/null 2>&1; then
            echo -e "${BLUE}🎵 Using $player...${NC}"
            if $player_cmd "$file" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Audio played successfully${NC}"
                return 0
            fi
        fi
    done
    
    echo -e "${YELLOW}⚠️  No compatible audio player found${NC}"
    echo "  Install one of: paplay, aplay, ffplay, vlc, mpg123, sox"
    echo -e "${BLUE}💡 Manually play: $file${NC}"
    return 1
}

show_container_info() {
    echo -e "${BLUE}📋 Container information:${NC}"
    
    if command -v docker >/dev/null 2>&1; then
        # Show container status
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q wyoming; then
            echo "  Container status:"
            docker ps --format "  {{.Names}}: {{.Status}}" | grep wyoming
        fi
        
        # Show environment variables if container is running
        if docker exec wyoming-piper env 2>/dev/null | grep -q PIPER_VOICE; then
            local container_voice=$(docker exec wyoming-piper env 2>/dev/null | grep PIPER_VOICE | cut -d'=' -f2)
            echo "  Container PIPER_VOICE: $container_voice"
        fi
    fi
    
    # Show local .env configuration
    local env_voice=$(get_env_voice)
    echo "  Local .env PIPER_VOICE: $env_voice"
}

main() {
    print_banner
    
    echo -e "${BLUE}🔧 Configuration:${NC}"
    echo "  Host: $HOST"
    echo "  Port: $PORT"
    echo "  Output: $OUTPUT_FILE"
    echo
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Test connection
    if ! test_connection; then
        exit 1
    fi
    
    # Show container info
    show_container_info
    echo
    
    # Synthesize audio
    if synthesize_with_python_fallback; then
        echo
        play_audio "$OUTPUT_FILE"
        
        echo
        echo -e "${GREEN}✅ Test completed!${NC}"
        echo -e "${BLUE}💡 For more detailed testing, use: python3 test_voice.py --play${NC}"
    else
        echo
        echo -e "${YELLOW}⚠️  For full functionality, install Python dependencies:${NC}"
        echo "    pip install -r requirements-test.txt"
        echo "    python3 test_voice.py --play"
        exit 1
    fi
}

# Make sure we're in the script directory
cd "$(dirname "$0")"

# Run main function
main "$@"