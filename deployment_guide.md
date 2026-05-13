# KairosMD: Deployment Guide

To deploy the KairosMD MCP server and connect it to the PromptOpinion agent (Gemini 3.1 Flash), follow these instructions.

## 1. Local Development & Testing
Before deploying to the cloud, verify the server runs locally in SSE mode.

```powershell
# Install dependencies
uv sync

# 1. Seed the FHIR server (Required to generate ward_manifest.json)
uv run python -m kairosmd.seed

# 2. Start the MCP server in SSE mode
uv run kairosmd --sse
```
The server will be available at `http://localhost:8000`. You can test the SSE endpoint at `http://localhost:8000/sse`.

## 2. Cloud Deployment (SSE Mode)
PromptOpinion requires a publicly accessible URL to communicate with the MCP server.

### Option A: Railway (Recommended)
1.  **Create a new project** on Railway and connect your GitHub repository.
2.  **Environment Variables**: Add all variables from your `.env` file to the Railway project settings.
3.  **Build Command**: Railway will detect the `pyproject.toml`.
4.  **Start Command**: `uv run kairosmd --sse`
5.  **Networking**: Ensure the service is exposed on port `8000`.

### Option B: Docker
You can containerize the application for any cloud provider (DigitalOcean, AWS, etc.).

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app
COPY . .

# Synchronize dependencies and build the manifest
RUN uv sync
RUN uv run python -m kairosmd.seed

EXPOSE 8000
CMD ["uv", "run", "kairosmd", "--sse"]
```

## 3. Connecting to PromptOpinion
Once your server is live and reachable at a public URL (e.g., `https://kairos-mcp.up.railway.app`):

1.  Open the **PromptOpinion** developer console.
2.  Navigate to **MCP Integrations**.
3.  Add a new **SSE Connection**.
4.  Enter your deployment URL: `https://your-app-url.com/sse`.
5.  Select **Gemini 3.1 Flash** as the reasoning model.
6.  The agent will now have access to the 9 KairosMD tools.

## 4. Deploying the Dashboard (Optional)
The Next.js dashboard can be deployed separately to **Vercel**.

```bash
cd dashboard
npm install
# Set NEXT_PUBLIC_DASHBOARD_BASE_URL to your Vercel URL
npm run build
```
Ensure that the `DASHBOARD_BASE_URL` in your MCP server environment variables matches your Vercel deployment URL so the deep-links work correctly.
