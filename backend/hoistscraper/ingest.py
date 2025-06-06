import csv
import io
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from typing import List

from . import db, models

router = APIRouter(
    prefix="/api/ingest",
    tags=["ingest"],
)

logger = logging.getLogger(__name__)

@router.post("/sites/csv", response_model=List[models.SiteRead])
def ingest_sites_from_csv(
    file: UploadFile = File(...),
    session: Session = Depends(db.get_session),
):
    """
    Ingests sites from a CSV file.

    The CSV file should have the following columns:
    - Level
    - Jurisdiction/Body
    - Type
    - URL
    - ... and other optional columns
    """
    try:
        contents = file.file.read()
        buffer = io.StringIO(contents.decode("utf-8"))
        csv_reader = csv.DictReader(buffer)

        sites_to_create = []
        for row in csv_reader:
            name = row.get("Jurisdiction/Body")
            url = row.get("URL")

            if not name or not url:
                continue

            # Skip if a site with the same URL already exists
            existing_site = session.exec(select(models.Site).where(models.Site.url == url)).first()
            if existing_site:
                continue

            description_parts = []
            if row.get("Level"):
                description_parts.append(f"Level: {row.get('Level')}")
            if row.get("Type"):
                description_parts.append(f"Type: {row.get('Type')}")
            if row.get("Notes for Local/Specific Access"):
                description_parts.append(f"Notes: {row.get('Notes for Local/Specific Access')}")
            
            description = ". ".join(description_parts)

            site_create = models.SiteCreate(
                name=name,
                url=url,
                description=description,
                active=True,
            )
            sites_to_create.append(site_create)

        if not sites_to_create:
            raise HTTPException(
                status_code=400,
                detail="No new sites to create from the provided CSV. "
                       "Check if the required columns (Jurisdiction/Body, URL) are present "
                       "or if the sites already exist in the database.",
            )

        db_sites = []
        for site_create in sites_to_create:
            db_site = models.Site.model_validate(site_create)
            session.add(db_site)
            db_sites.append(db_site)

        session.commit()
        for db_site in db_sites:
            session.refresh(db_site)

        return db_sites

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if 'buffer' in locals() and not buffer.closed:
            buffer.close()
        if 'file' in locals() and not file.file.closed:
            file.file.close() 