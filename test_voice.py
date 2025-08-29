#!/usr/bin/env python3
"""
Wyoming Piper Voice Test Script

This script tests the Wyoming Piper TTS container by:
1. Connecting to the running container
2. Requesting available voice information
3. Synthesizing test text with the configured voice
4. Saving audio output to a WAV file
5. Optionally playing the audio

Usage:
    python3 test_voice.py [--host HOST] [--port PORT] [--play] [--text TEXT]

Requirements:
    pip install wyoming

Author: Claude Code
"""

import asyncio
import argparse
import io
import os
import subprocess
import sys
import wave
from pathlib import Path
from typing import List, Dict, Optional

try:
    from wyoming.audio import AudioChunk, AudioStop
    from wyoming.client import AsyncTcpClient
    from wyoming.tts import Synthesize, SynthesizeVoice
    from wyoming.info import Describe, Info
except ImportError:
    print("ERROR: Wyoming library not installed.")
    print("Install with: pip install wyoming")
    sys.exit(1)


def print_banner():
    """Print test banner"""
    print("=" * 60)
    print("     Wyoming Piper GPU Voice Test")
    print("=" * 60)


async def get_server_info(host: str, port: int) -> Optional[Dict]:
    """Get server information and available voices."""
    try:
        async with AsyncTcpClient(host, port) as client:
            print(f"✓ Connected to {host}:{port}")
            
            # Request server info
            await client.write_event(Describe().event())
            
            while True:
                event = await client.read_event()
                if event is None:
                    break
                    
                if Info.is_type(event.type):
                    info = Info.from_event(event)
                    return {
                        'name': info.name,
                        'version': info.version,
                        'description': info.description,
                        'voices': _extract_voices(info)
                    }
                    
    except Exception as e:
        print(f"✗ Failed to connect to {host}:{port}: {e}")
        return None


def _extract_voices(info: Info) -> List[Dict]:
    """Extract voice information from server info."""
    voices = []
    if info.tts:
        for tts_service in info.tts:
            for voice in tts_service.voices:
                if voice.installed:
                    voices.append({
                        'name': voice.name,
                        'languages': voice.languages or [],
                        'description': voice.description,
                        'installed': voice.installed
                    })
    return voices


async def synthesize_test_text(
    host: str, 
    port: int, 
    text: str, 
    output_file: str,
    voice_name: Optional[str] = None
) -> bool:
    """Synthesize text and save to WAV file."""
    try:
        async with AsyncTcpClient(host, port) as client:
            print(f"🎵 Synthesizing: \"{text}\"")
            
            # Configure voice if specified
            voice = None
            if voice_name:
                voice = SynthesizeVoice(name=voice_name)
                print(f"🎤 Using voice: {voice_name}")
            
            # Send synthesis request
            synthesize = Synthesize(text=text, voice=voice)
            await client.write_event(synthesize.event())
            
            # Collect audio response
            audio_data = bytearray()
            audio_params = None
            chunk_count = 0
            
            print("📥 Receiving audio data...", end=" ")
            
            while True:
                event = await client.read_event()
                if event is None:
                    print("\n✗ Connection lost during synthesis")
                    return False
                
                if AudioStop.is_type(event.type):
                    print(f"\n✓ Received {chunk_count} audio chunks")
                    break
                
                if AudioChunk.is_type(event.type):
                    chunk = AudioChunk.from_event(event)
                    chunk_count += 1
                    
                    # Store audio parameters from first chunk
                    if audio_params is None:
                        audio_params = {
                            'rate': chunk.rate,
                            'width': chunk.width,
                            'channels': chunk.channels
                        }
                        print(f"\n📊 Audio format: {chunk.rate}Hz, {chunk.width*8}-bit, {chunk.channels} channel(s)")
                    
                    audio_data.extend(chunk.audio)
                    print(".", end="", flush=True)
            
            # Save to WAV file
            if audio_params and audio_data:
                with wave.open(output_file, 'wb') as wav_file:
                    wav_file.setframerate(audio_params['rate'])
                    wav_file.setsampwidth(audio_params['width'])
                    wav_file.setnchannels(audio_params['channels'])
                    wav_file.writeframes(bytes(audio_data))
                
                duration = len(audio_data) / (audio_params['rate'] * audio_params['width'] * audio_params['channels'])
                file_size = len(audio_data)
                print(f"💾 Audio saved to: {output_file}")
                print(f"📏 Duration: {duration:.1f}s, Size: {file_size:,} bytes")
                return True
            
    except Exception as e:
        print(f"✗ Synthesis failed: {e}")
        return False
    
    return False


