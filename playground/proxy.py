#!/usr/bin/env python3
"""
Lightweight CORS Proxy & Local Web Server for Jev Decision Sandbox
Zero external dependencies (uses only standard library).

Usage:
    python3 lab-jev-decision/proxy.py
    
    # Or with your API Key pre-configured:
    export JEV_API_KEY="your_api_key"
    python3 lab-jev-decision/proxy.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000
TARGET_HOST = "https://www.jevai.org"

import urllib.parse

def get_markdown_viewer_html(title, md_content, raw_url):
    json_content = json.dumps(md_content).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | ML-Learn</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Thai", Helvetica, Arial, sans-serif;
    }}
    .markdown-body {{
      box-sizing: border-box;
      min-width: 200px;
      max-width: 920px;
      margin: 0 auto;
      padding: 36px;
      background-color: transparent;
      color: #1e293b;
    }}
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {{
      border-bottom-color: #e2e8f0;
      color: #0f172a;
    }}
    .markdown-body code {{
      background-color: #f1f5f9;
      color: #0f172a;
      border-radius: 4px;
      padding: 0.2em 0.4em;
    }}
    .markdown-body pre {{
      background-color: #0f172a !important;
      color: #f8fafc;
      border-radius: 8px;
    }}
    .markdown-body pre code {{
      background-color: transparent !important;
      color: #f8fafc;
      padding: 0;
    }}
    @media (max-width: 767px) {{
      .markdown-body {{
        padding: 16px;
      }}
    }}
  </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col">
  <!-- Top Navigation Bar -->
  <header class="bg-white/95 backdrop-blur border-b border-slate-200 sticky top-0 z-20 px-4 sm:px-8 py-3 flex items-center justify-between shadow-xs">
    <div class="flex items-center gap-3">
      <a href="/index.html" class="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-indigo-600 transition">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">ML</span>
        <span class="hidden sm:inline">ML-Learn Portal</span>
      </a>
      <span class="text-slate-300">/</span>
      <span class="text-xs sm:text-sm font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{title}</span>
    </div>

    <div class="flex items-center gap-2 sm:gap-3">
      <a href="/lab-jev-decision/index.html" class="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium border border-indigo-200 transition flex items-center gap-1">
        🧪 Jev Sandbox
      </a>
      <a href="/24-ML-System1-Decision-Models-Jev.html" class="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium border border-emerald-200 transition flex items-center gap-1">
        📖 บทที่ 24
      </a>
      <a href="{raw_url}" class="text-xs px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-100 font-medium transition flex items-center gap-1">
        📄 Raw Markdown
      </a>
    </div>
  </header>

  <!-- Main Content Container -->
  <main class="flex-1 max-w-4xl w-full mx-auto my-6 sm:my-8 px-4">
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <article id="content" class="markdown-body"></article>
    </div>
  </main>

  <footer class="text-center py-6 text-xs text-slate-400 border-t border-slate-200 bg-white mt-auto">
    ML-Learn Curriculum • Jev System 1 Decision Model
  </footer>

  <script>
    const rawMarkdown = {json_content};
    if (window.marked) {{
      marked.setOptions({{
        gfm: true,
        breaks: true
      }});
      document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
    }} else {{
      const pre = document.createElement('pre');
      pre.textContent = rawMarkdown;
      document.getElementById('content').appendChild(pre);
    }}
  </script>
</body>
</html>"""

class JevProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Inject CORS headers for all responses
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, Origin, User-Agent")
        super().end_headers()

    def guess_type(self, path):
        ctype = super().guess_type(path)
        if ctype.startswith("text/") or ctype in ("application/json", "application/javascript"):
            if "charset=" not in ctype.lower():
                ctype += "; charset=utf-8"
        return ctype

    def do_OPTIONS(self):
        # Handle preflight CORS requests
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        # If the path starts with /api/, proxy to jevai.org
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        else:
            super().do_POST()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
            return

        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Serve markdown files as formatted HTML when viewed in browser
        if clean_path.endswith(".md") and "raw" not in query_params:
            accept_header = self.headers.get("Accept", "")
            if "text/html" in accept_header:
                self.serve_markdown_as_html(clean_path)
                return

        super().do_GET()

    def serve_markdown_as_html(self, clean_path):
        file_path = self.translate_path(clean_path)
        if not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                md_content = f.read()
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")
            return

        filename = os.path.basename(clean_path)
        raw_url = f"{clean_path}?raw=1"
        html = get_markdown_viewer_html(filename, md_content, raw_url)
        html_bytes = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

    def proxy_request(self, method):
        target_url = f"{TARGET_HOST}{self.path}"
        
        # Read incoming request body if POST
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Check if the request targets OpenThai-SystemOne
        is_openthai = False
        if body:
            try:
                payload = json.loads(body.decode('utf-8'))
                model_name = payload.get("model", "")
                if "OpenThai" in model_name:
                    is_openthai = True
                    target_url = os.environ.get("OPENTHAI_API_ENDPOINT", "https://api.iapp.co.th/v3/store/openthai/systemone")
            except Exception:
                pass

        # Prepare outgoing headers (include standard User-Agent to avoid Cloudflare 1010 block)
        user_agent = self.headers.get("User-Agent")
        if not user_agent or "python" in user_agent.lower():
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

        headers = {
            "User-Agent": user_agent,
            "Content-Type": self.headers.get("Content-Type", "application/json"),
            "Accept": "application/json"
        }

        # Check authorization header
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            if is_openthai and os.environ.get("IAPP_API_KEY"):
                auth_header = f"Bearer {os.environ.get('IAPP_API_KEY')}"
            elif os.environ.get("JEV_API_KEY"):
                auth_header = f"Bearer {os.environ.get('JEV_API_KEY')}"
            
        if auth_header:
            headers["Authorization"] = auth_header

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read()
                print(f"\n[Proxy {method} {self.path} -> HTTP {response.getcode()}]:\n{res_body.decode('utf-8', errors='ignore')}\n", flush=True)
                self.send_response(response.getcode())
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(res_body)

        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.end_headers()
            self.wfile.write(err_body)

        except Exception as e:
            err_json = json.dumps({"error": str(e), "message": "Proxy failed to reach Jev API"}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_json)

def run():
    # Change working directory to project root (one level up from this script)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    server_address = ("", PORT)
    httpd = HTTPServer(server_address, JevProxyHandler)
    
    print("\n" + "=" * 65)
    print("🚀 Jev Model Local Proxy & Web Server Started")
    print("=" * 65)
    print(f"• Local Sandbox URL:  http://localhost:{PORT}/lab-jev-decision/index.html")
    print(f"• Course Portal:      http://localhost:{PORT}/index.html")
    print(f"• Proxied API Target: {TARGET_HOST}")
    if os.environ.get("JEV_API_KEY"):
        print("• JEV_API_KEY:        Detected from environment variable ✅")
    else:
        print("• JEV_API_KEY:        Will use the key entered in browser UI")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
