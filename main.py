import os
import logging
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image

logger = logging.getLogger(__name__)

class ImageConverter:
    """Handles image conversion operations"""
    
    SUPPORTED_FORMATS = {
        "png": "PNG",
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "webp": "WEBP",
        "bmp": "BMP",
        "ico": "ICO",
        "gif": "GIF",
        "tiff": "TIFF"
    }
    
    def __init__(self, max_size_mb: int = 20):
        self.max_size_mb = max_size_mb
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        quality: int = 90,
        resize: Optional[Tuple[int, int]] = None
    ) -> Tuple[bool, str]:
        """
        Convert an image to the specified format
        
        Args:
            input_path: Path to input image
            output_path: Path to save converted image
            target_format: Target format (png, jpg, webp, etc.)
            quality: Quality for lossy formats (1-100)
            resize: Optional (width, height) to resize
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate input file
            if not input_path.exists():
                return False, f"Input file not found: {input_path}"
            
            # Check file size
            file_size_mb = input_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                return False, f"File too large ({file_size_mb:.1f}MB). Max: {self.max_size_mb}MB"
            
            # Open image
            try:
                img = Image.open(input_path)
            except Exception as e:
                return False, f"Failed to open image: {str(e)}"
            
            # Get original format
            original_format = img.format or "Unknown"
            
            # Resize if requested
            if resize:
                img = img.resize(resize, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB for JPEG
            if target_format.lower() in ["jpg", "jpeg"] and img.mode in ["RGBA", "P"]:
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            
            # Convert to RGB for BMP (which doesn't support RGBA)
            if target_format.lower() == "bmp" and img.mode == "RGBA":
                img = img.convert("RGB")
            
            # Save with proper parameters
            save_kwargs = {}
            if target_format.lower() in ["jpg", "jpeg"]:
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True
            elif target_format.lower() == "webp":
                save_kwargs["quality"] = quality
                save_kwargs["method"] = 6  # Best compression
            elif target_format.lower() == "png":
                save_kwargs["optimize"] = True
                save_kwargs["compress_level"] = 6
            
            # Save image
            img.save(output_path, format=target_format.upper(), **save_kwargs)
            
            # Validate output
            if not output_path.exists() or output_path.stat().st_size == 0:
                return False, "Conversion failed - output file is empty"
            
            return True, f"Successfully converted to {target_format.upper()}"
            
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return False, f"Conversion error: {str(e)}"
    
    def get_supported_formats(self) -> dict:
        """Get dictionary of supported formats"""
        return self.SUPPORTED_FORMATS.copy()
    
    def get_file_size(self, path: Path) -> str:
        """Get human-readable file size"""
        size_bytes = path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"
