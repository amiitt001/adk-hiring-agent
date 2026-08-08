"""
Launcher server - provides a web UI for users to enter their API keys
before starting the ADK hiring agent.
"""

import http.server
import json
import os
import subprocess
import signal
import sys
import threading
import urllib.parse

PORT = 8888
ADK_PORT = 8080
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
adk_process = None


def read_env():
    """Read current .env values."""
    values = {"GEMINI_API_KEY": "", "GITHUB_TOKEN": "", "MODEL_NAME": "gemini-2.5-flash"}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    values[key.strip()] = val.strip()
    return values


def write_env(gemini_key, github_token, model_name):
    """Write values to .env file."""
    with open(ENV_FILE, "w") as f:
        f.write(f"# Gemini API key (Required for running agents with Gemini)\n")
        f.write(f"GEMINI_API_KEY={gemini_key}\n\n")
        f.write(f"# Model Name\n")
        f.write(f"MODEL_NAME={model_name}\n\n")
        f.write(f"# GitHub Personal Access Token (Optional)\n")
        f.write(f"GITHUB_TOKEN={github_token}\n")


def start_adk_server():
    """Start the ADK web server as a subprocess."""
    global adk_process
    if adk_process and adk_process.poll() is None:
        adk_process.terminate()
        adk_process.wait(timeout=5)

    # Kill any existing process on ADK_PORT
    os.system(f"fuser -k {ADK_PORT}/tcp 2>/dev/null")

    venv_python = os.path.join(PROJECT_DIR, "venv", "bin", "python")
    venv_adk = os.path.join(PROJECT_DIR, "venv", "bin", "adk")

    if os.path.exists(venv_adk):
        cmd = [venv_adk, "web", "--port", str(ADK_PORT), PROJECT_DIR.split("/")[-1]]
        cwd = os.path.dirname(PROJECT_DIR)
    else:
        cmd = ["adk", "web", "--port", str(ADK_PORT), PROJECT_DIR.split("/")[-1]]
        cwd = os.path.dirname(PROJECT_DIR)

    env = os.environ.copy()
    env_values = read_env()
    env.update(env_values)

    adk_process = subprocess.Popen(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print(f"✅ ADK server starting on port {ADK_PORT}...")


LAUNCHER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Hiring Agent - Setup</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0a0a1a;
            color: #e0e0e0;
            overflow: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 60%);
            z-index: 0;
            animation: bgShift 20s ease-in-out infinite alternate;
        }

        @keyframes bgShift {
            0% { transform: translate(0, 0) rotate(0deg); }
            100% { transform: translate(-2%, -1%) rotate(2deg); }
        }

        .container {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 520px;
            padding: 20px;
        }

        .card {
            background: rgba(15, 15, 35, 0.85);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(99, 102, 241, 0.15);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                        0 0 80px rgba(99, 102, 241, 0.05);
            animation: cardEntry 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes cardEntry {
            from { opacity: 0; transform: translateY(30px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
        }

        .logo h1 {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(135deg, #c7d2fe, #a5b4fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 32px;
            line-height: 1.5;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            color: #a5b4fc;
            margin-bottom: 8px;
        }

        label .badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-required {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
        }

        .badge-optional {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
        }

        input, select {
            width: 100%;
            padding: 12px 16px;
            background: rgba(30, 30, 60, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 10px;
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            outline: none;
            transition: all 0.25s ease;
        }

        input:focus, select:focus {
            border-color: rgba(99, 102, 241, 0.6);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            background: rgba(30, 30, 60, 0.8);
        }

        input::placeholder {
            color: #4b5563;
        }

        .input-hint {
            font-size: 11px;
            color: #4b5563;
            margin-top: 6px;
            line-height: 1.4;
        }

        .input-hint a {
            color: #818cf8;
            text-decoration: none;
        }

        .input-hint a:hover {
            text-decoration: underline;
        }

        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .status {
            margin-top: 16px;
            padding: 12px 16px;
            border-radius: 10px;
            font-size: 13px;
            display: none;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .status-success {
            display: block;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.25);
            color: #34d399;
        }

        .status-error {
            display: block;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.25);
            color: #f87171;
        }

        .status-loading {
            display: block;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.2), transparent);
            margin: 24px 0;
        }

        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 11px;
            color: #374151;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <div class="logo-icon">🤖</div>
                <h1>AI Hiring Agent</h1>
            </div>
            <p class="subtitle">
                Configure your API keys to get started with the multi-agent hiring evaluation system.
            </p>

            <form id="configForm">
                <div class="form-group">
                    <label>
                        Gemini API Key
                        <span class="badge badge-required">Required</span>
                    </label>
                    <input type="password" id="geminiKey" placeholder="Enter your Gemini API key"
                           value="__GEMINI_KEY__" required>
                    <p class="input-hint">
                        Get your key at <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a>
                    </p>
                </div>

                <div class="form-group">
                    <label>
                        Model
                        <span class="badge badge-optional">Optional</span>
                    </label>
                    <select id="modelName">
                        <option value="gemini-2.5-flash" __SEL_25F__>Gemini 2.5 Flash (Recommended)</option>
                        <option value="gemini-2.0-flash" __SEL_20F__>Gemini 2.0 Flash</option>
                        <option value="gemini-2.5-pro" __SEL_25P__>Gemini 2.5 Pro</option>
                    </select>
                </div>

                <div class="divider"></div>

                <div class="form-group">
                    <label>
                        GitHub Token
                        <span class="badge badge-optional">Optional</span>
                    </label>
                    <input type="password" id="githubToken" placeholder="ghp_xxxxxxxxxxxx"
                           value="__GITHUB_TOKEN__">
                    <p class="input-hint">
                        For higher GitHub API rate limits. Generate at
                        <a href="https://github.com/settings/tokens" target="_blank">github.com/settings/tokens</a>
                    </p>
                </div>

                <button type="submit" class="btn btn-primary" id="submitBtn">
                    🚀 Launch Hiring Agent
                </button>
            </form>

            <div id="status" class="status"></div>

            <div class="footer">
                Built by Amit Verma · Powered by Google ADK & Gemini
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('configForm');
        const statusEl = document.getElementById('status');
        const submitBtn = document.getElementById('submitBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const geminiKey = document.getElementById('geminiKey').value.trim();
            const githubToken = document.getElementById('githubToken').value.trim();
            const modelName = document.getElementById('modelName').value;

            if (!geminiKey) {
                showStatus('error', '⚠️ Gemini API Key is required.');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Starting...';
            showStatus('loading', '⏳ Saving configuration and starting the agent server...');

            try {
                const response = await fetch('/save-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        gemini_key: geminiKey,
                        github_token: githubToken,
                        model_name: modelName
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showStatus('success', '✅ Configuration saved! Redirecting to the agent UI...');
                    setTimeout(() => {
                        window.location.href = 'http://' + window.location.hostname + ':__ADK_PORT__';
                    }, 2000);
                } else {
                    showStatus('error', '❌ Error: ' + (data.error || 'Unknown error'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '🚀 Launch Hiring Agent';
                }
            } catch (err) {
                showStatus('error', '❌ Connection failed: ' + err.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 Launch Hiring Agent';
            }
        });

        function showStatus(type, message) {
            statusEl.className = 'status status-' + type;
            statusEl.textContent = message;
        }
    </script>
</body>
</html>"""


class LauncherHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            env = read_env()
            html = LAUNCHER_HTML
            html = html.replace("__GEMINI_KEY__", env.get("GEMINI_API_KEY", ""))
            html = html.replace("__GITHUB_TOKEN__", env.get("GITHUB_TOKEN", ""))
            html = html.replace("__ADK_PORT__", str(ADK_PORT))

            model = env.get("MODEL_NAME", "gemini-2.5-flash")
            html = html.replace("__SEL_25F__", "selected" if model == "gemini-2.5-flash" else "")
            html = html.replace("__SEL_20F__", "selected" if model == "gemini-2.0-flash" else "")
            html = html.replace("__SEL_25P__", "selected" if model == "gemini-2.5-pro" else "")

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/save-config":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()

            try:
                data = json.loads(body)
                gemini_key = data.get("gemini_key", "").strip()
                github_token = data.get("github_token", "").strip()
                model_name = data.get("model_name", "gemini-2.5-flash").strip()

                if not gemini_key:
                    self._json_response({"success": False, "error": "Gemini API key is required"})
                    return

                write_env(gemini_key, github_token, model_name)

                # Start ADK server in background
                threading.Thread(target=start_adk_server, daemon=True).start()

                self._json_response({"success": True, "message": "Configuration saved"})

            except Exception as e:
                self._json_response({"success": False, "error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def cleanup(signum, frame):
    global adk_process
    print("\n🛑 Shutting down...")
    if adk_process and adk_process.poll() is None:
        adk_process.terminate()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"""
╔══════════════════════════════════════════════════╗
║        🤖 AI Hiring Agent - Launcher             ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Setup page:  http://localhost:{PORT}              ║
║  Agent UI:    http://localhost:{ADK_PORT} (after setup) ║
║                                                  ║
╚══════════════════════════════════════════════════╝
""")

    server = http.server.HTTPServer(("0.0.0.0", PORT), LauncherHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cleanup(None, None)
