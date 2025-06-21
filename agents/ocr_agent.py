import pytesseract
from PIL import Image
import os
import logging

class OCRAgent:
    def __init__(self, language='eng'):
        self.language = language
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract path for macOS"""
        try:
            # Test if tesseract is accessible
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            # Try common macOS paths
            possible_paths = [
                '/usr/local/bin/tesseract',  # Homebrew Intel
                '/opt/homebrew/bin/tesseract',  # Homebrew Apple Silicon
                '/opt/local/bin/tesseract'  # MacPorts
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
            else:
                raise Exception("Tesseract not found. Please install with: brew install tesseract")
    
    def extract_text_from_image(self, image_path):
        """Extract text from image with comprehensive error handling"""
        try:
            print(f"Processing image: {image_path}")
            
            # Validate image path
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': f'Image file not found: {image_path}',
                    'text': ''
                }
            
            # Open and process image
            image = Image.open(image_path)
            print(f"Image size: {image.size}, mode: {image.mode}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Try multiple OCR configurations
            configs = [
                '--oem 3 --psm 6',  # Default
                '--oem 3 --psm 3',  # Fully automatic page segmentation
                '--oem 3 --psm 4',  # Single column of text
                '--oem 3 --psm 7',  # Single text line
                '--oem 3 --psm 8',  # Single word
                '--oem 3 --psm 11', # Sparse text
                '--oem 3 --psm 12', # Sparse text with OSD
            ]
            
            extracted_text = ""
            for config in configs:
                try:
                    text = pytesseract.image_to_string(
                        image, 
                        lang=self.language,
                        config=config
                    ).strip()
                    
                    if text and len(text) > len(extracted_text):
                        extracted_text = text
                        print(f"Best result with config: {config}")
                        
                except Exception as e:
                    print(f"Config {config} failed: {e}")
                    continue
            
            if not extracted_text:
                return {
                    'success': False,
                    'error': 'No text could be extracted from the image. The image may be too blurry, have poor contrast, or contain no readable text.',
                    'text': ''
                }
            
            print(f"Extracted text length: {len(extracted_text)}")
            print(f"First 100 chars: {extracted_text[:100]}...")
            
            return {
                'success': True,
                'text': extracted_text,
                'error': None
            }
            
        except pytesseract.TesseractNotFoundError:
            return {
                'success': False,
                'error': 'Tesseract OCR engine not found. Please install with: brew install tesseract',
                'text': ''
            }
        except Exception as e:
            logging.error(f"OCR extraction failed: {str(e)}")
            return {
                'success': False,
                'error': f'OCR processing failed: {str(e)}',
                'text': ''
            }
