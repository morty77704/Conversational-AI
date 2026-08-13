from pydantic import BaseModel


class HealthResponse(BaseModel):    # 创造返回的对象
    status: str