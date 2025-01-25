from fastapi import FastAPI
from routes.map import router as map_router

app = FastAPI()

app.include_router(map_router, prefix="/api")

if __name__ == "__main__"