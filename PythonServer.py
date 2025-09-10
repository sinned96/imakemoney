#!/usr/bin/env python3
"""
Simple Python server for the imakemoney application.
This server can be launched from the gallery editor's "Aufnahme" button.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Server configuration
DEFAULT_PORT = 8000
DEFAULT_HOST = "localhost"

def main():
    """Main server function"""
    port = DEFAULT_PORT
    host = DEFAULT_HOST
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # Change to the directory where the server is located
    server_dir = Path(__file__).parent
    os.chdir(server_dir)
    
    # Create HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"Server starting on {host}:{port}")
            print(f"Serving directory: {server_dir}")
            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except OSError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()