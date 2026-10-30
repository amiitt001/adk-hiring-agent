# 🌐 Deploying ADK Hiring Agent to Render.com

This guide provides step-by-step instructions to deploy the **AI-Powered Conversational Hiring Agent** on [Render.com](https://render.com).

---

## 🌐 Live Service Information

- **Live Service URL:** `https://adk-hiring-agent.onrender.com`
- **Health Check Endpoint:** `https://adk-hiring-agent.onrender.com/health`

---

## ⚡ Option 1: Render Blueprint (1-Click Deployment - Recommended)

Render supports Infrastructure-as-Code using the [`render.yaml`](file:///home/orion/Downloads/adk-hiring-agent-main/adk-hiring-agent-main/render.yaml) file included in this repository.

1. **Push your code** to a GitHub or GitLab repository.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Blueprint**.
3. Connect your Git repository.
4. Render will automatically detect `render.yaml` and configure the service.
5. In the Environment Variables section, enter your `GEMINI_API_KEY` (and optional `GITHUB_TOKEN`).
6. Click **Apply**. Render will build and deploy your application automatically!

---

## 🛠️ Option 2: Manual Render Web Service Setup

If you prefer to configure the Web Service manually on Render:

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Select your repository.
3. Configure the following settings:
   - **Name:** `adk-hiring-agent`
   - **Environment:** `Python 3`
   - **Region:** Any (e.g. Oregon, Frankfurt)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `./start.sh`
4. Add **Environment Variables**:
   - `GEMINI_API_KEY` = `your_gemini_api_key_here` (Required)
   - `MODEL_NAME` = `gemini-3.5-flash` (Optional, defaults to `gemini-3.5-flash`)
   - `GITHUB_TOKEN` = `your_github_token_here` (Optional, for higher API rate limits)
5. Click **Create Web Service**.

---

## 🐳 Option 3: Deploying as a Docker Web Service on Render

Render also supports native Docker deployments:

1. Click **New +** -> **Web Service**.
2. Select your repository.
3. Choose **Docker** as the Runtime environment. Render will detect the included [`Dockerfile`](file:///home/orion/Downloads/adk-hiring-agent-main/adk-hiring-agent-main/Dockerfile).
4. Set `GEMINI_API_KEY` in Environment Variables.
5. Click **Create Web Service**.

---

## 🔑 How API Keys are Handled on Cloud Deployments

- **Automatic Web Mode**: When `GEMINI_API_KEY` is provided in Render's Environment Variables, `start.sh` automatically launches the **ADK Web UI** directly on `http://0.0.0.0:$PORT`.
- **Setup Launcher Mode**: If `GEMINI_API_KEY` is not provided in environment variables, `start.sh` falls back to `launcher.py` on `$PORT`, allowing users to enter and test their API key via the web browser.
