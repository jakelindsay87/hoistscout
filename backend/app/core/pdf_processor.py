"""
PDF processing pipeline for tender documents.
"""

import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
import hashlib
from datetime import datetime
from loguru import logger

from unstructured.partition.auto import partition
from unstructured.staging.base import elements_to_json
from minio import Minio
from minio.error import S3Error
import httpx

from ..schemas.document import ProcessedDocument, DocumentMetadata


class PDFProcessor:
    """
    Processes PDF documents with intelligent extraction.
    
    Features:
    - Parallel processing with Celery
    - OCR for scanned documents
    - Table extraction
    - LLM-powered content analysis
    - MinIO storage integration
    """
    
    def __init__(self):
        self.minio_client = self._init_minio()
        self.bucket_name = "tender-documents"
        self._ensure_bucket()
        
    def _init_minio(self) -> Minio:
        """Initialize MinIO client."""
        import os
        
        return Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False  # Set to True in production with HTTPS
        )
    
    def _ensure_bucket(self):
        """Ensure the storage bucket exists."""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
    
    async def process_batch(
        self, 
        pdf_urls: List[str]
    ) -> Dict[str, ProcessedDocument]:
        """
        Process multiple PDFs in parallel.
        
        Args:
            pdf_urls: List of PDF URLs to process
            
        Returns:
            Dict mapping URL to processed document data
        """
        tasks = [self.process_pdf(url) for url in pdf_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = {}
        for url, result in zip(pdf_urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process {url}: {result}")
            else:
                processed[url] = result
                
        return processed
    
    async def process_pdf(self, pdf_url: str) -> ProcessedDocument:
        """
        Process a single PDF document.
        
        Steps:
        1. Download PDF
        2. Store in MinIO
        3. Extract text and structure
        4. Analyze with LLM if needed
        5. Return processed data
        """
        try:
            # Download PDF
            pdf_content = await self._download_pdf(pdf_url)
            
            # Generate unique object key
            url_hash = hashlib.md5(pdf_url.encode()).hexdigest()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            object_key = f"pdfs/{timestamp}_{url_hash}.pdf"
            
            # Store in MinIO
            await self._store_pdf(object_key, pdf_content)
            
            # Extract content
            extracted_data = await self._extract_content(pdf_content)
            
            # Create metadata
            metadata = DocumentMetadata(
                filename=self._extract_filename(pdf_url),
                file_size=len(pdf_content),
                mime_type="application/pdf",
                pages=extracted_data.get("page_count", 0),
                has_images=extracted_data.get("has_images", False),
                has_tables=extracted_data.get("has_tables", False)
            )
            
            return ProcessedDocument(
                source_url=pdf_url,
                minio_object_key=object_key,
                extracted_text=extracted_data.get("text", ""),
                extracted_data=extracted_data,
                metadata=metadata,
                processing_status="completed",
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_url}: {e}")
            
            return ProcessedDocument(
                source_url=pdf_url,
                minio_object_key=None,
                extracted_text="",
                extracted_data={"error": str(e)},
                metadata=None,
                processing_status="failed",
                processed_at=datetime.utcnow()
            )
    
    async def _download_pdf(self, url: str) -> bytes:
        """Download PDF from URL."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    async def _store_pdf(self, object_key: str, content: bytes):
        """Store PDF in MinIO."""
        import io
        
        await asyncio.to_thread(
            self.minio_client.put_object,
            bucket_name=self.bucket_name,
            object_name=object_key,
            data=io.BytesIO(content),
            length=len(content),
            content_type="application/pdf"
        )
        
        logger.info(f"Stored PDF in MinIO: {object_key}")
    
    async def _extract_content(
        self, 
        pdf_content: bytes
    ) -> Dict[str, Any]:
        """
        Extract content from PDF using Unstructured.
        
        Returns:
            Dict with extracted text, tables, images, and metadata
        """
        import tempfile
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        
        try:
            # Use Unstructured to partition the PDF
            elements = await asyncio.to_thread(
                partition,
                filename=tmp_path,
                strategy="hi_res",  # High resolution for better OCR
                infer_table_structure=True,  # Extract tables
                include_page_breaks=True
            )
            
            # Extract different types of content
            text_content = []
            tables = []
            page_count = 1
            
            for element in elements:
                if element.category == "Table":
                    tables.append(element.metadata.text_as_html)
                elif element.category == "PageBreak":
                    page_count += 1
                else:
                    text_content.append(str(element))
            
            # Combine all text
            full_text = "\n".join(text_content)
            
            # Extract key information with LLM if needed
            key_info = await self._extract_key_information(full_text)
            
            return {
                "text": full_text,
                "tables": tables,
                "page_count": page_count,
                "has_tables": len(tables) > 0,
                "has_images": any(e.category == "Image" for e in elements),
                "key_information": key_info,
                "elements": elements_to_json(elements)
            }
            
        finally:
            # Clean up temp file
            Path(tmp_path).unlink()
    
    async def _extract_key_information(
        self, 
        text: str
    ) -> Dict[str, Any]:
        """
        Use LLM to extract key information from PDF text.
        
        This is useful for tender documents that contain:
        - Submission requirements
        - Evaluation criteria
        - Technical specifications
        - Important dates
        """
        if len(text) < 100:
            return {}
            
        # Truncate very long texts
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        try:
            # Use Ollama to extract key information
            import ollama
            
            prompt = f"""
            Extract key information from this tender document:
            
            {text}
            
            Extract:
            - Submission deadline
            - Required documents
            - Evaluation criteria
            - Contact information
            - Any special requirements
            
            Return as JSON.
            """
            
            response = await asyncio.to_thread(
                ollama.chat,
                model="llama3.1",
                messages=[{"role": "user", "content": prompt}],
                format="json"
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            return {}
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        from urllib.parse import urlparse, unquote
        
        path = urlparse(url).path
        filename = path.split('/')[-1]
        
        # Decode URL encoding
        filename = unquote(filename)
        
        # Fallback if no filename
        if not filename or not filename.endswith('.pdf'):
            filename = f"document_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf"
            
        return filename
    
    async def get_document(self, object_key: str) -> bytes:
        """Retrieve document from MinIO."""
        try:
            response = await asyncio.to_thread(
                self.minio_client.get_object,
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            return response.read()
        finally:
            response.close()
            response.release_conn()
    
    async def delete_document(self, object_key: str):
        """Delete document from MinIO."""
        await asyncio.to_thread(
            self.minio_client.remove_object,
            bucket_name=self.bucket_name,
            object_name=object_key
        )