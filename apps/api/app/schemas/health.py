from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class DependencyStatus(BaseModel):
    name: str
    ok: bool
    detail: str


class ReadinessResponse(HealthResponse):
    dependencies: list[DependencyStatus]

