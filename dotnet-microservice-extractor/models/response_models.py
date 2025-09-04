from pydantic import BaseModel
from typing import Literal,Any, Dict


class ResponseModel(BaseModel):
    status: str
    data: Dict[str, Any]