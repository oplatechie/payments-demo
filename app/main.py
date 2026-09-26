"""FastAPI app for the payments demo."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import admin, admin_auth, payments, refunds
from app.db import init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="payments-demo", lifespan=lifespan)
    app.include_router(payments.router)
    app.include_router(refunds.router)
    app.include_router(admin_auth.router)
    app.include_router(admin.router)
    return app


app = create_app()
