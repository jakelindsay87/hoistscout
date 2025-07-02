from typing import Optional
from sqlalchemy import String, Boolean, LargeBinary, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from .base import Base, TimestampMixin


class AuthType(str, enum.Enum):
    NONE = "none"
    BASIC = "basic"
    OAUTH = "oauth"
    FORM = "form"


class Website(Base, TimestampMixin):
    __tablename__ = "websites"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    credentials: Mapped[Optional[bytes]] = mapped_column(LargeBinary)  # Encrypted JSON
    auth_type: Mapped[AuthType] = mapped_column(
        Enum(AuthType, name="auth_type"),
        default=AuthType.NONE,
        nullable=False
    )
    scraping_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    opportunities: Mapped[list["Opportunity"]] = relationship(
        back_populates="website",
        cascade="all, delete-orphan"
    )
    scraping_jobs: Mapped[list["ScrapingJob"]] = relationship(
        back_populates="website",
        cascade="all, delete-orphan"
    )