# wyoming-piper-gpu
Wyoming Piper TTS docker container with Nvidia GPU support for Home-Assistant

https://github.com/rhasspy/wyoming-piper


[![Publish Docker image](https://github.com/slackr31337/wyoming-piper-gpu/actions/workflows/docker-image.yml/badge.svg)](https://github.com/slackr31337/wyoming-piper-gpu/actions/workflows/docker-image.yml)


docker pull ghcr.io/slackr31337/wyoming-piper-gpu:latest


# Configuration

## Quick Start with Environment File

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` to customize your voice and settings:
   ```bash
   nano .env  # or your preferred editor
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

## Voice Model Configuration

The container supports numerous voice models that download automatically on first use:

### Popular English Voices
- `en_US-amy-medium` - Female, clear (default)
- `en_US-lessac-medium` - Female, expressive  
- `en_US-ryan-medium` - Male, clear
- `en_US-kimberly-medium` - Female, warm
- `en_GB-alan-medium` - Male, British

### Finding More Voices
- **Browse all available voices:** [HuggingFace - rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
- **Listen to voice samples:** [Piper Voice Samples](https://rhasspy.github.io/piper-samples/)

Voice models are automatically downloaded on first use, so you can try any voice from the repository by setting it in your `.env` file.

### Voice Quality Parameters
- `PIPER_LENGTH` - Speech speed (0.5=fast, 2.0=slow)
- `PIPER_NOISE` - Voice variation (0.0=monotone, 1.0=expressive)
- `PIPER_NOISEW` - Pronunciation variation
- `PIPER_SILENCE` - Pause duration between sentences

See `.env.example` for complete configuration options and available voices.

## Environment Variables (Legacy Method)

You can also set environment variables directly:

> PIPER_VOICE="en_US-lessac-medium"
> 
> PIPER_LENGTH="1.0"
> 
> PIPER_NOISE="0.667"
> 
> PIPER_NOISEW="0.333"
> 
> PIPER_SPEAKER="0"
> 
> PIPER_SILENCE="1.2"
>
> LOG_LEVEL="debug" # For debug logging
>
> STREAMING=false # To disable streaming


# Docker Compose Usage

## Using .env file (Recommended)

The provided `docker-compose.yml` uses environment variables from `.env` file:

```bash
# Copy and customize configuration
cp .env.example .env
nano .env

# Start container
docker-compose up -d
```

## Manual Docker Compose Configuration

If you prefer to specify environment variables directly:

```yaml
services:
  wyoming-piper:  
    image: slackr31337/wyoming-piper-gpu:latest  
    container_name: wyoming-piper
    environment:  
      - PIPER_VOICE=en_US-amy-medium
      - PIPER_LENGTH=1.0
      - PIPER_NOISE=0.667
      - PIPER_NOISEW=0.333
      - PIPER_SILENCE=1.2
      - LOG_LEVEL=info
      - STREAMING=true
    ports:  
      - "10200:10200"
    volumes:  
      - ./data:/data  
    restart: unless-stopped
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities:
                - gpu
                - utility
                - compute
```

## Data Persistence

Voice models are automatically downloaded to the `./data` directory on first use. This directory is mounted as a volume for persistence between container restarts.

# Voice Testing

## Quick Test

Test your voice configuration and hear the output:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run test with audio playback
python3 test_voice.py --play
```

## Test Options

### Python Test Script (Recommended)
Full-featured test with detailed output:

```bash
# Basic test
python3 test_voice.py

# Test with custom text
python3 test_voice.py --text "Hello, this is my custom message!"

# Test and play audio automatically
python3 test_voice.py --play

# Test specific voice model
python3 test_voice.py --voice en_US-ryan-medium --play

# Test remote server
python3 test_voice.py --host 192.168.1.100 --port 10201 --play
```

### Simple Bash Test
Quick test without Python dependencies:

```bash
# Basic test (requires netcat/curl)
./test_voice.sh

# Custom text
./test_voice.sh localhost 10200 "Your custom message here"
```

### Docker Test
Test without any local dependencies:

```bash
# Run test from Docker container
./test_voice_docker.sh

# Custom text
./test_voice_docker.sh "Your custom message here"
```

## Test Output

All test scripts will:
- ✅ Verify connection to Wyoming Piper container
- 📋 Show server info and available voices  
- 🎤 Display which voice model is configured
- 🎵 Synthesize test text to speech
- 💾 Save output as WAV file (`test_output.wav`)
- 🔊 Play audio automatically (with `--play` option)

## Troubleshooting Tests

**Connection Failed:**
```bash
# Check container status
docker-compose ps

# Check container logs  
docker-compose logs wyoming-piper

# Restart container
docker-compose restart wyoming-piper
```

**Audio Playback Issues:**
```bash
# Install audio player (Ubuntu/Debian)
sudo apt install pulseaudio-utils alsa-utils

# Test audio system
speaker-test -t sine -f 440 -c 2 -s 2

# Manually play output
aplay test_output.wav
# or
paplay test_output.wav
```

**Wrong Voice Model:**
- Verify `.env` file has correct `PIPER_VOICE` setting
- Restart container after changing voice: `docker-compose restart wyoming-piper`
- Check container environment: `docker exec wyoming-piper env | grep PIPER`