def play_audio(file_path: str) -> bool:
    """Attempt to play audio file using available system players."""
    if not os.path.exists(file_path):
        print(f"✗ Audio file not found: {file_path}")
        return False
    
    # List of common audio players to try
    players = [
        ['paplay'],  # PulseAudio
        ['aplay'],   # ALSA
        ['ffplay', '-nodisp', '-autoexit'],  # FFmpeg
        ['cvlc', '--play-and-exit', '--intf', 'dummy'],  # VLC
        ['mpg123'],  # mpg123
        ['play'],    # SoX
    ]
    
    print("🔊 Attempting to play audio...")
    
    for player_cmd in players:
        try:
            cmd = player_cmd + [file_path]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=10,
                check=True
            )
            if result.returncode == 0:
                print(f"✓ Played audio using: {player_cmd[0]}")
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    print("✗ No compatible audio player found")
    print("   Install one of: paplay, aplay, ffplay, vlc, mpg123, sox")
    print(f"   Or manually play: {file_path}")
    return False


def load_env_config() -> Dict[str, str]:
    """Load configuration from .env file."""
    env_file = Path(".env")
    config = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test Wyoming Piper TTS voice output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_voice.py                    # Basic test
  python3 test_voice.py --play             # Test and play audio
  python3 test_voice.py --text "Hello!"    # Custom text
  python3 test_voice.py --host 192.168.1.100 --port 10201  # Custom server
        """
    )
    
    parser.add_argument(
        '--host', 
        default='localhost', 
        help='Wyoming Piper server hostname (default: localhost)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=10200, 
        help='Wyoming Piper server port (default: 10200)'
    )
    parser.add_argument(
        '--text', 
        default="Hello! This is a test of the Wyoming Piper text to speech system. "
                "I am demonstrating the current voice model configuration. "
                "Can you hear the difference in voice characteristics?",
        help='Text to synthesize'
    )
    parser.add_argument(
        '--output', 
        default='test_output.wav',
        help='Output WAV file (default: test_output.wav)'
    )
    parser.add_argument(
        '--play', 
        action='store_true',
        help='Automatically play the generated audio'
    )
    parser.add_argument(
        '--voice',
        help='Override voice model (uses .env PIPER_VOICE by default)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load configuration
    env_config = load_env_config()
    configured_voice = env_config.get('PIPER_VOICE')
    
    if configured_voice:
        print(f"🔧 Configuration from .env:")
        print(f"   PIPER_VOICE = {configured_voice}")
    
    # Use specified voice or env voice
    target_voice = args.voice or configured_voice
    if target_voice:
        print(f"🎯 Target voice: {target_voice}")
    
    print()
    
    # Test server connection and get info
    print("🔍 Checking server information...")
    server_info = await get_server_info(args.host, args.port)
    
    if not server_info:
        print("❌ Cannot connect to Wyoming Piper server")
        print(f"   Make sure container is running: docker-compose ps")
        print(f"   Check logs: docker-compose logs wyoming-piper")
        sys.exit(1)
    
    print(f"📋 Server: {server_info['name']} v{server_info['version']}")
    if server_info['description']:
        print(f"   {server_info['description']}")
    
    # Show available voices
    voices = server_info['voices']
    if voices:
        print(f"\n🎤 Available voices ({len(voices)}):")
        for voice in voices[:5]:  # Show first 5
            langs = ', '.join(voice['languages']) if voice['languages'] else 'unknown'
            desc = f" - {voice['description']}" if voice['description'] else ""
            print(f"   • {voice['name']} ({langs}){desc}")
        
        if len(voices) > 5:
            print(f"   ... and {len(voices) - 5} more")
    else:
        print("\n⚠️  No voices reported by server")
    
    print()
    
    # Synthesize test audio
    success = await synthesize_test_text(
        args.host, 
        args.port, 
        args.text, 
        args.output,
        target_voice
    )
    
    if success:
        print(f"\n✅ Test completed successfully!")
        
        if args.play:
            print()
            play_audio(args.output)
        else:
            print(f"\n💡 To hear the voice, run: python3 test_voice.py --play")
            print(f"   Or manually play: {args.output}")
    else:
        print(f"\n❌ Test failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)