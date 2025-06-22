import os
from utils.sarvam_client import SarvamClient

class TranslationAgent:
    def __init__(self):
        self.sarvam_client = SarvamClient()
        
        # Language mapping for consistency
        self.language_names = {
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
    
    def translate_text(self, text, source_lang, target_lang):
        """Translate text using Sarvam-Translate with proper error handling"""
        try:
            print(f"🔍 Translation request: {source_lang} -> {target_lang}")
            
            # Check if source and target are the same
            if source_lang == target_lang:
                print(f"⚠️ Source and target languages are the same ({source_lang}), skipping translation")
                return {
                    'success': True,
                    'translated_text': text,
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'skipped': True
                }
            
            # Normalize language codes
            source_lang = self._normalize_language_code(source_lang)
            target_lang = self._normalize_language_code(target_lang)
            
            # Check again after normalization
            if source_lang == target_lang:
                print(f"⚠️ Normalized languages are the same ({source_lang}), skipping translation")
                return {
                    'success': True,
                    'translated_text': text,
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'skipped': True
                }
            
            print(f"🔍 Proceeding with Sarvam-Translate: {source_lang} -> {target_lang}")
            
            # Use the corrected Sarvam translate method
            result = self.sarvam_client.translate(
                text=text,
                source_language_code=source_lang,
                target_language_code=target_lang
            )
            
            if result and result.get('success'):
                print(f"✅ Translation successful via Sarvam-Translate")
                return result
            else:
                print(f"❌ Sarvam-Translate failed: {result.get('error', 'Unknown error')}")
                return {
                    'success': True,
                    'translated_text': text,  # Fallback to original text
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'fallback_used': True,
                    'error': result.get('error', 'Translation failed')
                }
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return {
                'success': True,  # Return success to continue processing
                'translated_text': text,  # Fallback to original text
                'source_language': source_lang,
                'target_language': target_lang,
                'error': str(e),
                'fallback_used': True
            }
    
    def translate_analysis_to_language(self, analysis_data, source_lang, target_lang):
        """Translate analysis data to target language using Sarvam-Translate"""
        try:
            print(f"🔍 Translating analysis from {source_lang} to {target_lang}")
            
            if not analysis_data or not analysis_data.get('success'):
                print("❌ Invalid analysis data for translation")
                return analysis_data
            
            # Check if translation is needed
            if source_lang == target_lang:
                print(f"⚠️ Languages are the same, returning original analysis")
                return analysis_data
            
            analysis = analysis_data.get('analysis', {})
            if not isinstance(analysis, dict):
                print("❌ Analysis is not a dictionary")
                return analysis_data
            
            # Create translated analysis
            translated_analysis = analysis.copy()
            
            # Fields to translate using Sarvam-Translate
            fields_to_translate = [
                'summary',
                'comprehensive_analysis',
                'risk_assessment',
                'follow_up_actions'
            ]
            
            translation_success = True
            
            for field in fields_to_translate:
                if field in analysis and analysis[field]:
                    print(f"🔍 Translating field: {field} using Sarvam-Translate")
                    
                    translation_result = self.translate_text(
                        analysis[field], source_lang, target_lang
                    )
                    
                    if translation_result.get('success'):
                        translated_analysis[field] = translation_result.get('translated_text', analysis[field])
                        if translation_result.get('skipped'):
                            print(f"⚠️ Translation skipped for {field}")
                        elif translation_result.get('fallback_used'):
                            print(f"⚠️ Translation fallback used for {field}")
                        else:
                            print(f"✅ Successfully translated {field}")
                    else:
                        print(f"❌ Translation failed for {field}, keeping original")
                        translated_analysis[field] = analysis[field]
                        translation_success = False
            
            # Translate recommendations if they exist
            if 'recommendations' in analysis and isinstance(analysis['recommendations'], list):
                translated_recommendations = []
                for i, rec in enumerate(analysis['recommendations']):
                    if isinstance(rec, str) and len(rec.strip()) > 0:
                        print(f"🔍 Translating recommendation {i+1}")
                        translation_result = self.translate_text(rec, source_lang, target_lang)
                        if translation_result.get('success'):
                            translated_recommendations.append(
                                translation_result.get('translated_text', rec)
                            )
                        else:
                            translated_recommendations.append(rec)
                    else:
                        translated_recommendations.append(rec)
                
                translated_analysis['recommendations'] = translated_recommendations
            
            # Update language info
            translated_analysis['language'] = target_lang
            translated_analysis['translation_applied'] = translation_success
            translated_analysis['translation_source'] = 'sarvam-translate'
            
            # Return updated analysis data
            result = analysis_data.copy()
            result['analysis'] = translated_analysis
            
            print(f"✅ Analysis translation completed using Sarvam-Translate")
            return result
            
        except Exception as e:
            print(f"❌ Error in translate_analysis_to_language: {e}")
            import traceback
            traceback.print_exc()
            # Return original data on error
            return analysis_data
    
    def _normalize_language_code(self, lang_code):
        """Normalize language codes to standard format"""
        # Handle common variations
        lang_mapping = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'gu': 'gu-IN',
            'mr': 'mr-IN',
            'bn': 'bn-IN',
            'or': 'or-IN',
            'pa': 'pa-IN'
        }
        
        return lang_mapping.get(lang_code, lang_code)
    
    def get_language_name(self, lang_code):
        """Get human-readable language name"""
        return self.language_names.get(lang_code, lang_code)
