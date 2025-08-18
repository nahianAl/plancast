"""
File Processing Service for PlanCast.

Handles input file validation and conversion for:
- JPG/PNG images
- Single-page PDF files

Converts all inputs to standardized image format for CubiCasa5K processing.
"""

import os
import magic
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path

from models.data_structures import FileFormat, ProcessingJob

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass


class FileProcessor:
    """
    Production-ready file processor for floor plan inputs.
    
    Handles validation, format detection, and conversion to standard image format.
    """
    
    # File size limits (bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MIN_FILE_SIZE = 1024  # 1KB
    
    # Image constraints
    MAX_IMAGE_DIMENSION = 4096  # pixels
    MIN_IMAGE_DIMENSION = 512   # pixels
    
    # Supported MIME types
    SUPPORTED_MIME_TYPES = {
        'image/jpeg': FileFormat.JPEG,
        'image/jpg': FileFormat.JPG,
        'image/png': FileFormat.PNG,
        'application/pdf': FileFormat.PDF
    }
    
    def __init__(self):
        """Initialize file processor."""
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
    def validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate uploaded file meets requirements.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Dict with validation results
            
        Raises:
            FileProcessingError: If file is invalid
        """
        logger.info(f"Validating file: {filename} ({len(file_content)} bytes)")
        
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise FileProcessingError(
                f"File too large: {len(file_content)} bytes. "
                f"Maximum allowed: {self.MAX_FILE_SIZE} bytes"
            )
            
        if len(file_content) < self.MIN_FILE_SIZE:
            raise FileProcessingError(
                f"File too small: {len(file_content)} bytes. "
                f"Minimum required: {self.MIN_FILE_SIZE} bytes"
            )
        
        # Detect file type using magic numbers (more reliable than extension)
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
        except Exception as e:
            raise FileProcessingError(f"Could not detect file type: {str(e)}")
            
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            supported_types = list(self.SUPPORTED_MIME_TYPES.keys())
            raise FileProcessingError(
                f"Unsupported file type: {mime_type}. "
                f"Supported types: {', '.join(supported_types)}"
            )
            
        file_format = self.SUPPORTED_MIME_TYPES[mime_type]
        
        # Additional validation based on file type
        if file_format == FileFormat.PDF:
            self._validate_pdf(file_content)
        else:
            self._validate_image(file_content)
            
        logger.info(f"File validation passed: {filename} ({file_format.value})")
        
        return {
            "filename": filename,
            "file_format": file_format,
            "file_size_bytes": len(file_content),
            "mime_type": mime_type,
            "is_valid": True
        }
    
    def _validate_pdf(self, file_content: bytes) -> None:
        """
        Validate PDF file requirements.
        
        Args:
            file_content: PDF file bytes
            
        Raises:
            FileProcessingError: If PDF is invalid
        """
        try:
            doc = fitz.open("pdf", file_content)
            
            # Check page count - must be single page
            page_count = len(doc)
            if page_count != 1:
                doc.close()
                raise FileProcessingError(
                    f"Multi-page PDFs not supported. Found {page_count} pages. "
                    f"Please save your floor plan as a single-page PDF."
                )
                
            # Check if page contains content
            page = doc.load_page(0)
            text_content = page.get_text().strip()
            image_list = page.get_images()
            
            if not text_content and not image_list:
                doc.close()
                raise FileProcessingError(
                    "PDF appears to be empty. No text or images found."
                )
                
            doc.close()
            logger.info("PDF validation passed: single page with content")
            
        except fitz.fitz.FileDataError as e:
            raise FileProcessingError(f"Invalid PDF file: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"PDF validation failed: {str(e)}")
    
    def _validate_image(self, file_content: bytes) -> None:
        """
        Validate image file requirements.
        
        Args:
            file_content: Image file bytes
            
        Raises:
            FileProcessingError: If image is invalid
        """
        try:
            with Image.open(BytesIO(file_content)) as img:
                width, height = img.size
                
                # Check dimensions
                if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
                    raise FileProcessingError(
                        f"Image too large: {width}x{height}. "
                        f"Maximum dimension: {self.MAX_IMAGE_DIMENSION}px"
                    )
                    
                if width < self.MIN_IMAGE_DIMENSION or height < self.MIN_IMAGE_DIMENSION:
                    logger.warning(
                        f"Small image detected: {width}x{height}. Will upscale to minimum dimension {self.MIN_IMAGE_DIMENSION}px during processing."
                    )
                
                # Check aspect ratio (floor plans are typically landscape)
                aspect_ratio = width / height
                if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                    logger.warning(
                        f"Unusual aspect ratio: {aspect_ratio:.2f}. "
                        f"Floor plans are typically landscape orientation."
                    )
                
                logger.info(f"Image validation passed: {width}x{height} ({img.mode})")
                
        except Exception as e:
            raise FileProcessingError(f"Invalid image file: {str(e)}")
    
    def process_file_to_image(self, file_content: bytes, file_format: FileFormat) -> Tuple[bytes, Tuple[int, int]]:
        """
        Convert input file to standardized image format for CubiCasa5K.
        
        Args:
            file_content: Raw file bytes
            file_format: Detected file format
            
        Returns:
            Tuple of (image_bytes, (width, height))
            
        Raises:
            FileProcessingError: If conversion fails
        """
        logger.info(f"Converting {file_format.value} to image format")
        
        try:
            if file_format in [FileFormat.JPG, FileFormat.JPEG, FileFormat.PNG]:
                return self._process_image(file_content)
            elif file_format == FileFormat.PDF:
                return self._process_pdf(file_content)
            else:
                raise FileProcessingError(f"Unsupported format for processing: {file_format}")
                
        except Exception as e:
            logger.error(f"File processing failed: {str(e)}")
            raise FileProcessingError(f"Could not process file: {str(e)}")
    
    def _process_image(self, file_content: bytes) -> Tuple[bytes, Tuple[int, int]]:
        """
        Process image files (JPG/PNG).
        
        Args:
            file_content: Image file bytes
            
        Returns:
            Tuple of (processed_image_bytes, dimensions)
        """
        with Image.open(BytesIO(file_content)) as img:
            # Convert to RGB if necessary (CubiCasa5K expects RGB)
            if img.mode != 'RGB':
                logger.info(f"Converting image from {img.mode} to RGB")
                img = img.convert('RGB')
            
            # Get dimensions
            width, height = img.size
            
            # Optionally upscale to ensure minimum dimension
            min_dim = min(width, height)
            if min_dim < self.MIN_IMAGE_DIMENSION:
                scale = self.MIN_IMAGE_DIMENSION / float(min_dim)
                new_w = int(round(width * scale))
                new_h = int(round(height * scale))
                # Avoid exceeding maximums
                if new_w > self.MAX_IMAGE_DIMENSION or new_h > self.MAX_IMAGE_DIMENSION:
                    ratio = min(self.MAX_IMAGE_DIMENSION / float(new_w), self.MAX_IMAGE_DIMENSION / float(new_h))
                    new_w = int(round(new_w * ratio))
                    new_h = int(round(new_h * ratio))
                logger.info(f"Upscaling image from {width}x{height} to {new_w}x{new_h}")
                img = img.resize((new_w, new_h), resample=Image.LANCZOS)
                width, height = new_w, new_h

            # Save as high-quality PNG for CubiCasa5K processing
            output_buffer = BytesIO()
            img.save(output_buffer, format='PNG', optimize=True)
            processed_bytes = output_buffer.getvalue()
            
            logger.info(f"Image processed: {width}x{height}, {len(processed_bytes)} bytes")
            return processed_bytes, (width, height)
    
    def _process_pdf(self, file_content: bytes) -> Tuple[bytes, Tuple[int, int]]:
        """
        Process single-page PDF files.
        
        Args:
            file_content: PDF file bytes
            
        Returns:
            Tuple of (image_bytes, dimensions)
        """
        try:
            doc = fitz.open("pdf", file_content)
            page = doc.load_page(0)  # We know it's single page from validation
            
            # Check for embedded images first (most efficient)
            image_list = page.get_images()
            if image_list:
                logger.info("Extracting embedded image from PDF")
                return self._extract_pdf_embedded_image(doc, page, image_list[0])
            
            # Fallback: Convert PDF page to image
            logger.info("Converting PDF page to image")
            return self._convert_pdf_page_to_image(page)
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise FileProcessingError(f"Could not process PDF: {str(e)}")
        finally:
            if 'doc' in locals():
                doc.close()
    
    def _extract_pdf_embedded_image(self, doc, page, img_ref) -> Tuple[bytes, Tuple[int, int]]:
        """Extract embedded image from PDF."""
        try:
            # Get image data
            xref = img_ref[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Process extracted image
            with Image.open(BytesIO(image_bytes)) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                width, height = img.size
                
                # Save as PNG
                output_buffer = BytesIO()
                img.save(output_buffer, format='PNG', optimize=True)
                processed_bytes = output_buffer.getvalue()
                
                logger.info(f"Extracted embedded image: {width}x{height}")
                return processed_bytes, (width, height)
                
        except Exception as e:
            logger.warning(f"Could not extract embedded image: {str(e)}")
            # Fall back to page rendering
            return self._convert_pdf_page_to_image(page)
    
    def _convert_pdf_page_to_image(self, page) -> Tuple[bytes, Tuple[int, int]]:
        """Convert PDF page to high-resolution image."""
        # Use high DPI for better CubiCasa5K accuracy
        matrix = fitz.Matrix(2.0, 2.0)  # 2x scaling = ~150 DPI
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        
        with Image.open(BytesIO(img_data)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            width, height = img.size
            
            # Optimize for CubiCasa5K
            output_buffer = BytesIO()
            img.save(output_buffer, format='PNG', optimize=True)
            processed_bytes = output_buffer.getvalue()
            
            logger.info(f"PDF page converted to image: {width}x{height}")
            return processed_bytes, (width, height)
    
    def create_processing_job(self, file_content: bytes, filename: str) -> ProcessingJob:
        """
        Create a new processing job from uploaded file.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            ProcessingJob with initial data
            
        Raises:
            FileProcessingError: If file processing fails
        """
        # Validate file
        validation_result = self.validate_file(file_content, filename)
        
        # Process to image format
        image_bytes, dimensions = self.process_file_to_image(
            file_content, 
            validation_result["file_format"]
        )
        
        # Generate unique job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Create processing job
        job = ProcessingJob(
            job_id=job_id,
            filename=filename,
            file_format=validation_result["file_format"],
            file_size_bytes=validation_result["file_size_bytes"],
            current_step="file_processed"
        )
        
        # Store processed image temporarily
        # TODO: In production, store in cloud storage or database
        temp_image_path = self.temp_dir / f"{job_id}.png"
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)
            
        logger.info(f"Processing job created: {job_id} for {filename}")
        return job
    
    def cleanup_temp_files(self, job_id: str) -> None:
        """Clean up temporary files for a job."""
        temp_image_path = self.temp_dir / f"{job_id}.png"
        if temp_image_path.exists():
            temp_image_path.unlink()
            logger.info(f"Cleaned up temp file for job: {job_id}")


# Convenience function for direct use
def process_uploaded_file(file_content: bytes, filename: str) -> ProcessingJob:
    """
    Process an uploaded file and create a processing job.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        
    Returns:
        ProcessingJob ready for CubiCasa5K processing
        
    Raises:
        FileProcessingError: If processing fails
    """
    processor = FileProcessor()
    return processor.create_processing_job(file_content, filename)