from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registra los modelos en la base)
from app.database import Base, engine
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API de Gastos Personales", lifespan=lifespan)
app.include_router(auth.router)


@app.get("/")
def raiz():
    return {"mensaje": "API de gastos funcionando"}