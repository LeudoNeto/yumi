from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR, settings
from .database import init_db
from .routers import auth, company, customer, menu, orders, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    # wait for MySQL and create tables on startup
    init_db()
    yield


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve uploaded images (logos, item photos)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(company.router)
app.include_router(customer.router)
app.include_router(menu.router)
app.include_router(public.router)
app.include_router(orders.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
