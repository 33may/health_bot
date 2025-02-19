import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from loguru import logger

from application.backend.logic.inference.chat import interact_model, chat

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

            async for token in chat(data_list):
                # await websocket.send_text(json.dumps({
                #     "type": token.type,
                #     "content": token.content
                # }))
                await websocket.send_text(token.content)
                await asyncio.sleep(0)

    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await websocket.close(code=1011)