from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

from application.backend.logic.inference.chat import interact_chat_model

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()

            context = [{"role": "user", "content": data}]

            for token in interact_chat_model(context, stream=True):
                await websocket.send_text(token)
                await asyncio.sleep(0)
    except WebSocketDisconnect:
        print("Клиент отключился")
