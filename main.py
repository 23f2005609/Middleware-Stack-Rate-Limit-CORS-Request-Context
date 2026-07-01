import time
import uuid
from collections import defaultdict
from fastapi import FastAPI, Request, Response, status

app = FastAPI()

# Configuration
ALLOWED_ORIGINS = ["https://app-tufp93.example.com", "http://localhost:3000"]
RATE_LIMIT_BUCKET = 10
RATE_LIMIT_WINDOW = 10  # seconds

# State
rate_limit_store = defaultdict(lambda: {"count": 0, "window_start": time.time()})

@app.middleware("http")
async def main_middleware(request: Request, call_next):
    # --- 1. Rate Limiting Logic ---
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()
    data = rate_limit_store[client_id]

    if now - data["window_start"] > RATE_LIMIT_WINDOW:
        data["count"] = 1
        data["window_start"] = now
    else:
        if data["count"] >= RATE_LIMIT_BUCKET:
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content="Rate limit exceeded")
        data["count"] += 1

    # --- 2. Request Context Logic ---
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # --- 3. CORS & Response Headers ---
    # Inject Request ID
    response.headers["X-Request-ID"] = request_id
    
    # Strict CORS Logic
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "X-Request-ID, X-Client-Id, Content-Type"

    return response

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "your-email@example.com", 
        "request_id": request.state.request_id
    }

import os
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)