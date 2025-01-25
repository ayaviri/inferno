from fastapi import FastAPI
from routes.map import router as map_router

app = FastAPI()

app.include_router(map_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


