"""API endpoints for website credential management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from loguru import logger

from hoistscraper import db
from hoistscraper.models import Website
from hoistscraper.models_credentials import (
    WebsiteCredential,
    WebsiteCredentialCreate,
    WebsiteCredentialRead
)
from hoistscraper.auth.credential_manager import credential_manager


router = APIRouter(prefix="/api/credentials", tags=["credentials"])


@router.post("/", response_model=WebsiteCredentialRead)
def create_credential(
    credential: WebsiteCredentialCreate,
    session: Session = Depends(db.get_session)
):
    """Store encrypted credentials for a website."""
    # Verify website exists
    website = session.get(Website, credential.website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website {credential.website_id} not found"
        )
    
    try:
        db_credential = credential_manager.store_credential(session, credential)
        
        # Return read model (without encrypted password)
        return WebsiteCredentialRead(
            id=db_credential.id,
            website_id=db_credential.website_id,
            username=db_credential.username,
            auth_type=db_credential.auth_type,
            additional_fields=db_credential.additional_fields,
            notes=db_credential.notes,
            created_at=db_credential.created_at,
            updated_at=db_credential.updated_at,
            last_used_at=db_credential.last_used_at,
            is_valid=db_credential.is_valid
        )
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store credentials"
        )


@router.get("/", response_model=List[WebsiteCredentialRead])
def list_credentials(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(db.get_session)
):
    """List all stored credentials (without passwords)."""
    credentials = session.exec(
        select(WebsiteCredential)
        .offset(skip)
        .limit(limit)
    ).all()
    
    return [
        WebsiteCredentialRead(
            id=cred.id,
            website_id=cred.website_id,
            username=cred.username,
            auth_type=cred.auth_type,
            additional_fields=cred.additional_fields,
            notes=cred.notes,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
            last_used_at=cred.last_used_at,
            is_valid=cred.is_valid
        )
        for cred in credentials
    ]


@router.get("/{website_id}", response_model=WebsiteCredentialRead)
def get_credential(
    website_id: int,
    session: Session = Depends(db.get_session)
):
    """Get credential info for a specific website."""
    credential = session.exec(
        select(WebsiteCredential).where(
            WebsiteCredential.website_id == website_id
        )
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for website {website_id}"
        )
    
    return WebsiteCredentialRead(
        id=credential.id,
        website_id=credential.website_id,
        username=credential.username,
        auth_type=credential.auth_type,
        additional_fields=credential.additional_fields,
        notes=credential.notes,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
        last_used_at=credential.last_used_at,
        is_valid=credential.is_valid
    )


@router.delete("/{website_id}")
def delete_credential(
    website_id: int,
    session: Session = Depends(db.get_session)
):
    """Delete credentials for a website."""
    credential = session.exec(
        select(WebsiteCredential).where(
            WebsiteCredential.website_id == website_id
        )
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for website {website_id}"
        )
    
    session.delete(credential)
    session.commit()
    
    return {"message": f"Credentials deleted for website {website_id}"}


@router.post("/{website_id}/validate")
def validate_credential(
    website_id: int,
    session: Session = Depends(db.get_session)
):
    """Test if stored credentials are valid by attempting to decrypt them."""
    result = credential_manager.get_credential(session, website_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No valid credentials found for website {website_id}"
        )
    
    username, _, _ = result
    return {
        "website_id": website_id,
        "username": username,
        "is_valid": True,
        "message": "Credentials successfully decrypted"
    }


@router.post("/{website_id}/mark-invalid")
def mark_credential_invalid(
    website_id: int,
    session: Session = Depends(db.get_session)
):
    """Mark credentials as invalid (e.g., after authentication failure)."""
    credential_manager.mark_invalid(session, website_id)
    
    return {
        "website_id": website_id,
        "message": "Credentials marked as invalid"
    }