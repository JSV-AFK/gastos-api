from fastapi import FastAPI

app = FastAPI(title="API de Gastos Personales")


@app.get("/")
def raiz():
    return {"mensaje": "API de gastos funcionando"}
