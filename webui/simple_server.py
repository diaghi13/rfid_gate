#!/usr/bin/env python3
"""
Simple Web Server for RFID Gate Web UI
=====================================

Server semplice per servire la Web UI senza dipendenze FastAPI
"""

import http.server
import socketserver
import os
import mimetypes
from urllib.parse import urlparse, unquote

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        """Handle GET requests with custom routing"""
        parsed_path = urlparse(self.path)
        path = unquote(parsed_path.path)
        
        # Root redirect to demo index
        if path == '/':
            path = '/demo-index.html'
        
        # Remove leading slash and normalize path
        if path.startswith('/'):
            path = path[1:]
        
        # Security check - prevent directory traversal
        if '..' in path:
            self.send_error(403, "Forbidden")
            return
        
        file_path = os.path.join(os.getcwd(), path)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.js'):
                    content_type = 'text/javascript'
                else:
                    content_type = 'application/octet-stream'
            
            # Send response
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-length', len(content))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(content)
                
                print(f"✅ Served: {path}")
                
            except Exception as e:
                print(f"❌ Error serving {path}: {e}")
                self.send_error(500, f"Internal Server Error: {e}")
        else:
            print(f"❌ File not found: {file_path}")
            self.send_error(404, f"File not found: {path}")

def main():
    PORT = 8082
    
    # Assicuriamoci di essere nella directory corretta
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🌐 RFID Gate Web UI - Simple Server")
    print("=" * 40)
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📍 Server starting on port {PORT}")
    print(f"🔗 Access URLs:")
    print(f"   • Home/Login: http://localhost:{PORT}/")
    print(f"   • Dashboard: http://localhost:{PORT}/templates/dashboard.html")
    print(f"   • Control: http://localhost:{PORT}/templates/control.html")
    print(f"   • Logs: http://localhost:{PORT}/templates/logs.html")
    print(f"   • Config: http://localhost:{PORT}/templates/config.html")
    print(f"🛑 Press Ctrl+C to stop")
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()