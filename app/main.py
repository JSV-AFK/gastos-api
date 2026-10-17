from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registra los modelos en la base)
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API de Gastos Personales", lifespan=lifespan)


@app.get("/")
def raiz():
    return {"mensaje": "API de gastos funcionando"}