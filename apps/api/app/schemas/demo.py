from pydantic import BaseModel

from app.schemas.inference import InferenceRunResponse


class DemoSampleResponse(BaseModel):
    sample_id: str
    title: str
    description: str
    is_synthetic: bool
    cached: bool
    sample_filename: str
    sample_image_url: str
    reference_image_url: str | None = None
    result: InferenceRunResponse
    explanation: list[str]
    limitations: list[str]
