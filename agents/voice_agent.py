import os
import time
import uuid
import re
import json
from utils.sarvam_client import SarvamClient

class VoiceAgent:
    def __init__(self):
        self.sarvam_client = SarvamClient()
        
        # Updated voice profiles with correct speakers for each language
        self.voice_profiles = {
            'hi-IN': 'meera',      # Hindi - female
            'en-IN': 'arvind',     # English - male  
            'ta-IN': 'diya',       # Tamil - use 'diya' for Tamil
            'te-IN': 'pavithra',   # Telugu
            'kn-IN': 'maya',       # Kannada
            'ml-IN': 'vidya',      # Malayalam
            'gu-IN': 'manisha',    # Gujarati
            'mr-IN': 'anushka',    # Marathi
            'bn-IN': 'abhilash',   # Bengali
            'or-IN': 'arya',       # Odia
            'pa-IN': 'karun'       # Punjabi
        }
        
        # List of all valid speakers from Sarvam API
        self.allowed_speakers = [
            'meera', 'pavithra', 'maitreyi', 'arvind', 'amol', 
            'amartya', 'diya', 'neel', 'misha', 'vian', 'arjun', 
            'maya', 'anushka', 'abhilash', 'manisha', 'vidya', 
            'arya', 'karun', 'hitesh'
        ]
    
    def generate_speech_response(self, analysis_data, language='hi-IN'):
        """Generate speech from analysis data with enhanced error handling"""
        try:
            print(f"🔍 ===== VOICE AGENT DEBUG START =====")
            print(f"🔍 Generating speech for language: {language}")
            print(f"🔍 Analysis data type: {type(analysis_data)}")
            print(f"🔍 Analysis data success: {analysis_data.get('success') if isinstance(analysis_data, dict) else 'Not a dict'}")
            
            # Debug: Print the full analysis data structure
            if isinstance(analysis_data, dict):
                print(f"🔍 Analysis data keys: {list(analysis_data.keys())}")
                # Check for nested analysis
                if 'analysis' in analysis_data:
                    nested_analysis = analysis_data['analysis']
                    print(f"🔍 Nested analysis keys: {list(nested_analysis.keys()) if isinstance(nested_analysis, dict) else 'Not a dict'}")
            
            # Use Flask app root path if available, otherwise use project path
            try:
                from flask import current_app
                if current_app:
                    app_root = current_app.root_path
                    static_audio_dir = os.path.join(app_root, 'static', 'audio')
                else:
                    raise RuntimeError("No Flask app context")
            except:
                # Fallback to your project path
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                static_audio_dir = os.path.join(project_root, 'static', 'audio')
            
            print(f"🔍 Target audio directory: {static_audio_dir}")
            
            # Ensure static audio directory exists
            os.makedirs(static_audio_dir, exist_ok=True)
            
            # Set proper permissions
            if os.name != 'nt':  # Not Windows
                os.chmod(static_audio_dir, 0o755)
            
            # TEST TRANSLATION FIRST - ADDED FOR DEBUGGING
            self.test_translation(language)
            
            # Format speech text based on analysis data - ALWAYS TRANSLATE IF NEEDED
            if not analysis_data.get('success'):
                speech_text = self._get_error_speech(language)
                print(f"🔍 Using error speech text")
            else:
                speech_text = self._format_for_speech(analysis_data, language)
                print(f"🔍 Using formatted speech text")
            
            print(f"🔍 Speech text length: {len(speech_text)}")
            print(f"🔍 Speech text preview: {speech_text[:200]}...")
            
            # Validate and clean text for TTS - INCREASED LENGTH LIMIT
            speech_text = self._validate_text_for_tts(speech_text, max_length=800)  # Increased from 600
            print(f"🔍 Validated speech text length: {len(speech_text)}")
            
            # Get the correct speaker for the language
            speaker = self.voice_profiles.get(language, 'meera')
            print(f"🔍 Initial speaker selection: {speaker} for language: {language}")
            
            # Validate speaker is in allowed list
            if speaker not in self.allowed_speakers:
                print(f"❌ Invalid speaker {speaker}, using 'meera' as fallback")
                speaker = 'meera'
            
            print(f"🔍 Final speaker: {speaker}")
            
            # Generate audio using Sarvam TTS with timeout handling
            print(f"🔍 Calling Sarvam TTS...")
            audio_data = None
            max_retries = 2
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Ensure text is not too long before TTS call - INCREASED LIMIT
                    if len(speech_text) > 1000:  # Increased from 800
                        speech_text = speech_text[:1000]
                        last_period = speech_text.rfind('.')
                        if last_period > 500:  # Increased from 400
                            speech_text = speech_text[:last_period + 1]
                    
                    print(f"🔍 Final speech text length: {len(speech_text)}")
                    
                    audio_data = self.sarvam_client.text_to_speech(
                        speech_text,
                        language,
                        speaker=speaker
                    )
                    
                    if audio_data and len(audio_data) > 1000:  # Ensure we got substantial audio data
                        print(f"🔍 Audio data received: {len(audio_data)} bytes")
                        break
                    else:
                        print(f"⚠️ Insufficient audio data, retrying...")
                        retry_count += 1
                        if retry_count < max_retries:
                            time.sleep(1)  # Brief delay before retry
                        
                except Exception as tts_error:
                    print(f"❌ Sarvam TTS error (attempt {retry_count + 1}): {tts_error}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(1)
                    else:
                        return self.generate_fallback_audio(speech_text, language)
            
            if audio_data and len(audio_data) > 1000:
                # Create unique filename with timestamp
                timestamp = int(time.time())
                audio_filename = f"analysis_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
                audio_path = os.path.join(static_audio_dir, audio_filename)
                
                print(f"🔍 Saving audio to: {audio_path}")
                
                # Write audio data to file with error handling
                try:
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    print(f"🔍 Audio file written")
                    
                    # Set proper file permissions
                    if os.name != 'nt':  # Not Windows
                        os.chmod(audio_path, 0o644)
                    
                    # Verify file was created successfully
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        print(f"✅ Audio file created successfully: {audio_path}")
                        print(f"✅ File size: {file_size} bytes")
                        
                        if file_size > 0:
                            print(f"🔍 ===== VOICE AGENT DEBUG END - SUCCESS =====")
                            return audio_path
                        else:
                            print("❌ Audio file is empty")
                            return self.generate_fallback_audio(speech_text, language)
                    else:
                        print("❌ Audio file doesn't exist after writing")
                        return self.generate_fallback_audio(speech_text, language)
                        
                except IOError as e:
                    print(f"❌ Error writing audio file: {e}")
                    return self.generate_fallback_audio(speech_text, language)
            else:
                print("❌ No audio data received from TTS service")
                return self.generate_fallback_audio(speech_text, language)
                
        except Exception as e:
            print(f"❌ Error in generate_speech_response: {e}")
            import traceback
            traceback.print_exc()
            return self.generate_fallback_audio(speech_text if 'speech_text' in locals() else "Audio generation failed", language)
    
    def _validate_text_for_tts(self, text, max_length=800):  # Increased from 600
        """Validate and clean text before sending to TTS"""
        try:
            # Remove problematic characters but keep more punctuation
            text = re.sub(r'[^\w\s\.,!?;:\-\(\)\u0900-\u097F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0A80-\u0AFF\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F]', '', text)
            
            # Ensure reasonable length
            if len(text) > max_length:
                text = text[:max_length]
                last_period = text.rfind('.')
                if last_period > max_length // 2:
                    text = text[:last_period + 1]
            
            # Ensure it's not too short
            if len(text.strip()) < 10:
                return self._get_minimal_speech('en-IN')
            
            return text.strip()
            
        except Exception as e:
            print(f"❌ Error validating text for TTS: {e}")
            return self._get_minimal_speech('en-IN')
    
    def _get_minimal_speech(self, language):
        """Get minimal speech text that should always work"""
        minimal_messages = {
            'en-IN': "Your health report has been analyzed.",
            'hi-IN': "आपकी स्वास्थ्य रिपोर्ट का विश्लेषण हो गया है।",
            'ta-IN': "உங்கள் சுகாதார அறிக்கை பகுப்பாய்வு செய்யப்பட்டது।"
        }
        return minimal_messages.get(language, minimal_messages['en-IN'])

    def _get_conclusion_message(self, language):
        """Get conclusion message in the specified language - RESTORED FROM OLD CODE"""
        conclusions = {
            'en-IN': "Based on this report, there is no reason to worry, but always consult your doctor before taking any decisions.",
            'hi-IN': "इस रिपोर्ट के आधार पर, चिंता की कोई बात नहीं है, लेकिन कोई भी निर्णय लेने से पहले हमेशा अपने डॉक्टर से सलाह लें।",
            'ta-IN': "இந்த அறிக்கையின் அடிப்படையில், கவலைப்பட எந்த காரணமும் இல்லை, ஆனால் எந்த முடிவும் எடுப்பதற்கு முன் எப்போதும் உங்கள் மருத்துவரை அணுகவும்।",
            'te-IN': "ఈ రిపోర్ట్ ఆధారంగా, ఆందోళనకు ఎటువంటి కారణం లేదు, కానీ ఏదైనా నిర్ణయం తీసుకునే ముందు ఎల్లప్పుడూ మీ వైద్యుడిని సంప్రదించండి।",
            'kn-IN': "ಈ ವರದಿಯ ಆಧಾರದ ಮೇಲೆ, ಚಿಂತಿಸಲು ಯಾವುದೇ ಕಾರಣವಿಲ್ಲ, ಆದರೆ ಯಾವುದೇ ನಿರ್ಧಾರ ತೆಗೆದುಕೊಳ್ಳುವ ಮೊದಲು ಯಾವಾಗಲೂ ನಿಮ್ಮ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ।",
            'ml-IN': "ഈ റിപ്പോർട്ടിന്റെ അടിസ്ഥാനത്തിൽ, ആശങ്കപ്പെടാൻ യാതൊരു കാരണവുമില്ല, എന്നാൽ ഏതെങ്കിലും തീരുമാനം എടുക്കുന്നതിന് മുമ്പ് എപ്പോഴും നിങ്ങളുടെ ഡോക്ടറെ സമീപിക്കുക।",
            'gu-IN': "આ રિપોર્ટના આધારે, ચિંતા કરવાનું કોઈ કારણ નથી, પરંતુ કોઈપણ નિર્ણય લેતા પહેલા હંમેશા તમારા ડૉક્ટરની સલાહ લો।",
            'mr-IN': "या अहवालाच्या आधारे, काळजी करण्याचे कोणतेही कारण नाही, परंतु कोणताही निर्णय घेण्यापूर्वी नेहमी आपल्या डॉक्टरांचा सल्ला घ्या।",
            'bn-IN': "এই রিপোর্টের ভিত্তিতে, চিন্তার কোনো কারণ নেই, তবে কোনো সিদ্ধান্ত নেওয়ার আগে সর্বদা আপনার ডাক্তারের সাথে পরামর্শ করুন।",
            'or-IN': "ଏହି ରିପୋର୍ଟ ଆଧାରରେ, ଚିନ୍ତାର କୌଣସି କାରଣ ନାହିଁ, କିନ୍ତୁ କୌଣସି ନିଷ୍ପତ୍ତି ନେବା ପୂର୍ବରୁ ସର୍ବଦା ଆପଣଙ୍କ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
            'pa-IN': "ਇਸ ਰਿਪੋਰਟ ਦੇ ਆਧਾਰ 'ਤੇ, ਚਿੰਤਾ ਕਰਨ ਦੀ ਕੋਈ ਗੱਲ ਨਹੀਂ ਹੈ, ਪਰ ਕੋਈ ਵੀ ਫੈਸਲਾ ਲੈਣ ਤੋਂ ਪਹਿਲਾਂ ਹਮੇਸ਼ਾ ਆਪਣੇ ਡਾਕਟਰ ਨਾਲ ਸਲਾਹ ਕਰੋ।"
        }
        return conclusions.get(language, conclusions['en-IN'])

    # NEW METHOD: Translate analysis data for UI display
    def translate_analysis_for_display(self, analysis_data, target_language):
        """Translate analysis data for UI display"""
        try:
            print(f"🔍 === TRANSLATING ANALYSIS FOR UI DISPLAY ===")
            print(f"🔍 Target language: {target_language}")
            
            if target_language == 'en-IN':
                print(f"🔍 Target is English, returning original data")
                return analysis_data  # No translation needed
            
            # Extract the detailed summary
            english_summary = self._extract_english_summary(analysis_data)
            if not english_summary:
                print(f"🔍 No English summary found, returning original data")
                return analysis_data
            
            print(f"🔍 Found English summary: {len(english_summary)} chars")
            
            # Translate using Sarvam
            translated_summary = self._translate_with_sarvam(english_summary, target_language)
            
            # Create a deep copy of the analysis data
            translated_data = self._deep_copy_dict(analysis_data)
            
            # Update the analysis data with translated content
            self._update_analysis_with_translation(translated_data, translated_summary)
            
            print(f"✅ Analysis data translated for UI display")
            return translated_data
            
        except Exception as e:
            print(f"❌ Error translating analysis for display: {e}")
            import traceback
            traceback.print_exc()
            return analysis_data
    
    def _deep_copy_dict(self, original_dict):
        """Create a deep copy of a dictionary"""
        try:
            import copy
            return copy.deepcopy(original_dict)
        except:
            # Fallback manual copy
            if isinstance(original_dict, dict):
                new_dict = {}
                for key, value in original_dict.items():
                    if isinstance(value, dict):
                        new_dict[key] = self._deep_copy_dict(value)
                    elif isinstance(value, list):
                        new_dict[key] = value.copy()
                    else:
                        new_dict[key] = value
                return new_dict
            return original_dict
    
    def _update_analysis_with_translation(self, analysis_data, translated_text):
        """Update analysis data with translated text"""
        try:
            # Update nested analysis if it exists
            if 'analysis' in analysis_data and isinstance(analysis_data['analysis'], dict):
                if 'summary' in analysis_data['analysis']:
                    analysis_data['analysis']['summary'] = translated_text
                if 'comprehensive_analysis' in analysis_data['analysis']:
                    analysis_data['analysis']['comprehensive_analysis'] = translated_text
                if 'detailed_summary' in analysis_data['analysis']:
                    analysis_data['analysis']['detailed_summary'] = translated_text
            
            # Update top-level fields
            if 'summary' in analysis_data:
                analysis_data['summary'] = translated_text
            if 'comprehensive_analysis' in analysis_data:
                analysis_data['comprehensive_analysis'] = translated_text
            if 'detailed_summary' in analysis_data:
                analysis_data['detailed_summary'] = translated_text
                
        except Exception as e:
            print(f"❌ Error updating analysis with translation: {e}")
    
    def test_translation(self, target_language):
        """Test translation with simple text - ADDED FOR DEBUGGING"""
        if target_language == 'en-IN':
            print(f"🔍 Target is English, skipping translation test")
            return
            
        test_text = "Hello, this is a test message."
        print(f"🔍 Testing translation to {target_language}")
        print(f"🔍 Test input: {test_text}")
        
        try:
            result = self.sarvam_client.translate(
                text=test_text,
                source_language_code='en-IN',
                target_language_code=target_language
            )
            
            print(f"🔍 Test translation result: {result}")
            print(f"🔍 Test result type: {type(result)}")
            print(f"🔍 Test result success: {result.get('success') if result else 'No result'}")
            
            if result and result.get('success'):
                translated = result.get('translated_text', test_text)
                print(f"✅ Test translation successful!")
                print(f"🔍 Original: {test_text}")
                print(f"🔍 Translated: {translated}")
                
                if translated == test_text:
                    print(f"⚠️ WARNING: Test translation returned same text - translation may not be working!")
            else:
                print(f"❌ Test translation failed: {result.get('error') if result else 'No result'}")
                
        except Exception as e:
            print(f"❌ Test translation exception: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_for_speech(self, analysis_data, language):
        """Format analysis data for speech synthesis - ENHANCED WITH DEBUGGING"""
        try:
            print(f"🔍 === _format_for_speech DEBUG START ===")
            print(f"🔍 Target language: {language}")
            
            if not analysis_data.get('success'):
                print(f"🔍 Analysis not successful, returning error speech")
                return self._get_error_speech(language)
            
            # STEP 1: Get the English summary (source content)
            english_summary = self._extract_english_summary(analysis_data)
            
            if not english_summary or len(english_summary.strip()) < 50:
                print(f"🔍 No suitable English summary found, using fallback")
                return self._get_error_speech(language)
            
            print(f"🔍 English summary length: {len(english_summary)}")
            print(f"🔍 English summary preview: {english_summary[:200]}...")
            
            # STEP 2: If target language is English, use directly
            if language == 'en-IN':
                print(f"🔍 Target language is English, using summary directly")
                speech_content = self._make_concise_for_tts(english_summary, language)
                return self._finalize_speech_text(speech_content, language)  # FIXED: Added language parameter
            
            # STEP 3: For other languages, ALWAYS translate using Sarvam-Translate
            print(f"🔍 Translating English summary to {language} using Sarvam-Translate")
            translated_text = self._translate_with_sarvam(english_summary, language)
            speech_content = self._make_concise_for_tts(translated_text, language)
            return self._finalize_speech_text(speech_content, language)  # FIXED: Added language parameter
            
        except Exception as e:
            print(f"❌ Error formatting speech text: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_speech(language)
    
    def _extract_english_summary(self, analysis_data):
        """Extract English summary from analysis data"""
        try:
            # Check nested analysis first
            nested_analysis = analysis_data.get('analysis', {})
            if nested_analysis:
                summary = nested_analysis.get('summary', '')
                if summary and len(summary.strip()) > 50:
                    return summary
                
                comprehensive = nested_analysis.get('comprehensive_analysis', '')
                if comprehensive and len(comprehensive.strip()) > 50:
                    return comprehensive
                    
                detailed = nested_analysis.get('detailed_summary', '')
                if detailed and len(detailed.strip()) > 50:
                    return detailed
            
            # Check top-level
            summary = analysis_data.get('summary', '')
            if summary and len(summary.strip()) > 50:
                return summary
            
            comprehensive = analysis_data.get('comprehensive_analysis', '')
            if comprehensive and len(comprehensive.strip()) > 50:
                return comprehensive
                
            detailed = analysis_data.get('detailed_summary', '')
            if detailed and len(detailed.strip()) > 50:
                return detailed
            
            return ""
            
        except Exception as e:
            print(f"❌ Error extracting English summary: {e}")
            return ""
    
    def _translate_with_sarvam(self, english_text, target_language):
        """Translate English text to target language using Sarvam-Translate - ENHANCED WITH DEBUGGING"""
        try:
            print(f"🔍 Translating with Sarvam: {len(english_text)} chars to {target_language}")
            print(f"🔍 Input text: {english_text[:100]}...")
            print(f"🔍 Source language: 'en-IN'")
            print(f"🔍 Target language: '{target_language}'")
            print(f"🔍 Supported languages: {list(self.voice_profiles.keys())}")
            
            if target_language == 'en-IN':
                print(f"🔍 Target is English, returning original text")
                return english_text
            
            # Handle long text by chunking - IMPROVED CHUNKING
            if len(english_text) > 800:  # Increased from 700
                return self._translate_long_text(english_text, target_language)
            
            # Test Sarvam connection first
            try:
                connection_test = self.sarvam_client.test_connection()
                print(f"🔍 Sarvam connection test: {connection_test}")
            except:
                print(f"⚠️ Could not test Sarvam connection")
            
            # Use Sarvam client to translate
            result = self.sarvam_client.translate(
                text=english_text,
                source_language_code='en-IN',
                target_language_code=target_language
            )
            
            print(f"🔍 Sarvam translation result: {result}")
            print(f"🔍 Result type: {type(result)}")
            print(f"🔍 Result success: {result.get('success') if result else 'No result'}")
            
            if result and result.get('success'):
                translated_text = result.get('translated_text', english_text)
                print(f"✅ Translation successful!")
                print(f"🔍 Original length: {len(english_text)}")
                print(f"🔍 Translated length: {len(translated_text)}")
                print(f"🔍 Translated preview: {translated_text[:200]}...")
                
                # Verify translation actually happened
                if translated_text != english_text:
                    return translated_text
                else:
                    print(f"⚠️ Translation returned same text - using fallback")
                    return self._get_fallback_translation(english_text, target_language)
            else:
                print(f"❌ Translation failed: {result.get('error') if result else 'No result'}")
                return self._get_fallback_translation(english_text, target_language)
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_translation(english_text, target_language)
    
    def _translate_long_text(self, text, target_language):
        """Translate long text by chunking with better sentence preservation - IMPROVED"""
        try:
            print(f"🔍 Translating long text: {len(text)} chars")
            
            # If text is extremely long, truncate first but more conservatively
            if len(text) > 2500:  # Increased from 2000
                text = text[:2500]
                last_period = text.rfind('.')
                if last_period > 1200:  # Increased from 1000
                    text = text[:last_period + 1]
            
            # Split text into sentences more carefully
            sentences = re.split(r'(?<=[.!?])\s+', text)  # Better sentence splitting
            translated_sentences = []
            
            current_chunk = ""
            chunk_limit = 600  # Increased from 400
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Add sentence with proper spacing
                test_chunk = current_chunk + (" " if current_chunk else "") + sentence + "."
                
                if len(test_chunk) < chunk_limit:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        translated_chunk = self._translate_with_sarvam(current_chunk, target_language)
                        translated_sentences.append(translated_chunk)
                    current_chunk = sentence + "."
            
            # Translate remaining chunk
            if current_chunk:
                translated_chunk = self._translate_with_sarvam(current_chunk, target_language)
                translated_sentences.append(translated_chunk)
            
            final_text = " ".join(translated_sentences)
            
            # Final safety check - more conservative
            if len(final_text) > 1000:  # Increased from 800
                final_text = final_text[:1000]
                last_period = final_text.rfind('.')
                if last_period > 500:  # Increased from 400
                    final_text = final_text[:last_period + 1]
            
            return final_text
            
        except Exception as e:
            print(f"❌ Error translating long text: {e}")
            return text[:600]  # Increased fallback from 400
    
    def _get_fallback_translation(self, text, target_language):
        """Provide fallback translations for common phrases"""
        fallback_translations = {
            'hi-IN': {
                'Keep eating healthy foods like you are doing': 'जैसा आप कर रहे हैं वैसे ही स्वस्थ भोजन खाते रहें',
                'Eat more fruits and vegetables every day': 'रोज फल और सब्जियां खाएं',
                'This test shows how your body is working': 'यह जांच दिखाती है कि आपका शरीर कैसे काम कर रहा है',
                'Your health report shows': 'आपकी स्वास्थ्य रिपोर्ट दिखाती है',
                'Hello! I have analyzed your medical report': 'नमस्ते! मैंने आपकी मेडिकल रिपोर्ट का विश्लेषण किया है'
            },
            'ta-IN': {
                'Keep eating healthy foods like you are doing': 'நீங்கள் செய்வது போல் ஆரோக்கியமான உணவுகளை தொடர்ந்து சாப்பிடுங்கள்',
                'Eat more fruits and vegetables every day': 'தினமும் அதிக பழங்கள் மற்றும் காய்கறிகள் சாப்பிடுங்கள்',
                'This test shows how your body is working': 'இந்த பரிசோதனை உங்கள் உடல் எப்படி வேலை செய்கிறது என்பதைக் காட்டுகிறது',
                'Your health report shows': 'உங்கள் சுகாதார அறிக்கை காட்டுகிறது',
                'Hello! I have analyzed your medical report': 'வணக்கம்! நான் உங்கள் மருத்துவ அறிக்கையை பகுப்பாய்வு செய்துள்ளேன்'
            }
        }
        
        lang_dict = fallback_translations.get(target_language, {})
        return lang_dict.get(text, text)
    
    def _make_concise_for_tts(self, text, language):
        """Make text more concise for TTS - IMPROVED TO PRESERVE MORE CONTENT"""
        try:
            # Remove very long sentences and keep only essential information
            sentences = re.split(r'[.!?]+', text)
            
            # Keep more sentences for better context - INCREASED LIMITS
            important_sentences = []
            for sentence in sentences[:8]:  # Increased from 6
                sentence = sentence.strip()
                if len(sentence) > 10 and len(sentence) < 200:  # Increased max length from 150
                    important_sentences.append(sentence)
            
            concise_text = '. '.join(important_sentences[:7])  # Increased from 5
            
            # Ensure it's not too long for TTS - INCREASED LIMIT
            if len(concise_text) > 800:  # Increased from 600
                concise_text = concise_text[:800]
                # Find last complete sentence
                last_period = concise_text.rfind('.')
                if last_period > 400:  # Increased from 300
                    concise_text = concise_text[:last_period + 1]
            
            return concise_text
            
        except Exception as e:
            print(f"❌ Error making text concise: {e}")
            return text[:600]  # Increased fallback from 400
    
    def _finalize_speech_text(self, text, language='en-IN'):
        """Finalize speech text with proper formatting and conclusion - RESTORED FROM OLD CODE"""
        try:
            # Clean up the text
            text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
            text = text.strip()
            
            # Ensure it ends with proper punctuation
            if not text.endswith(('.', '!', '?')):
                text += '.'
            
            # Add conclusion message - THIS WAS MISSING IN THE NEW CODE
            conclusion = self._get_conclusion_message(language)
            text = f"{text} {conclusion}"
            
            return text
            
        except Exception as e:
            print(f"❌ Error finalizing speech text: {e}")
            return text
    
    def _get_error_speech(self, language):
        """Get error message for speech in specified language"""
        error_messages = {
            'en-IN': "I'm sorry, I couldn't analyze your medical report properly. Please try uploading the image again or consult with your healthcare provider.",
            'hi-IN': "मुझे खुशी है कि मैं आपकी मेडिकल रिपोर्ट का सही विश्लेषण नहीं कर सका। कृपया छवि को फिर से अपलोड करें या अपने डॉक्टर से सलाह लें।",
            'ta-IN': "மன்னிக்கவும், உங்கள் மருத்துவ அறிக்கையை சரியாக பகுப்பாய்வு செய்ய முடியவில்லை। படத்தை மீண்டும் பதிவேற்றவும் அல்லது உங்கள் மருத்துவரை அணுகவும்।"
        }
        error_text = error_messages.get(language, error_messages['en-IN'])
        
        # Add conclusion to error message as well
        conclusion = self._get_conclusion_message(language)
        return f"{error_text} {conclusion}"
    
    def generate_fallback_audio(self, text, language):
        """Generate fallback audio when main TTS fails"""
        try:
            print(f"🔍 Generating fallback audio for language: {language}")
            
            # Use longer text for fallback - INCREASED FROM 200
            fallback_text = text[:300] if len(text) > 300 else text
            
            # Ensure it ends properly
            if not fallback_text.endswith(('.', '!', '?')):
                last_period = fallback_text.rfind('.')
                if last_period > 100:  # Increased from 50
                    fallback_text = fallback_text[:last_period + 1]
                else:
                    fallback_text += '.'
            
            print(f"🔍 Fallback text length: {len(fallback_text)}")
            
            # Try with different speakers
            fallback_speakers = ['meera', 'arvind', 'diya']
            
            for speaker in fallback_speakers:
                try:
                    print(f"🔍 Trying fallback speaker: {speaker}")
                    audio_data = self.sarvam_client.text_to_speech(
                        fallback_text,
                        language,
                        speaker=speaker
                    )
                    
                    if audio_data and len(audio_data) > 500:  # Ensure minimum audio size
                        # Save fallback audio
                        timestamp = int(time.time())
                        audio_filename = f"fallback_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
                        
                        try:
                            from flask import current_app
                            static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
                        except:
                            project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                            static_audio_dir = os.path.join(project_root, 'static', 'audio')
                        
                        audio_path = os.path.join(static_audio_dir, audio_filename)
                        
                        with open(audio_path, 'wb') as f:
                            f.write(audio_data)
                        
                        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                            print(f"✅ Fallback audio generated: {audio_path}")
                            return audio_path
                            
                except Exception as speaker_error:
                    print(f"❌ Fallback speaker {speaker} failed: {speaker_error}")
                    continue
            
            # If all else fails, try with absolute minimum text
            try:
                minimal_text = self._get_minimal_speech(language)
                audio_data = self.sarvam_client.text_to_speech(
                    minimal_text,
                    language,
                    speaker='meera'
                )
                
                if audio_data:
                    # Save minimal audio
                    timestamp = int(time.time())
                    audio_filename = f"minimal_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
                    
                    try:
                        from flask import current_app
                        static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
                    except:
                        project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                        static_audio_dir = os.path.join(project_root, 'static', 'audio')
                    
                    audio_path = os.path.join(static_audio_dir, audio_filename)
                    
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"✅ Minimal fallback audio generated: {audio_path}")
                        return audio_path
                    
            except Exception as minimal_error:
                print(f"❌ Minimal fallback failed: {minimal_error}")
            
            print(f"❌ All fallback speakers failed")
            return None
            
        except Exception as e:
            print(f"❌ Error generating fallback audio: {e}")
            return None
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return list(self.voice_profiles.keys())
    
    def get_language_name(self, language_code):
        """Get human-readable language name"""
        language_names = {
            'hi-IN': 'Hindi',
            'en-IN': 'English',
            'ta-IN': 'Tamil',
            'te-IN': 'Telugu',
            'kn-IN': 'Kannada',
            'ml-IN': 'Malayalam',
            'gu-IN': 'Gujarati',
            'mr-IN': 'Marathi',
            'bn-IN': 'Bengali',
            'or-IN': 'Odia',
            'pa-IN': 'Punjabi'
        }
        return language_names.get(language_code, language_code)
    
    def validate_language(self, language_code):
        """Validate if language is supported"""
        return language_code in self.voice_profiles
    
    def debug_translation_status(self, language='hi-IN'):
        """Debug method to check translation status and capabilities"""
        try:
            print(f"🔍 === TRANSLATION DEBUG STATUS ===")
            print(f"🔍 Target language: {language}")
            print(f"🔍 Supported languages: {list(self.voice_profiles.keys())}")
            print(f"🔍 Language validation: {self.validate_language(language)}")
            
            # Test Sarvam client connection
            try:
                if hasattr(self.sarvam_client, 'test_connection'):
                    connection_status = self.sarvam_client.test_connection()
                    print(f"🔍 Sarvam connection: {connection_status}")
                else:
                    print(f"🔍 Sarvam connection: test_connection method not available")
            except Exception as conn_error:
                print(f"❌ Sarvam connection error: {conn_error}")
            
            # Test simple translation
            if language != 'en-IN':
                test_result = self.test_translation(language)
                print(f"🔍 Translation test completed")
            else:
                print(f"🔍 Target is English, skipping translation test")
            
            # Check voice profile
            speaker = self.voice_profiles.get(language, 'meera')
            print(f"🔍 Selected speaker: {speaker}")
            print(f"🔍 Speaker validation: {speaker in self.allowed_speakers}")
            
            return {
                'language': language,
                'supported': self.validate_language(language),
                'speaker': speaker,
                'speaker_valid': speaker in self.allowed_speakers,
                'sarvam_available': hasattr(self, 'sarvam_client') and self.sarvam_client is not None
            }
            
        except Exception as e:
            print(f"❌ Debug translation status error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'language': language,
                'supported': False
            }
    
    def cleanup_old_audio_files(self, max_age_hours=24):
        """Clean up old audio files to save space"""
        try:
            try:
                from flask import current_app
                static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
            except:
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                static_audio_dir = os.path.join(project_root, 'static', 'audio')
            
            if not os.path.exists(static_audio_dir):
                return
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(static_audio_dir):
                if filename.endswith('.wav'):
                    file_path = os.path.join(static_audio_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            print(f"🗑️ Cleaned up old audio file: {filename}")
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Error cleaning up audio files: {e}")
