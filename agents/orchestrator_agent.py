import os
import tempfile
from agents.ocr_agent import OCRAgent
from agents.medicalanalyser_agent import MedicalAnalyzerAgent
from agents.translation_agent import TranslationAgent
from agents.voice_agent import VoiceAgent
from utils.language_detector import LanguageDetector

class OrchestratorAgent:
    def __init__(self):
        self.ocr_agent = OCRAgent()
        self.medical_agent = MedicalAnalyzerAgent()
        self.translation_agent = TranslationAgent()
        self.voice_agent = VoiceAgent()
        self.language_detector = LanguageDetector()
    
    def process_medical_report(self, image_path, user_language='en-IN', audio_language='hi-IN'):
        """Process medical report with improved content flow for voice synthesis"""
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
            
            # Step 3: Analyze medical data (ALWAYS in English first)
            print("Analyzing medical data...")
            analysis_result = self.medical_agent.analyze_report(
                extracted_text, 'en-IN'  # CHANGED: Always analyze in English first
            )
            print(f"Analysis result: {analysis_result.get('success', False)}")
            
            if not analysis_result.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to analyze medical report'
                }
            
            # Step 4: Generate audio response (VoiceAgent handles translation internally)
            print(f"Generating voice response in {audio_language}...")
            audio_file = None
            try:
                audio_file = self.voice_agent.generate_speech_response(
                    analysis_result, audio_language
                )
                
                if audio_file and os.path.exists(audio_file):
                    print(f"✅ Audio generated successfully: {audio_file}")
                else:
                    print("⚠️ Voice generation failed, continuing without audio")
                    audio_file = None
                    
            except Exception as voice_error:
                print(f"❌ Voice generation error: {voice_error}")
                import traceback
                traceback.print_exc()
                audio_file = None
            
            # Step 5: Generate text response - FIXED TRANSLATION LOGIC
            print(f"Generating text response in {user_language}...")
            if user_language == 'en-IN':
                # Use English analysis directly for text
                text_response = self._generate_text_response(analysis_result, user_language)
                final_analysis = analysis_result
            else:
                # FIXED: Properly translate the analysis data
                print(f"🔍 Translating analysis for UI display using VoiceAgent...")
                translated_analysis = self.voice_agent.translate_analysis_for_display(
                    analysis_result, user_language
                )
                
                # ADDITIONAL FIX: Translate recommendations separately if they're still in English
                if 'recommendations' in translated_analysis:
                    translated_recommendations = []
                    for rec in translated_analysis['recommendations']:
                        if self._is_english_text(rec):
                            translated_rec = self._translate_text_with_voice_agent(rec, user_language)
                            translated_recommendations.append(translated_rec)
                        else:
                            translated_recommendations.append(rec)
                    translated_analysis['recommendations'] = translated_recommendations
                
                text_response = self._generate_text_response(translated_analysis, user_language)
                final_analysis = translated_analysis
                
                # FIXED: Debug with only the language parameter
                print(f"🔍 Running translation debug for language: {user_language}")
                self.voice_agent.debug_translation_status(user_language)
            
            return {
                'success': True,
                'detected_language': detected_language,
                'language_name': language_name,
                'analysis': final_analysis,
                'audio_file': audio_file,
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

    def process_medical_report_with_email(self, image_path, user_language='en-IN', audio_language='hi-IN', 
                                         generate_email=True, patient_info=None):
        """Process medical report and optionally generate doctor consultation email"""
        try:
            # Process the report normally
            result = self.process_medical_report(image_path, user_language, audio_language)
            
            if result['success'] and generate_email:
                # Generate email draft
                email_result = self.medical_agent.generate_doctor_consultation_email(
                    result['analysis'], patient_info
                )
                
                if email_result and email_result['success']:
                    result['email_draft'] = email_result['email_draft']
                    result['urgency_level'] = email_result['urgency_level']
                    result['appointment_timeframe'] = email_result['suggested_appointment_timeframe']
                    
                    # Translate email if needed
                    if user_language != 'en-IN':
                        translated_email = self._translate_email_draft(
                            email_result['email_draft'], user_language
                        )
                        result['email_draft_translated'] = translated_email
            
            return result
            
        except Exception as e:
            print(f"❌ Error in process_medical_report_with_email: {e}")
            return result  # Return original result even if email generation fails

    def _translate_email_draft(self, email_draft, target_language):
        """Translate email draft to target language"""
        try:
            # Translate subject and body separately
            translated_subject = self.voice_agent._translate_with_sarvam(
                email_draft['subject'], target_language
            )
            
            translated_body = self.voice_agent._translate_with_sarvam(
                email_draft['body'], target_language
            )
            
            return {
                'subject': translated_subject,
                'body': translated_body,
                'urgency_level': email_draft['urgency_level'],
                'appointment_timeframe': email_draft['appointment_timeframe']
            }
            
        except Exception as e:
            print(f"❌ Error translating email: {e}")
            return email_draft  # Return original if translation fails
    
    def _is_english_text(self, text):
        """Check if text is primarily in English"""
        try:
            # Simple heuristic: if text contains mostly ASCII characters, it's likely English
            ascii_chars = sum(1 for char in text if ord(char) < 128)
            total_chars = len(text)
            return (ascii_chars / total_chars) > 0.8 if total_chars > 0 else False
        except:
            return False
    
    def _translate_text_with_voice_agent(self, text, target_language):
        """Translate individual text using VoiceAgent's translation method"""
        try:
            return self.voice_agent._translate_with_sarvam(text, target_language)
        except:
            return text
    
    def _generate_text_response(self, analysis_data, language):
        """Generate language-specific text response with better error handling"""
        try:
            print(f"🔍 Generating text response for language: {language}")
            
            if not analysis_data or not analysis_data.get('success'):
                return self._get_error_message(language)
            
            # Use analysis_data directly (content should already be translated by now)
            analysis = analysis_data
            if not isinstance(analysis, dict):
                return self._get_error_message(language)
            
            # Format the response - content should already be translated
            formatted_text = self._format_response_by_language(analysis, language)
            
            print(f"🔍 Generated text response length: {len(formatted_text)}")
            return formatted_text
            
        except Exception as e:
            print(f"❌ Error generating text response: {e}")
            return self._get_error_message(language)
    
    def _format_response_by_language(self, analysis, language):
        """Format response based on language preferences - HEADERS ONLY, CONTENT ALREADY TRANSLATED"""
        try:
            # Get basic components (these should already be translated)
            summary = analysis.get('summary', 'Analysis completed.')
            comprehensive = analysis.get('comprehensive_analysis', '')
            recommendations = analysis.get('recommendations', [])
            
            # ADDITIONAL CHECK: Ensure recommendations are translated
            if recommendations and language != 'en-IN':
                translated_recommendations = []
                for rec in recommendations:
                    if self._is_english_text(rec):
                        translated_rec = self._translate_text_with_voice_agent(rec, language)
                        translated_recommendations.append(translated_rec)
                    else:
                        translated_recommendations.append(rec)
                recommendations = translated_recommendations
            
            # Format with language-specific HEADERS only - content is already translated
            if language.startswith('hi'):
                # Hindi headers
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
                # Tamil headers
                formatted = f"📋 **பகுப்பாய்வு சுருக்கம்**: {summary}\n\n"
                if comprehensive:
                    formatted += f"📊 **விரிவான பகுப்பாய்வு**:\n{comprehensive}\n\n"
                if recommendations:
                    formatted += "💡 **பரிந்துரைகள்**:\n"
                    for rec in recommendations:
                        formatted += f"• {rec}\n"
                    formatted += "\n"
                formatted += "⚠️ **முக்கியம்**: இது தகவலுக்கு மட்டுமே. தயவுசெய்து மருத்துவரை அணுகவும்।"
                
            # [Include all other language formatting from your existing code]
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
            # [Include all other languages]
        }
        
        return error_messages.get(language, error_messages['en-IN'])
