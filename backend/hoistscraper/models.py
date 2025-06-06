from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SiteBase(SQLModel):
    url: str = Field(index=True)
    name: str
    description: Optional[str] = None
    active: bool = True

class Site(SiteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SiteCreate(SiteBase):
    pass

class SiteRead(SiteBase):
    id: int
    created_at: datetime
    updated_at: datetime 