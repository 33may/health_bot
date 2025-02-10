import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from loguru import logger

from application.backend.logic.inference.chat import interact_chat_model

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_str = await websocket.receive_text()
            logger.debug(f"Received message: {data_str}")

            data_list = json.loads(data_str)
            logger.debug(f"Received data: {data_list}")

            for token in interact_chat_model(data_list, stream=True):
                await websocket.send_text(token)
                await asyncio.sleep(0)
    except WebSocketDisconnect:
        logger.debug("Websocket disconnected")
