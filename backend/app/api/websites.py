from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User, UserRole
from ..models.website import Website
from ..schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse
from ..utils.crypto import SecureCredentialManager
from .auth import get_current_user

router = APIRouter()
credential_manager = SecureCredentialManager()


def require_editor_role(current_user: User) -> User:
    if current_user.role not in [UserRole.EDITOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user


@router.get("/", response_model=List[WebsiteResponse])
async def list_websites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    stmt = select(Website).offset(skip).limit(limit)
    result = await db.execute(stmt)
    websites = result.scalars().all()
    return websites


@router.post("/", response_model=WebsiteResponse)
async def create_website(
    website_data: WebsiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(require_editor_role)]
):
    # Check if URL already exists
    stmt = select(Website).where(Website.url == str(website_data.url))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Website URL already exists"
        )
    
    # Encrypt credentials if provided
    encrypted_credentials = None
    if website_data.credentials:
        encrypted_credentials = credential_manager.encrypt_credentials(
            website_data.credentials
        )
    
    # Create website
    website = Website(
        name=website_data.name,
        url=str(website_data.url),
        category=website_data.category,
        auth_type=website_data.auth_type,
        credentials=encrypted_credentials,
        scraping_config=website_data.scraping_config,
        is_active=website_data.is_active
    )
    
    db.add(website)
    await db.commit()
    await db.refresh(website)
    
    return website


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Website).where(Website.id == website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    return website


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: int,
    website_data: WebsiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(require_editor_role)]
):
    stmt = select(Website).where(Website.id == website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Update fields
    update_data = website_data.model_dump(exclude_unset=True)
    
    # Handle credentials update
    if "credentials" in update_data and update_data["credentials"]:
        update_data["credentials"] = credential_manager.encrypt_credentials(
            update_data["credentials"]
        )
    
    for field, value in update_data.items():
        setattr(website, field, value)
    
    await db.commit()
    await db.refresh(website)
    
    return website


@router.delete("/{website_id}")
async def delete_website(
    website_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(require_editor_role)]
):
    stmt = select(Website).where(Website.id == website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    await db.delete(website)
    await db.commit()
    
    return {"detail": "Website deleted successfully"}


@router.post("/{website_id}/test")
async def test_website_scraping(
    website_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(require_editor_role)]
):
    stmt = select(Website).where(Website.id == website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # TODO: Trigger test scraping job
    return {"detail": "Test scraping job created", "job_id": "test-123"}