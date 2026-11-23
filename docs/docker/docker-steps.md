# 🐳 Docker Operations Guide for InsightFlow

This document provides complete, step-by-step instructions for building, running, testing, managing, and debugging the **InsightFlow** container locally using Docker.

---

## 📑 Table of Contents
- [1. Prerequisites](#1-prerequisites)
- [2. Building the Docker Image](#2-building-the-docker-image)
- [3. Running the Container Locally](#3-running-the-container-locally)
- [4. Testing & Verification](#4-testing--verification)
- [5. Managing Container Lifecycle](#5-managing-container-lifecycle)
- [6. Debugging & Troubleshooting](#6-debugging--troubleshooting)
- [7. Optional: Docker Compose](#7-optional-docker-compose)

---

## 1. Prerequisites

Before starting, ensure you have:
1. **Docker Desktop** installed and running on your machine:
   ```powershell
   docker --version
   ```
2. Your **`.env`** file configured in the project root.  
   *(If not present, copy from `.env.example` and supply your API keys).*

---

## 2. Building the Docker Image

### Basic Build
Run this command from the project root directory where the `Dockerfile` is located:

```powershell
docker build -t insightflow-image .
```

### Build with a Specific Version Tag
```powershell
docker build -t insightflow-image:v0.1.0 .
```

### Force Rebuild (Bypass Cache)
Use this if you updated `requirements.txt` or want a completely fresh build:
```powershell
docker build --no-cache -t insightflow-image .
```

### Inspect Created Images
Verify that the image is built and view its size:
```powershell
docker images
```

---

## 3. Running the Container Locally

### A. Run in Foreground (Interactive Mode with Live Logs)
Best for testing so you can see live server output and requests in your terminal:

```powershell
docker run -p 8000:8000 --env-file .env insightflow-image
```

> **Press `Ctrl + C`** to gracefully stop the container.

---

### B. Run in Background (Detached Mode)
Keeps your terminal free while the API runs in the background:

```powershell
docker run -d -p 8000:8000 --name insightflow-app --env-file .env insightflow-image
```

- `-d`: Runs container in the background (detached).
- `-p 8000:8000`: Forwards host port `8000` to container port `8000`.
- `--name insightflow-app`: Assigns a readable container name.
- `--env-file .env`: Injects your environment variables securely at runtime.

---

## 4. Testing & Verification

Once your container is running, test the endpoints:

### 1. Check Container Health Status
```powershell
docker ps
```
Look for `STATUS: Up ... (healthy)`.

### 2. View Live Container Logs
```powershell
docker logs -f insightflow-app
```

### 3. Verify Health Endpoints
- **Liveness Check:**
  ```powershell
  curl http://localhost:8000/health
  ```
  *Expected Response:* `{"status":"healthy","version":"0.1.0",...}`

- **Qdrant Readiness Check:**
  ```powershell
  curl http://localhost:8000/health/ready
  ```
  *Expected Response:* `{"status":"ready","qdrant_connected":true,...}`

### 4. Open Interactive Documentation
Open your browser and navigate to:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Send a Test Query via PowerShell
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -ContentType "application/json" -Body '{"question": "What is RAG?", "include_sources": false}'
```

---

## 5. Managing Container Lifecycle

| Action | Command |
| :--- | :--- |
| **View running containers** | `docker ps` |
| **View all containers (including stopped)** | `docker ps -a` |
| **View live logs** | `docker logs -f insightflow-app` |
| **Stop container** | `docker stop insightflow-app` |
| **Start stopped container** | `docker start insightflow-app` |
| **Restart container** | `docker restart insightflow-app` |
| **Remove container** | `docker rm -f insightflow-app` |
| **Remove image** | `docker rmi insightflow-image` |
| **Clean up unused containers & caches** | `docker system prune` |

---

## 6. Debugging & Troubleshooting

### Opening an Interactive Shell Inside the Container
To inspect container files, directories, or permissions:

```powershell
docker exec -it insightflow-app /bin/bash
```

### Common Errors & Solutions

#### Error: `Bind for 0.0.0.0:8000 failed: port is already allocated`
**Cause:** Another process (or a local `uvicorn`/`fastapi dev` instance) is using port 8000.  
**Solution:** Either stop the local process, or map to a different host port (e.g., `8080`):
```powershell
docker run -d -p 8080:8000 --name insightflow-app --env-file .env insightflow-image
```
*(Access API at `http://localhost:8080`)*

#### Error: Missing Environment Variables / API Keys
**Cause:** The `--env-file .env` flag was omitted.  
**Solution:** Always include `--env-file .env` when executing `docker run`.

---

## 7. Optional: Docker Compose

If you prefer using `docker compose`, you can create a `docker-compose.yml` file in your project root:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: insightflow-image:latest
    container_name: insightflow-app
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Then manage the container with single commands:
- **Start:** `docker compose up -d`
- **View Logs:** `docker compose logs -f`
- **Stop:** `docker compose down`
