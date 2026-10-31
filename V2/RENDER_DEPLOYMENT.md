# 🌐 Deploying ADK Hiring Agent to Render.com

This guide provides step-by-step instructions to deploy the **AI-Powered Conversational Hiring Agent** on [Render.com](https://render.com).

---

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
   - `GITHUB_TOKEN` = `your_github_token_here` (Optional; enables the public GraphQL contribution breakdown and raises REST rate limits)
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
- Configure `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in Render before deploy. Startup now fails closed if neither is present; the local setup launcher is not exposed publicly.
- The prior fallback started the setup launcher on Render's routed port and later started ADK on a second port. Render does not route that second port, so the browser redirect could not reliably reach the agent.
- Render routes the configured web service port, which `start.sh` reads from `$PORT`, and the service binds to `0.0.0.0`. Do not assume a health endpoint exists on ADK Web; this Blueprint uses Render's default port check.
- The ADK Web UI currently has no application-level authentication in this repository. A public deployment can expose candidate data and agent execution to unauthenticated visitors; use only in a trusted/private environment until access controls are added.
