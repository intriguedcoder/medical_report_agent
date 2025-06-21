import os
import tempfile
from agents.ocr_agent import OCRAgent
from agents.medicalanalyser_agent import MedicalAnalyzerAgent
from agents.translation_agent import TranslationAgent
from agents.voice_agent import VoiceAgent
from utils.language_detector import LanguageDetector


class OrchestratorAgent:  # Make sure this class name matches your import
    def __init__(self):
        self.ocr_agent = OCRAgent()
        self.medical_agent = MedicalAnalyzerAgent()
        self.translation_agent = TranslationAgent()
        self.voice_agent = VoiceAgent()
        self.language_detector = LanguageDetector()
    
    def process_medical_report(self, image_path, user_language='en-IN', audio_language='hi-IN'):
        """Process medical report with improved error handling and audio generation"""
        try:
            print("Starting report processing...")
            print(f"Image path: {image_path}")
            print(f"User language: {user_language}")
            print(f"Audio language: {audio_language}")
            
            # Step 1: Extract text from image
            print("Extracting text from image...")
            ocr_result = self.ocr_agent.extract_text_from_image(image_path)
            print(f"OCR result: {ocr_result.get('success', False)}")
            
            if not ocr_result.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to extract text from image'
                }
            
            extracted_text = ocr_result.get('text', '')
            if not extracted_text.strip():
                return {
                    'success': False,
                    'error': 'No text found in the image'
                }
            
            # Step 2: Detect language using instance method
            detected_language = self.language_detector.detect_language(extracted_text)
            language_name = self.language_detector.get_language_name(detected_language)
            
            print(f"Detected language: {detected_language} ({language_name})")
            print(f"Final languages - User: {user_language}, Audio: {audio_language}")
            
            # Step 3: Analyze medical data
            print("Analyzing medical data...")
            analysis_result = self.medical_agent.analyze_report(
                extracted_text, user_language
            )
            print(f"Analysis result: {analysis_result.get('success', False)}")
            
            if not analysis_result.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to analyze medical report'
                }
            
            # Step 4: Handle translation more intelligently
            print(f"Processing language-specific response...")
            
            if user_language == audio_language:
                print(f"⚠️ User and audio languages are the same ({user_language}), skipping translation")
                translated_result = analysis_result  # Use original analysis
            else:
                # Only translate if languages are different
                try:
                    print(f"Translating from {user_language} to {audio_language}")
                    translated_result = self.translation_agent.translate_analysis_to_language(
                        analysis_result, user_language, audio_language
                    )
                except Exception as translation_error:
                    print(f"❌ Translation failed: {translation_error}")
                    translated_result = analysis_result  # Use original on translation failure
            
            # Step 5: Generate voice response with better error handling
            print(f"Generating voice response in {audio_language}...")
            
            audio_file = None
            try:
                audio_file = self.voice_agent.generate_speech_response(
                    translated_result, audio_language
                )
                print(f"Voice generation result: {audio_file}")
                
                if audio_file and os.path.exists(audio_file):
                    print(f"✅ Audio generated successfully: {audio_file}")
                else:
                    print("⚠️ Voice generation failed, continuing without audio")
                    audio_file = None
                    
            except Exception as voice_error:
                print(f"❌ Voice generation error: {voice_error}")
                audio_file = None
            
            # Step 6: Generate text response
            text_response = self._generate_text_response(translated_result, user_language)
            
            # Return comprehensive result
            return {
                'success': True,
                'detected_language': detected_language,
                'language_name': language_name,
                'analysis': translated_result,
                'audio_file': audio_file,  # May be None if generation failed
                'audio_language': audio_language,
                'text_response': text_response
            }
            
        except Exception as e:
            print(f"❌ Error in process_medical_report: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }
    
    def _generate_text_response(self, analysis_data, language):
        """Generate language-specific text response with better error handling"""
        try:
            print(f"🔍 Generating text response for language: {language}")
            
            if not analysis_data or not analysis_data.get('success'):
                return self._get_error_message(language)
            
            analysis = analysis_data.get('analysis', {})
            if not isinstance(analysis, dict):
                return self._get_error_message(language)
            
            # Format the response
            formatted_text = self._format_response_by_language(analysis, language)
            
            print(f"🔍 Generated text response length: {len(formatted_text)}")
            return formatted_text
            
        except Exception as e:
            print(f"❌ Error generating text response: {e}")
            return self._get_error_message(language)
    
    def _format_response_by_language(self, analysis, language):
        """Format response based on language preferences"""
        try:
            # Get basic components
            summary = analysis.get('summary', 'Analysis completed.')
            comprehensive = analysis.get('comprehensive_analysis', '')
            recommendations = analysis.get('recommendations', [])
            
            # Format based on language
            if language.startswith('hi'):
                # Hindi formatting
                formatted = f"📋 **विश्लेषण सारांश**: {summary}\n\n"
                if comprehensive:
                    formatted += f"📊 **विस्तृत विश्लेषण**:\n{comprehensive}\n\n"
                if recommendations:
                    formatted += "💡 **सुझाव**:\n"
                    for rec in recommendations:
                        formatted += f"• {rec}\n"
                    formatted += "\n"
                formatted += "⚠️ **महत्वपूर्ण**: यह केवल जानकारी के लिए है। कृपया डॉक्टर से सलाह लें।"
                
            elif language.startswith('ta'):
                # Tamil formatting
                formatted = f"📋 **பகுப்பாய்வு சுருக்கம்**: {summary}\n\n"
                if comprehensive:
                    formatted += f"📊 **விரிவான பகுப்பாய்வு**:\n{comprehensive}\n\n"
                if recommendations:
                    formatted += "💡 **பரிந்துரைகள்**:\n"
                    for rec in recommendations:
                        formatted += f"• {rec}\n"
                    formatted += "\n"
                formatted += "⚠️ **முக்கியம்**: இது தகவலுக்கு மட்டுமே. தயவுசெய்து மருத்துவரை அணுகவும்।"
                
            else:
                # English formatting (default)
                formatted = f"📋 **Analysis Summary**: {summary}\n\n"
                if comprehensive:
                    formatted += f"📊 **Detailed Analysis**:\n{comprehensive}\n\n"
                if recommendations:
                    formatted += "💡 **Recommendations**:\n"
                    for rec in recommendations:
                        formatted += f"• {rec}\n"
                    formatted += "\n"
                formatted += "⚠️ **Important**: This is for informational purposes only. Please consult a doctor."
            
            return formatted
            
        except Exception as e:
            print(f"❌ Error formatting response: {e}")
            return self._get_error_message(language)
    
    def _get_error_message(self, language):
        """Get error message in specified language"""
        error_messages = {
            'hi-IN': '❌ रिपोर्ट का विश्लेषण नहीं हो सका। कृपया पुनः प्रयास करें।',
            'en-IN': '❌ Unable to analyze the report. Please try again.',
            'ta-IN': '❌ அறிக்கையை பகுப்பாய்வு செய்ய முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.',
            'te-IN': '❌ రిపోర్ట్‌ను విశ్లేషించలేకపోయాము. దయచేసి మళ్లీ ప్రయత్నించండి।',
            'kn-IN': '❌ ವರದಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ।',
            'ml-IN': '❌ റിപ്പോർട്ട് വിശകലനം ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക।',
        }
        
        return error_messages.get(language, error_messages['en-IN'])
