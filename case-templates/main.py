from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.db.database import Base, engine
from app.api import auth, cases, interrogation, solutions, leaderboard

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DetectiveOS API",
    description="AI-powered mystery solving platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# In development: CORS_ORIGINS in .env = http://localhost:3000,http://127.0.0.1:5500
# In production:  CORS_ORIGINS in Render/Railway = https://your-app.vercel.app
#
# The wildcard ["*"] below is a safety fallback — remove it in production
# once you have set CORS_ORIGINS correctly in your hosting environment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(interrogation.router)
app.include_router(solutions.router)
app.include_router(leaderboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "DetectiveOS API", "version": "1.0.0"}


@app.exception_handler(Exception)
async def generic_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
