#!/usr/bin/env python3
"""
Claude Code -> OpenRouter Proxy
Translates Anthropic API format to OpenRouter format for using non-Anthropic models
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import ssl
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file, overriding existing values"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    # Always override environment with .env values
                    os.environ[key] = value

# Load .env file at startup
load_env_file()

# Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
TARGET_MODEL = "moonshotai/kimi-k2.5"  # Change this to use different models
PROXY_PORT = 8080

class AnthropicToOpenRouterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_POST(self):
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            print(f"[DEBUG] Received request: {len(body)} bytes")
            
            try:
                # Parse Anthropic request
                anthropic_request = json.loads(body)
                print(f"[DEBUG] Request model: {anthropic_request.get('model', 'unknown')}")
                
                # Convert to OpenRouter format
                openrouter_request = self.convert_request(anthropic_request)
                
                # Forward to OpenRouter
                response = self.forward_to_openrouter(openrouter_request)
                
                # Convert response back to Anthropic format
                anthropic_response = self.convert_response(response)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(anthropic_response).encode())
                print(f"[DEBUG] Response sent successfully")
                
            except ConnectionAbortedError as e:
                # Client disconnected (WinError 10053) - log and ignore
                print(f"[WARNING] Client disconnected during request: {e}")
                return
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode error: {e}")
                try:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode())
                except ConnectionAbortedError:
                    print(f"[WARNING] Client disconnected during error response")
                    return
            except Exception as e:
                print(f"[ERROR] Request processing error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                except ConnectionAbortedError:
                    print(f"[WARNING] Client disconnected during error response")
                    return
        except ConnectionAbortedError as e:
            # Handle connection abort at outer level
            print(f"[WARNING] Client disconnected: {e}")
            return
        except Exception as e:
            print(f"[CRITICAL] Handler error: {e}")
            import traceback
            traceback.print_exc()
    
    def do_GET(self):
        # Handle GET requests (models list, etc.)
        if '/models' in self.path:
            # Return a fake models list that includes our target model
            models = {
                "data": [
                    {
                        "id": TARGET_MODEL,
                        "object": "model",
                        "created": 1700000000,
                        "owned_by": "openrouter"
                    }
                ]
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(models).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def convert_request(self, anthropic_request):
        """Convert Anthropic API request to OpenRouter format"""
        openrouter_request = {
            "model": TARGET_MODEL,
            "messages": [],
            "stream": False,  # Disable streaming to get regular JSON response
            "temperature": anthropic_request.get("temperature", 1.0),
            "max_tokens": anthropic_request.get("max_tokens", 4096)
        }
        
        # Handle system message
        system = anthropic_request.get("system", "")
        if system:
            openrouter_request["messages"].append({
                "role": "system",
                "content": system
            })
        
        # Convert messages
        for msg in anthropic_request.get("messages", []):
            openrouter_request["messages"].append({
                "role": msg.get("role"),
                "content": msg.get("content", "")
            })
        
        # Handle tools if present
        if "tools" in anthropic_request:
            openrouter_request["tools"] = anthropic_request["tools"]
        
        return openrouter_request
    
    def forward_to_openrouter(self, request_data):
        """Send request to OpenRouter API"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        # Never log API key material, even prefixes.
        print("[DEBUG] OpenRouter API key loaded from environment")
        
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://localhost:8080",
            "X-Title": "Claude-Code-Proxy",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(request_data).encode(),
            headers=headers,
            method="POST"
        )
        
        # Create SSL context that doesn't verify certificates (for simplicity)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
                response_body = response.read().decode()
                print(f"[DEBUG] OpenRouter raw response: {response_body[:500]}")
                return json.loads(response_body)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode error: {e}")
            print(f"[ERROR] Raw response was: {response_body[:500] if 'response_body' in locals() else 'N/A'}")
            raise
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"[ERROR] OpenRouter returned {e.code}: {error_body}")
            raise Exception(f"HTTP Error {e.code}: {error_body}")
    
    def convert_response(self, openrouter_response):
        """Convert OpenRouter response to Anthropic format"""
        choice = openrouter_response.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        anthropic_response = {
            "id": openrouter_response.get("id", "msg_"),
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": message.get("content", "")
                }
            ],
            "model": TARGET_MODEL,
            "stop_reason": "end_turn" if choice.get("finish_reason") == "stop" else None,
            "usage": {
                "input_tokens": openrouter_response.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": openrouter_response.get("usage", {}).get("completion_tokens", 0)
            }
        }
        
        return anthropic_response

def main():
    server = HTTPServer(('127.0.0.1', PROXY_PORT), AnthropicToOpenRouterHandler)
    print(f"🚀 Claude Code -> OpenRouter Proxy")
    print(f"   Target Model: {TARGET_MODEL}")
    print(f"   Listening on: http://127.0.0.1:{PROXY_PORT}")
    
    # Check env var first, then .env file
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(f"   API Key: ✗ Not found in environment")
        print(f"   Checking .env file...")
    else:
        print(f"   API Key: ✓ Set (from environment)")
    print()
    print(f"To use with Claude Code:")
    print(f"  $env:ANTHROPIC_BASE_URL=\"http://127.0.0.1:{PROXY_PORT}/v1\"")
    print(f"  claude")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Proxy stopped by user")
    except Exception as e:
        print(f"\n💥 Proxy error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[Proxy exited - press Enter to close]")
        input()
    sys.exit(0)

if __name__ == "__main__":
    main()
