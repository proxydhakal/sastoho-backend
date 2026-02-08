from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_serializer

class ContactSubmissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1)
    submission_type: str = Field(default="feedback", pattern="^(feedback|grievance)$")

class ContactSubmissionOut(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    submission_type: str
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at')
    def serialize_created_at(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None
