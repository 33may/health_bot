from typing import Literal, Union

from pydantic import BaseModel

class TokenObject(BaseModel):
    type: Literal["message", "think", "done", "rag"]
    content: str