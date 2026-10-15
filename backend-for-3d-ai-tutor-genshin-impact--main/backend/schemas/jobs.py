"""Background job status schema.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from backend.schemas.compat import BaseModel


class JobResponse(BaseModel):
    id: str
    owner_id: str
    job_type: str
    status: str
    progress: float
    resource_id: Optional[str] = None
    result: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
