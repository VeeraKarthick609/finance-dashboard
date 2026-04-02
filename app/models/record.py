from typing import Optional

from pydantic import BaseModel, Field
import datetime


# --- Request schemas ---

class CreateRecordRequest(BaseModel):
    amount: float = Field(gt=0)
    type: str = Field(pattern=r"^(income|expense)$")
    category: str = Field(min_length=1, max_length=50)
    date: datetime.date
    notes: Optional[str] = Field(None, max_length=500)


class UpdateRecordRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[str] = Field(None, pattern=r"^(income|expense)$")
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    date: Optional[datetime.date] = None
    notes: Optional[str] = Field(None, max_length=500)


# --- Response schemas ---

class RecordResponse(BaseModel):
    id: str
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str]
    user_id: str
    created_at: str
    updated_at: str
