from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, UTC

class SiteBase(SQLModel):
    url: str = Field(index=True)
    name: str
    description: Optional[str] = None
    active: bool = True

class Site(SiteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class SiteCreate(SiteBase):
    pass

class SiteRead(SiteBase):
    id: int
    created_at: datetime
    updated_at: datetime 