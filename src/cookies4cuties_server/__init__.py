from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from cookies4cuties_server.config import get_settings
from cookies4cuties_server.routes import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the Supabase client when the API starts."""
    supabase_key = (
        settings.supabase_key
        or settings.supabase_service_role_key
    )

    if not settings.supabase_url or not supabase_key:
        raise RuntimeError(
            "Supabase is not configured. "
            "Set SUPABASE_URL and SUPABASE_KEY in your .env file."
        )

    app.state.supabase = create_client(
        settings.supabase_url,
        supabase_key,
    )

    yield

    # The Supabase client is shared by the application's routes.


app = FastAPI(
    title="Cookies4Cuties API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)