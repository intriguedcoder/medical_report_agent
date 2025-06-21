import pytesseract
from PIL import Image
import os
import logging
import re

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
        """Extract text from image with comprehensive error handling - FIXED DATA STRUCTURE"""
        try:
            print(f"🔍 OCR: Processing image: {image_path}")
            
            # Validate image path
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': f'Image file not found: {image_path}',
                    'text': '',
                    'cleaned_text': ''  # Added for compatibility
                }
            
            # Open and process image
            image = Image.open(image_path)
            print(f"🔍 OCR: Image size: {image.size}, mode: {image.mode}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhanced OCR configurations for medical documents
            configs = [
                '--oem 3 --psm 6',  # Default - uniform block of text
                '--oem 3 --psm 4',  # Single column of text
                '--oem 3 --psm 3',  # Fully automatic page segmentation
                '--oem 3 --psm 11', # Sparse text - good for forms
                '--oem 3 --psm 12', # Sparse text with OSD
                '--oem 3 --psm 1',  # Automatic page segmentation with OSD
            ]
            
            extracted_text = ""
            best_config = ""
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(
                        image, 
                        lang=self.language,
                        config=config
                    ).strip()
                    
                    # Prioritize text with medical keywords or numbers
                    if text and self._is_better_medical_text(text, extracted_text):
                        extracted_text = text
                        best_config = config
                        print(f"🔍 OCR: Better result with config: {config}")
                        
                except Exception as e:
                    print(f"🔍 OCR: Config {config} failed: {e}")
                    continue
            
            if not extracted_text:
                return {
                    'success': False,
                    'error': 'No text could be extracted from the image. The image may be too blurry, have poor contrast, or contain no readable text.',
                    'text': '',
                    'cleaned_text': ''
                }
            
            # Clean the extracted text for better medical analysis
            cleaned_text = self._clean_medical_text(extracted_text)
            
            print(f"🔍 OCR: Extracted text length: {len(extracted_text)}")
            print(f"🔍 OCR: Cleaned text length: {len(cleaned_text)}")
            print(f"🔍 OCR: Best config used: {best_config}")
            print(f"🔍 OCR: Text preview: {cleaned_text[:200]}...")
            
            # Check if we got meaningful medical content
            if self._contains_medical_content(cleaned_text):
                print(f"✅ OCR: Medical content detected in extracted text")
            else:
                print(f"⚠️ OCR: No clear medical content detected")
            
            return {
                'success': True,
                'text': extracted_text,           # Original text
                'cleaned_text': cleaned_text,     # Cleaned text for medical analysis
                'error': None,
                'config_used': best_config
            }
            
        except pytesseract.TesseractNotFoundError:
            return {
                'success': False,
                'error': 'Tesseract OCR engine not found. Please install with: brew install tesseract',
                'text': '',
                'cleaned_text': ''
            }
        except Exception as e:
            logging.error(f"OCR extraction failed: {str(e)}")
            return {
                'success': False,
                'error': f'OCR processing failed: {str(e)}',
                'text': '',
                'cleaned_text': ''
            }

    def _is_better_medical_text(self, new_text, current_text):
        """Determine if new text is better for medical analysis"""
        if not current_text:
            return True
        
        if len(new_text) < 10:  # Too short
            return False
        
        # Count medical indicators
        medical_keywords = [
            'blood', 'sugar', 'glucose', 'cholesterol', 'pressure', 'hemoglobin',
            'test', 'result', 'level', 'mg/dL', 'mmHg', 'patient', 'name', 'age',
            'report', 'analysis', 'normal', 'high', 'low', 'date', 'value'
        ]
        
        new_score = sum(1 for keyword in medical_keywords if keyword.lower() in new_text.lower())
        current_score = sum(1 for keyword in medical_keywords if keyword.lower() in current_text.lower())
        
        # Also consider text length and number presence
        new_has_numbers = bool(re.search(r'\d+', new_text))
        current_has_numbers = bool(re.search(r'\d+', current_text))
        
        # Prefer text with more medical keywords, numbers, and reasonable length
        if new_score > current_score:
            return True
        elif new_score == current_score:
            if new_has_numbers and not current_has_numbers:
                return True
            elif len(new_text) > len(current_text) * 1.2:  # Significantly longer
                return True
        
        return False

    def _clean_medical_text(self, text):
        """Clean extracted text for better medical analysis"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors in medical context
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # Fix split numbers
        text = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', text)  # Fix decimal points
        text = re.sub(r'(\d)\s*/\s*(\d)', r'\1/\2', text)  # Fix ratios like blood pressure
        
        # Clean up common OCR mistakes
        text = text.replace('|', 'I')  # Common mistake
        text = text.replace('0', 'O')  # In some contexts
        
        # Remove extra line breaks but preserve structure
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple line breaks to double
        text = re.sub(r'\n\s+', '\n', text)  # Line breaks with spaces
        
        return text.strip()

    def _contains_medical_content(self, text):
        """Check if text contains medical content"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Medical indicators
        medical_indicators = [
            'blood', 'sugar', 'glucose', 'cholesterol', 'pressure', 'hemoglobin',
            'test', 'result', 'level', 'patient', 'report', 'analysis',
            'mg/dl', 'mmhg', 'normal', 'high', 'low', 'date', 'value',
            'creatinine', 'urea', 'triglycerides', 'hdl', 'ldl'
        ]
        
        # Check for medical terms
        medical_term_count = sum(1 for term in medical_indicators if term in text_lower)
        
        # Check for numbers (important in medical reports)
        has_numbers = bool(re.search(r'\d+', text))
        
        # Check for medical units
        medical_units = ['mg/dl', 'mmhg', 'mg', 'ml', 'units', '%', 'g/dl']
        has_medical_units = any(unit in text_lower for unit in medical_units)
        
        # Consider it medical content if it has medical terms + numbers or medical units
        return (medical_term_count >= 2 and has_numbers) or has_medical_units
