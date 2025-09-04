from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router
import time
from utils import logger
from dotenv import load_dotenv
import nest_asyncio

nest_asyncio.apply()

load_dotenv()

app = FastAPI(
    title="Dot net Microservice Extractor",
    version="v1",
    description="A service to analyze and convert .NET applications into microservices",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],  # Explicitly allow Authorization header for JWT
    allow_credentials=True,
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} {response.status_code} {duration:.2f}s"
    )
    return response

# Include the migration routes (includes /register and /login)
app.include_router(api_router, prefix="/api/v1")