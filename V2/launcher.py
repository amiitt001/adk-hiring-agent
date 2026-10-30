"""
Launcher server - provides a web UI for users to enter and test their API keys
before starting the ADK hiring agent.
"""

import http.server
import html as html_module
import json
import re
import os
import signal
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import requests

PORT = int(os.getenv("PORT", "8888"))
ADK_PORT = int(os.getenv("ADK_PORT", "8080"))
HOST = os.getenv("HOST", "127.0.0.1")
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
adk_process = None


def read_env():
    """Read current .env values, keeping track of standard and custom keys."""
    env_data = {
        "GEMINI_API_KEY": "",
        "GITHUB_TOKEN": "",
        "MODEL_NAME": "gemini-3.5-flash",
        "custom_keys": {}
    }

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key in ("GEMINI_API_KEY", "GITHUB_TOKEN", "MODEL_NAME"):
                        env_data[key] = val
                    elif key:
                        env_data["custom_keys"][key] = val
    for key in ("GEMINI_API_KEY", "GITHUB_TOKEN", "MODEL_NAME"):
        if os.getenv(key):
            env_data[key] = os.environ[key]
    return env_data


def write_env(gemini_key, github_token, model_name, custom_keys=None):
    """Write standard and custom API key values to .env file."""
    if any("\n" in value or "\r" in value for value in (gemini_key, github_token, model_name)):
        raise ValueError("Configuration values must not contain newlines")
    lines = [
        "# Gemini API key (Required for running agents with Gemini)",
        f"GEMINI_API_KEY={gemini_key}",
        "",
        "# Model Name",
        f"MODEL_NAME={model_name}",
        "",
        "# GitHub Personal Access Token (Optional for higher rate limits)",
        f"GITHUB_TOKEN={github_token}",
        ""
    ]

    if custom_keys and isinstance(custom_keys, dict):
        custom_lines = []
        for k, v in custom_keys.items():
            k_clean = k.strip().upper().replace(" ", "_")
            v_clean = v.strip()
            reserved = {"GEMINI_API_KEY", "GOOGLE_API_KEY", "GITHUB_TOKEN", "MODEL_NAME", "PATH", "PYTHONPATH"}
            if (re.fullmatch(r"[A-Z_][A-Z0-9_]*", k_clean) and k_clean not in reserved
                    and v_clean and not any(ch in v_clean for ch in "\r\n")):
                custom_lines.append(f"{k_clean}={v_clean}")
        if custom_lines:
            lines.append("# Custom API Keys & Environment Variables")
            lines.extend(custom_lines)
            lines.append("")

    payload = "\n".join(lines)
    env_dir = os.path.dirname(ENV_FILE)
    fd, temp_path = tempfile.mkstemp(prefix=".env.", dir=env_dir, text=True)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(payload)
        os.replace(temp_path, ENV_FILE)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def validate_gemini_key(api_key):
    """Test if a Gemini API key is valid using Google AI Studio REST API."""
    if not api_key:
        return False, "Gemini API Key is required."
    try:
        resp = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": api_key}, timeout=10
        )
        if resp.status_code == 200:
            return True, "API Key is valid and active!"
        else:
            err_msg = f"HTTP {resp.status_code}"
            try:
                data = resp.json()
                if "error" in data and "message" in data["error"]:
                    err_msg = data["error"]["message"]
            except Exception:
                pass
            return False, f"Validation failed: {err_msg[:200]}"
    except Exception as e:
        return False, "Network error during key validation. Check connectivity and try again."


def start_adk_server():
    """Start the ADK web server as a subprocess."""
    global adk_process
    if adk_process and adk_process.poll() is None:
        adk_process.terminate()
        try:
            adk_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adk_process.kill()
            adk_process.wait(timeout=5)

    venv_adk = os.path.join(PROJECT_DIR, "venv", "bin", "adk")

    if os.path.exists(venv_adk):
        cmd = [venv_adk, "web", "--host", HOST, "--port", str(ADK_PORT), "adk_agents"]
        cwd = PROJECT_DIR
    else:
        cmd = ["adk", "web", "--host", HOST, "--port", str(ADK_PORT), "adk_agents"]
        cwd = PROJECT_DIR

    env = os.environ.copy()
    env_info = read_env()
    if env_info["GEMINI_API_KEY"]:
        env["GEMINI_API_KEY"] = env_info["GEMINI_API_KEY"]
        env["GOOGLE_API_KEY"] = env_info["GEMINI_API_KEY"]
    env["MODEL_NAME"] = env_info["MODEL_NAME"]
    env["GITHUB_TOKEN"] = env_info["GITHUB_TOKEN"]
    for ck, cv in env_info["custom_keys"].items():
        env[ck] = cv

    adk_process = subprocess.Popen(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"✅ ADK server starting on port {ADK_PORT}...")


