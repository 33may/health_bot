import os
import sys

from fastapi import FastAPI
from routers.chat_router import router as chat_router

app = FastAPI()

app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    uvicorn.run("service:app", host="0.0.0.0", port=8000, reload=True)