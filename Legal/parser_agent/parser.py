import fitz
import logging
import pytesseract
from PIL import Image
import io
import os

logger = logging.getLogger(__name__)

def extract_images_from_pdf(pdf_file):
    """Extract images from PDF pages."""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                images.append({
                    "image": image,
                    "page": page_num + 1,
                    "index": img_index
                })
                
        return images
    except Exception as e:
        logger.error(f"Failed to extract images from PDF: {str(e)}")
        return []

def extract_text_from_image(image_file):
    """Extract text from an image file using OCR."""
    try:
        # Read the image file
        image = Image.open(image_file)
        
        # Perform OCR
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            raise Exception("No text could be extracted from the image. Please ensure the image is clear and readable.")
            
        return text
    except Exception as e:
        logger.error(f"Image OCR failed: {str(e)}")
        raise Exception(f"Failed to extract text from image: {str(e)}")

def extract_text_from_pdf(file):
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        
        # First try to extract text directly
        for page in doc:
            text += page.get_text()
        
        # If no text is found or text is minimal, try OCR on the pages
        if not text.strip() or len(text.strip()) < 100:  # Arbitrary threshold
            logger.info("Minimal text found, attempting OCR on pages...")
            text = ""
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img) + "\n"
        
        # Extract text from embedded images
        images = extract_images_from_pdf(file)
        if images:
            logger.info(f"Found {len(images)} images in PDF, extracting text...")
            for img_data in images:
                try:
                    img_text = pytesseract.image_to_string(img_data["image"])
                    if img_text.strip():
                        text += f"\n[Text from image on page {img_data['page']}]:\n{img_text}\n"
                except Exception as e:
                    logger.error(f"Failed to extract text from image on page {img_data['page']}: {str(e)}")
        
        if not text.strip():
            raise Exception("No text could be extracted from the document. Please ensure the document is clear and readable.")
            
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise Exception(f"Failed to extract text from document: {str(e)}")

def extract_text(file):
    """Main function to extract text from either PDF or image files."""
    try:
        # Get file extension
        file_extension = os.path.splitext(file.name)[1].lower()
        
        # Handle different file types
        if file_extension == '.pdf':
            return extract_text_from_pdf(file)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return extract_text_from_image(file)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        raise Exception(f"Failed to process document: {str(e)}")
