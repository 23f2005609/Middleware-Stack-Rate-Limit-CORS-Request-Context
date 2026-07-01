import time
import uuid
import os
from collections import defaultdict
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. CORS Configuration (Use built-in middleware for preflight)
# ADD the origin of the exam page here as well
ALLOWED_ORIGINS = [
    "https://app-tufp93.example.com", 
    "http://localhost:3000",
    "https://exam-page-origin.com" # <--- ADD THE GRADER'S URL HERE IF KNOWN
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting and Context Middleware
rate_limit_store = defaultdict(lambda: {"count": 0, "window_start": time.time()})
RATE_LIMIT_BUCKET = 10
RATE_LIMIT_WINDOW = 10

@app.middleware("http")
async def context_and_rate_limit(request: Request, call_next):
    # Rate Limiting
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

    # Request Context
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Inject ID
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/ping")
async def ping(request: Request):
    return {"email": "your-email@example.com", "request_id": request.state.request_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)
