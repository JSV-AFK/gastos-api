import os

# En producción SIEMPRE se define SECRET_KEY como variable de entorno.
SECRET_KEY = os.getenv("SECRET_KEY", "clave-solo-para-desarrollo-cambiar-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60