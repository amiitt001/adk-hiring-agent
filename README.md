# AI-Powered Conversational Hiring Agent

Welcome to the **AI-Powered Conversational Hiring Agent System** built using Google's ADK (Agent Development Kit) and Gemini models!

> Made with ❤️ by Amit Verma

## Overview

This project provides a multi-agent system that automates technical candidate evaluation through a conversational interface. The system uses specialized AI agents to evaluate resumes, validate GitHub profiles, and provide comprehensive hiring recommendations.

### Features & System Components

- **5 Specialized AI Agents**: RubricBuilder, ResumeReviewer, GitHubValidator, GitHubReviewer, VerdictSynthesizer
- **1 Root Orchestrator**: Conversational coordinator that manages the evaluation workflow
- **Interactive Setup Launcher**: Web-based configuration manager to enter, test, and save API keys
- **Real-time API Integration**: Live GitHub account validation and Gemini LLM orchestration
- **Structured Evaluation Framework**: Objective, measurable criteria with scoring
- **End-to-End Workflow**: From job description to final HIRE/NO HIRE decision

### Technologies Used

- **Google ADK (Agent Development Kit)** - Agent framework
- **Gemini Models** - LLM for agent intelligence
- **Python 3.8+** - Programming language
- **GitHub REST API** - Account validation
- **python-dotenv** - Environment management
- **requests** - HTTP client library

---

## Getting Started & API Configuration

### Prerequisites

- Python 3.8+
- Gemini API Key (Get yours at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- GitHub Account / Personal Access Token (Optional, for higher rate limits)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/amiitt001/adk-hiring-agent.git
   cd adk-hiring-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**

   **Option A: Interactive Setup Launcher (Recommended)**
   Launch the web setup UI to enter, test, and save your API keys:
   ```bash
   python launcher.py
   # or
   ./run.sh launcher
   ```
   Open `http://localhost:8888` in your browser, enter your Gemini API key, use the **🧪 Test Key** button to verify it live, and click **🚀 Save & Launch Hiring Agent**.

   **Option B: Manual `.env` Setup**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   MODEL_NAME=gemini-3.5-flash
   GITHUB_TOKEN=your_github_token_here  # Optional
   ```

4. **Run the Hiring Agent:**
   - **Web UI Mode:**
     ```bash
     ./run.sh web
     ```
     Open `http://localhost:8080` to interact with the hiring agent.
   
   - **CLI Mode:**
     ```bash
     ./run.sh cli
     ```

---

## 🌐 Cloud Deployment (Render.com)

You can easily deploy this system on Render using 1-Click Blueprint or Manual setup:

- **Render Blueprint:** Connect your repository on Render and select `render.yaml`.
- **Start Command:** `./start.sh`
- **Environment Variables:** Set `GEMINI_API_KEY` in your Render dashboard.

See [`RENDER_DEPLOYMENT.md`](file:///home/orion/Downloads/adk-hiring-agent-main/adk-hiring-agent-main/RENDER_DEPLOYMENT.md) for full instructions.

---

**Good luck, and happy building!** 🚀
