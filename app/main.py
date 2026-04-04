from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings


app = FastAPI(title=settings.APP_NAME)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # или ["*"] для полного разрешения (не советую для прод)
    allow_credentials=True,         # нужно если используешь cookies/authorization
    allow_methods=["*"],            # GET/POST/PATCH/DELETE...
    allow_headers=["*"],            # Authorization, Content-Type и т.п.
)

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
