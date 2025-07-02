from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Text, Float, BigInteger, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from .base import Base, TimestampMixin


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"
    __table_args__ = (
        # Use regular btree index for now, GIN requires special setup
        Index('idx_opportunities_title', 'title'),
        Index('idx_opportunities_deadline', 'deadline'),
        Index('idx_opportunities_value', 'value'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    reference_number: Mapped[Optional[str]] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    categories: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    website: Mapped["Website"] = relationship(back_populates="opportunities")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    
    # Relationships
    opportunity: Mapped["Opportunity"] = relationship(back_populates="documents")