LAUNCHER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Hiring Agent - API Setup & Configuration</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #090a16;
            color: #e2e8f0;
            padding: 20px;
        }

        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 60%);
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
            max-width: 560px;
            padding: 10px;
        }

        .card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 20px;
            padding: 36px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5),
                        0 0 80px rgba(99, 102, 241, 0.08);
            animation: cardEntry 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes cardEntry {
            from { opacity: 0; transform: translateY(30px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
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
            color: #94a3b8;
            margin-bottom: 24px;
            line-height: 1.5;
        }

        .env-badge {
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 20px;
        }

        .env-badge-active {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .env-badge-missing {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: flex;
            align-items: center;
            justify-content: space-between;
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

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        input, select {
            width: 100%;
            padding: 12px 16px;
            padding-right: 44px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 10px;
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            outline: none;
            transition: all 0.25s ease;
        }

        select {
            padding-right: 16px;
            cursor: pointer;
        }

        input:focus, select:focus {
            border-color: rgba(99, 102, 241, 0.7);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
            background: rgba(30, 41, 59, 0.85);
        }

        input::placeholder {
            color: #64748b;
        }

        .toggle-visibility {
            position: absolute;
            right: 12px;
            background: none;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            font-size: 16px;
            padding: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s ease;
        }

        .toggle-visibility:hover {
            color: #c7d2fe;
        }

        .test-key-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 6px;
        }

        .btn-test {
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #c7d2fe;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-test:hover {
            background: rgba(99, 102, 241, 0.3);
            color: #fff;
        }

        .key-status {
            font-size: 11px;
            font-weight: 500;
        }

        .key-status-valid { color: #34d399; }
        .key-status-invalid { color: #f87171; }
        .key-status-testing { color: #818cf8; }

        .input-hint {
            font-size: 11px;
            color: #64748b;
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
            margin-top: 12px;
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
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.45);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(99, 102, 241, 0.2);
            color: #c7d2fe;
            padding: 8px 12px;
            font-size: 12px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 8px;
            width: auto;

        }

        .btn-secondary:hover {
            background: rgba(99, 102, 241, 0.2);
        }

        .custom-keys-container {
            margin-top: 12px;
            border-top: 1px dashed rgba(99, 102, 241, 0.2);
            padding-top: 16px;
        }

        .custom-key-row {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
            align-items: center;
        }

        .custom-key-row input {
            padding-right: 12px;
        }

        .custom-key-row input.key-name {
            width: 40%;
        }

        .custom-key-row input.key-value {
            width: 50%;
        }

        .btn-remove-row {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            border-radius: 8px;
            padding: 10px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .btn-remove-row:hover {
            background: rgba(239, 68, 68, 0.3);
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
            width: 14px;
            height: 14px;
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
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.25), transparent);
            margin: 20px 0;
        }

        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 11px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div class="logo">
                    <div class="logo-icon">🤖</div>
                    <h1>AI Hiring Agent</h1>
                </div>
            </div>
            <p class="subtitle">
                Configure & test your API keys to launch the multi-agent hiring evaluation system.
            </p>

            <div id="envStatusBadge">__ENV_BADGE__</div>

            <form id="configForm">
                <div class="form-group">
                    <label for="geminiKey">
                        <span>Gemini API Key</span>
                        <span class="badge badge-required">Required</span>
                    </label>
                    <div class="input-wrapper">
                        <input type="password" id="geminiKey" placeholder="Enter API key (leave blank to keep configured key)"
                               autocomplete="new-password">
                        <button type="button" class="toggle-visibility" onclick="togglePass('geminiKey', this)">👁️</button>
                    </div>
                    <div class="test-key-row">
                        <p class="input-hint">
                            Get your key at <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a>
                        </p>
                        <button type="button" class="btn-test" onclick="testGeminiKey()">🧪 Test Key</button>
                    </div>
                    <div id="keyStatus" class="key-status" style="margin-top:4px;"></div>
                </div>

                <div class="form-group">
                    <label for="modelName">
                        <span>Model</span>
                        <span class="badge badge-optional">Optional</span>
                    </label>
                    <select id="modelName">
                        <option value="gemini-3.5-flash" __SEL_35F__>Gemini 3.5 Flash</option>
                        <option value="gemini-2.5-flash" __SEL_25F__>Gemini 2.5 Flash</option>
                        <option value="gemini-2.5-pro" __SEL_25P__>Gemini 2.5 Pro</option>
                    </select>
                </div>

                <div class="divider"></div>

                <div class="form-group">
                    <label for="githubToken">
                        <span>GitHub Token</span>
                        <span class="badge badge-optional">Optional</span>
                    </label>
                    <div class="input-wrapper">
                        <input type="password" id="githubToken" placeholder="Enter token (leave blank to keep configured token)"
                               autocomplete="new-password">
                        <button type="button" class="toggle-visibility" onclick="togglePass('githubToken', this)">👁️</button>
                    </div>
                    <p class="input-hint">
                        For higher GitHub API rate limits during candidate profile checks.
                        <a href="https://github.com/settings/tokens" target="_blank">Generate token</a>
                    </p>
                </div>

                <div class="custom-keys-container">
                    <label>
                        <span>Additional / Custom API Keys</span>
                        <span class="badge badge-optional">Optional</span>
                    </label>
                    <p class="input-hint" style="margin-bottom: 10px;">
                        Add any extra environment variables or API keys (e.g., OPENAI_API_KEY, SERPER_API_KEY).
                    </p>
                    <div id="customKeysList">
                        __CUSTOM_KEYS_HTML__
                    </div>
                    <button type="button" class="btn-secondary" onclick="addCustomKeyRow()">+ Add Custom API Key</button>
                </div>

                <button type="submit" class="btn btn-primary" id="submitBtn">
                    🚀 Save & Launch Hiring Agent
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
        const keyStatusEl = document.getElementById('keyStatus');

        function togglePass(inputId, btn) {
            const input = document.getElementById(inputId);
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🔒';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        }

        async function testGeminiKey() {
            const geminiKey = document.getElementById('geminiKey').value.trim();
            if (!geminiKey) {
                keyStatusEl.className = 'key-status key-status-invalid';
                keyStatusEl.textContent = '⚠️ Please enter a Gemini API key first.';
                return;
            }

            keyStatusEl.className = 'key-status key-status-testing';
            keyStatusEl.innerHTML = '<span class="spinner"></span> Testing key with Google API...';

            try {
                const response = await fetch('/validate-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: geminiKey })
                });
                const data = await response.json();

                if (data.success) {
                    keyStatusEl.className = 'key-status key-status-valid';
                    keyStatusEl.textContent = '✅ ' + data.message;
                } else {
                    keyStatusEl.className = 'key-status key-status-invalid';
                    keyStatusEl.textContent = '❌ ' + data.message;
                }
            } catch (err) {
                keyStatusEl.className = 'key-status key-status-invalid';
                keyStatusEl.textContent = '❌ Test failed: ' + err.message;
            }
        }

        function addCustomKeyRow(keyName = '', keyValue = '') {
            const container = document.getElementById('customKeysList');
            const row = document.createElement('div');
            row.className = 'custom-key-row';
            const name = document.createElement('input');
            name.type = 'text'; name.className = 'key-name'; name.placeholder = 'KEY_NAME';
            name.value = keyName;
            const value = document.createElement('input');
            value.type = 'password'; value.className = 'key-value';
            value.placeholder = keyValue ? 'Configured (leave blank to keep)' : 'API Key / Value';
            const remove = document.createElement('button');
            remove.type = 'button'; remove.className = 'btn-remove-row';
            remove.title = 'Remove key'; remove.textContent = '✕';
            remove.addEventListener('click', () => row.remove());
            row.append(name, value, remove);
            container.appendChild(row);
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const geminiKey = document.getElementById('geminiKey').value.trim();
            const githubToken = document.getElementById('githubToken').value.trim();
            const modelName = document.getElementById('modelName').value;

            const customKeys = {};
            const keyRows = document.querySelectorAll('.custom-key-row');
            keyRows.forEach(row => {
                const name = row.querySelector('.key-name').value.trim();
                const val = row.querySelector('.key-value').value.trim();
                if (name && val) {
                    customKeys[name] = val;
                }
            });

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Saving & Starting...';
            showStatus('loading', '⏳ Saving configuration and launching the agent server...');

            try {
                const response = await fetch('/save-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        gemini_key: geminiKey,
                        github_token: githubToken,
                        model_name: modelName,
                        custom_keys: customKeys
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showStatus('success', '✅ Configuration saved successfully! Launching agent UI...');
                    setTimeout(() => {
                        window.location.href = 'http://' + window.location.hostname + ':__ADK_PORT__';
                    }, 2000);
                } else {
                    showStatus('error', '❌ Error saving config: ' + (data.error || 'Unknown error'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '🚀 Save & Launch Hiring Agent';
                }
            } catch (err) {
                showStatus('error', '❌ Connection failed: ' + err.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 Save & Launch Hiring Agent';
            }
        });

        function showStatus(type, message) {
            statusEl.className = 'status status-' + type;
            statusEl.textContent = message;
        }
    </script>
</body>
</html>"""


def render_setup_page():
    """Render the setup page without embedding any stored secret values."""
    env = read_env()
    page = LAUNCHER_HTML
    model = env.get("MODEL_NAME", "gemini-3.5-flash")
    env_badge = (
        '<div class="env-badge env-badge-active">● Active Configuration Loaded</div>'
        if env.get("GEMINI_API_KEY")
        else '<div class="env-badge env-badge-missing">⚠️ No API Key Configured Yet</div>'
    )
    page = page.replace("__ENV_BADGE__", env_badge).replace("__ADK_PORT__", str(ADK_PORT))
    choices = ("gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-pro")
    if model not in choices:
        model = choices[0]
    for placeholder, choice in zip(("__SEL_35F__", "__SEL_25F__", "__SEL_25P__"), choices):
        page = page.replace(placeholder, "selected" if model == choice else "")
    rows = []
    for key in env.get("custom_keys", {}):
        escaped_key = html_module.escape(key, quote=True)
        rows.append(
            '<div class="custom-key-row">'
            f'<input type="text" class="key-name" placeholder="KEY_NAME" value="{escaped_key}">'
            '<input type="password" class="key-value" placeholder="Configured (leave blank to keep)" value="">'
            '<button type="button" class="btn-remove-row" onclick="this.parentElement.remove()" title="Remove key">✕</button></div>'
        )
    return page.replace("__CUSTOM_KEYS_HTML__", "".join(rows))


class LauncherHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        if self.path in ("/health", "/healthz"):
            self._json_response({"status": "ok", "service": "adk-hiring-agent"})
            return

        if self.path == "/" or self.path.startswith("/?"):
            page = render_setup_page()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(page.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        origin = urllib.parse.urlparse(self.headers.get("Origin", ""))
        if origin.scheme != "http" or origin.hostname not in {"localhost", "127.0.0.1", "::1"}:
            self._json_response({"success": False, "error": "Local browser origin required."}, 403)
            return
        if self.headers.get_content_type() != "application/json":
            self._json_response({"success": False, "error": "Send a JSON request body."}, 415)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0 or content_length > 65536:
                self._json_response({"success": False, "error": "Request body is too large."}, 413)
                return
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("JSON body must be an object")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._json_response({"success": False, "error": "Invalid JSON request."}, 400)
            return

        if self.path == "/validate-key":
            try:
                api_key = data.get("api_key", "").strip()
                valid, msg = validate_gemini_key(api_key)
                self._json_response({"success": valid, "message": msg})
            except Exception:
                self._json_response({"success": False, "message": "Validation could not be completed."}, 400)

        elif self.path == "/save-config":
            try:
                existing = read_env()
                gemini_key = data.get("gemini_key", "").strip() or existing["GEMINI_API_KEY"]
                github_token = data.get("github_token", "").strip() or existing["GITHUB_TOKEN"]
                model_name = data.get("model_name", "gemini-3.5-flash").strip()
                custom_keys = data.get("custom_keys", {})
                if not isinstance(custom_keys, dict):
                    raise ValueError("Custom keys must be an object")
                custom_keys = {**existing["custom_keys"], **custom_keys}

                if not gemini_key:
                    self._json_response({"success": False, "error": "Gemini API key is required"})
                    return

                write_env(gemini_key, github_token, model_name, custom_keys)

                # Start ADK server in background
                threading.Thread(target=start_adk_server, daemon=True).start()

                self._json_response({"success": True, "message": "Configuration saved"})

            except Exception:
                self._json_response({"success": False, "error": "Configuration could not be saved."}, 400)
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def cleanup(signum, frame):
    global adk_process
    print("\n🛑 Shutting down...")
    if adk_process and adk_process.poll() is None:
        adk_process.terminate()
        try:
            adk_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adk_process.kill()
            adk_process.wait(timeout=5)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║             🤖 AI Hiring Agent - Setup Launcher          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  🔑 API Setup Page: http://localhost:{PORT}                 ║
║  🤖 Agent Web UI:   http://localhost:{ADK_PORT} (after setup)    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

    server = http.server.ThreadingHTTPServer((HOST, PORT), LauncherHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cleanup(None, None)
