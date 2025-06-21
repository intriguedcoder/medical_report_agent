import re
import requests
from utils.medical_knowledge import MedicalKnowledgeBase
from utils.sarvam_client import SarvamClient

class MedicalAnalyzerAgent:
    def __init__(self):
        self.knowledge_base = MedicalKnowledgeBase()
        self.sarvam_client = SarvamClient()
        
    def analyze_report(self, ocr_result, user_language='en-IN', audio_language=None):
        """Enhanced analysis using Sarvam-M for comprehensive report generation with audio language support"""
        
        # Add type checking and validation to fix the error
        if isinstance(ocr_result, str):
            # If ocr_result is a string, convert it to expected dictionary format
            ocr_result = {
                'success': True,
                'cleaned_text': ocr_result
            }
        elif not isinstance(ocr_result, dict):
            return {
                'success': False,
                'error': 'Invalid OCR result format - expected dictionary or string',
                'summary': self._get_error_message(user_language),
                'audio_language': audio_language or user_language
            }
        
        # Now safely check the success key
        if not ocr_result.get('success', False):
            return {
                'success': False,
                'error': 'OCR extraction failed',
                'summary': self._get_error_message(user_language),
                'audio_language': audio_language or user_language
            }
        
        extracted_text = ocr_result.get('cleaned_text', '')
        
        # Ensure extracted_text is a string
        if not isinstance(extracted_text, str):
            extracted_text = str(extracted_text)
        
        # Use Sarvam-M to generate comprehensive medical analysis
        comprehensive_analysis = self._generate_sarvam_analysis(extracted_text, user_language)
        
        # Extract structured data using traditional methods as backup
        structured_data = self._extract_structured_data(extracted_text, user_language)
        
        # Combine AI-generated insights with structured analysis
        final_analysis = self._combine_analyses(comprehensive_analysis, structured_data, user_language)
        
        # Add audio language to the result
        final_analysis['audio_language'] = audio_language or user_language
        
        return final_analysis
    
    def _generate_sarvam_analysis(self, medical_text, language='en-IN'):
        """Use Sarvam-M to generate comprehensive medical report analysis"""
        
        # Create a detailed prompt for Sarvam-M
        analysis_prompt = self._create_analysis_prompt(medical_text, language)
        
        try:
            # Call Sarvam-M API for comprehensive analysis
            response = self._call_sarvam_m_api(analysis_prompt)
            
            if response and response.get('success'):
                return self._parse_sarvam_response(response['content'], language)
            else:
                return self._fallback_analysis(medical_text, language)
                
        except Exception as e:
            print(f"Sarvam-M API error: {e}")
            return self._fallback_analysis(medical_text, language)
    
    def _create_analysis_prompt(self, medical_text, language):
        """Create a comprehensive prompt for Sarvam-M"""
        
        language_instructions = {
            'en-IN': {
                'instruction': "Analyze this medical report and provide a comprehensive assessment in English",
                'format': "English"
            },
            'hi-IN': {
                'instruction': "इस मेडिकल रिपोर्ट का विश्लेषण करें और हिंदी में व्यापक मूल्यांकन प्रदान करें",
                'format': "Hindi"
            },
            'ta-IN': {
                'instruction': "இந்த மருத்துவ அறிக்கையை பகுப்பாய்வு செய்து தமிழில் விரிவான மதிப்பீடு வழங்கவும்",
                'format': "Tamil"
            },
            'te-IN': {
                'instruction': "ఈ వైద్య నివేదికను విశ్లేషించి తెలుగులో సమగ్ర అంచనా అందించండి",
                'format': "Telugu"
            },
            'bn-IN': {
                'instruction': "এই চিকিৎসা রিপোর্টটি বিশ্লেষণ করুন এবং বাংলায় একটি বিস্তৃত মূল্যায়ন প্রদান করুন",
                'format': "Bengali"
            }
        }
        
        lang_config = language_instructions.get(language, language_instructions['en-IN'])
        
        prompt = f"""
{lang_config['instruction']}

Medical Report Text:
{medical_text}

Please provide a comprehensive analysis in {lang_config['format']} including:

1. **Patient Summary**: Brief overview of the patient's condition
2. **Key Findings**: Important test results and their interpretations
3. **Normal vs Abnormal Values**: Clear identification of concerning values
4. **Health Recommendations**: Specific dietary and lifestyle advice
5. **Risk Assessment**: Potential health risks based on the findings
6. **Follow-up Actions**: What the patient should do next
7. **Medication Insights**: If any medications are mentioned, explain their purpose

Format your response as a structured medical assessment that a patient can easily understand. Use simple language and avoid complex medical jargon. If any values are critical or require immediate attention, clearly highlight this. Respond in {lang_config['format']} language only.
"""
        return prompt
    
    def _call_sarvam_m_api(self, prompt):
        """Call Sarvam-M API for analysis"""
        url = "https://api.sarvam.ai/chat/completions"
        
        payload = {
            "model": "sarvam-m",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert medical AI assistant specializing in Indian healthcare. Provide accurate, culturally appropriate medical analysis while being empathetic and clear in your explanations."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        headers = {
            "api-subscription-key": self.sarvam_client.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'content': result['choices'][0]['message']['content']
                }
            else:
                print(f"Sarvam-M API error: {response.status_code}")
                return {'success': False}
        except Exception as e:
            print(f"Sarvam-M API exception: {e}")
            return {'success': False}
    
    def _parse_sarvam_response(self, ai_content, language):
        """Parse and structure the AI-generated analysis"""
        
        # Ensure ai_content is a string
        if not isinstance(ai_content, str):
            ai_content = str(ai_content)
            
        return {
            'success': True,
            'ai_generated': True,
            'comprehensive_analysis': ai_content,
            'summary': self._extract_summary_from_ai_response(ai_content),
            'recommendations': self._extract_recommendations_from_ai_response(ai_content),
            'risk_assessment': self._extract_risk_assessment_from_ai_response(ai_content),
            'follow_up_actions': self._extract_followup_from_ai_response(ai_content),
            'language': language
        }
    
    def _extract_summary_from_ai_response(self, content):
        """Extract summary section from AI response"""
        if not isinstance(content, str):
            content = str(content)
            
        lines = content.split('\n')
        summary_lines = []
        capturing = False
        
        for line in lines:
            if 'patient summary' in line.lower() or 'summary' in line.lower():
                capturing = True
                continue
            elif capturing and ('key findings' in line.lower() or '**' in line):
                break
            elif capturing:
                summary_lines.append(line.strip())
        
        return ' '.join(summary_lines).strip() if summary_lines else content[:200] + "..."
    
    def _extract_recommendations_from_ai_response(self, content):
        """Extract recommendations from AI response"""
        if not isinstance(content, str):
            content = str(content)
            
        lines = content.split('\n')
        recommendations = []
        capturing = False
        
        for line in lines:
            if 'recommendation' in line.lower() or 'advice' in line.lower():
                capturing = True
                continue
            elif capturing and ('risk assessment' in line.lower() or 'follow-up' in line.lower()):
                break
            elif capturing and line.strip() and not line.startswith('**'):
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _extract_risk_assessment_from_ai_response(self, content):
        """Extract risk assessment from AI response"""
        if not isinstance(content, str):
            content = str(content)
            
        lines = content.split('\n')
        risk_lines = []
        capturing = False
        
        for line in lines:
            if 'risk assessment' in line.lower() or 'risk' in line.lower():
                capturing = True
                continue
            elif capturing and ('follow-up' in line.lower() or 'medication' in line.lower()):
                break
            elif capturing and line.strip() and not line.startswith('**'):
                risk_lines.append(line.strip())
        
        return ' '.join(risk_lines).strip() if risk_lines else "Please consult with your healthcare provider for risk assessment."
    
    def _extract_followup_from_ai_response(self, content):
        """Extract follow-up actions from AI response"""
        if not isinstance(content, str):
            content = str(content)
            
        lines = content.split('\n')
        followup_lines = []
        capturing = False
        
        for line in lines:
            if 'follow-up' in line.lower() or 'next steps' in line.lower():
                capturing = True
                continue
            elif capturing and ('medication' in line.lower() or '**' in line):
                break
            elif capturing and line.strip() and not line.startswith('**'):
                followup_lines.append(line.strip())
        
        return ' '.join(followup_lines).strip() if followup_lines else "Schedule regular follow-up appointments with your healthcare provider."
    
    def _fallback_analysis(self, medical_text, language='en-IN'):
        """Fallback analysis when Sarvam-M API fails"""
        try:
            # Extract basic structured data
            structured_data = self._extract_structured_data(medical_text, language)
            
            # Generate basic analysis using knowledge base
            basic_analysis = self._generate_basic_analysis(medical_text, structured_data, language)
            
            return {
                'success': True,
                'ai_generated': False,
                'comprehensive_analysis': basic_analysis,
                'summary': self._generate_fallback_summary(structured_data, language),
                'recommendations': self._generate_basic_recommendations(structured_data, language),
                'risk_assessment': self._generate_basic_risk_assessment(structured_data, language),
                'follow_up_actions': self._generate_basic_followup(structured_data, language),
                'language': language,
                'fallback_used': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Fallback analysis failed: {str(e)}',
                'summary': self._get_error_message(language)
            }

    def _generate_basic_analysis(self, medical_text, structured_data, language):
        """Generate basic analysis without AI"""
        analysis_parts = []
        
        # Basic text analysis
        if structured_data.get('test_results'):
            analysis_parts.append("Test results have been extracted from your medical report.")
        
        if structured_data.get('abnormal_values'):
            analysis_parts.append("Some values appear to be outside normal ranges.")
        
        if structured_data.get('medications'):
            analysis_parts.append("Medications have been identified in the report.")
        
        return ' '.join(analysis_parts) if analysis_parts else "Basic medical report analysis completed."

    def _generate_fallback_summary(self, structured_data, language):
        """Generate a basic summary when AI fails"""
        error_messages = {
            'en-IN': "Medical report processed. Please consult with your healthcare provider for detailed interpretation.",
            'hi-IN': "मेडिकल रिपोर्ट प्रोसेस की गई। विस्तृत व्याख्या के लिए कृपया अपने डॉक्टर से सलाह लें।",
            'ta-IN': "மருத்துவ அறிக்கை செயலாக்கப்பட்டது. விரிவான விளக்கத்திற்கு உங்கள் மருத்துவரை அணுகவும்।",
            'te-IN': "వైద్య నివేదిక ప్రాసెస్ చేయబడింది. వివరణాత్మక వివరణ కోసం దయచేసి మీ వైద్యుడిని సంప్రదించండి।",
            'bn-IN': "চিকিৎসা রিপোর্ট প্রক্রিয়াজাত করা হয়েছে। বিস্তারিত ব্যাখ্যার জন্য আপনার চিকিৎসকের সাথে পরামর্শ করুন।"
        }
        return error_messages.get(language, error_messages['en-IN'])

    def _generate_basic_recommendations(self, structured_data, language):
        """Generate basic recommendations"""
        basic_recommendations = {
            'en-IN': [
                "Consult with your healthcare provider",
                "Follow prescribed medications as directed",
                "Maintain regular follow-up appointments"
            ],
            'hi-IN': [
                "अपने डॉक्टर से सलाह लें",
                "निर्धारित दवाएं नियमित रूप से लें",
                "नियमित जांच कराते रहें"
            ],
            'ta-IN': [
                "உங்கள் மருத்துவரை அணுகவும்",
                "பரிந்துரைக்கப்பட்ட மருந்துகளை எடுத்துக்கொள்ளுங்கள்",
                "வழக்கமான பரிசோதனைகளை மேற்கொள்ளுங்கள்"
            ],
            'te-IN': [
                "మీ వైద్యుడిని సంప్రదించండి",
                "సూచించిన మందులను తీసుకోండి",
                "క్రమం తప్పకుండా తనిఖీలు చేయించుకోండి"
            ],
            'bn-IN': [
                "আপনার চিকিৎসকের সাথে পরামর্শ করুন",
                "নির্ধারিত ওষুধ সেবন করুন",
                "নিয়মিত চেকআপ করান"
            ]
        }
        return basic_recommendations.get(language, basic_recommendations['en-IN'])

    def _generate_basic_risk_assessment(self, structured_data, language):
        """Generate basic risk assessment"""
        risk_messages = {
            'en-IN': "Please discuss these results with your healthcare provider for proper risk assessment.",
            'hi-IN': "उचित जोखिम मूल्यांकन के लिए कृपया इन परिणामों पर अपने डॉक्टर से चर्चा करें।",
            'ta-IN': "சரியான ஆபத்து மதிப்பீட்டிற்கு இந்த முடிவுகளை உங்கள் மருத்துவருடன் விவாதிக்கவும்।",
            'te-IN': "సరైన ప్రమాద అంచనా కోసం ఈ ఫలితాలను మీ వైద్యుడితో చర్చించండి।",
            'bn-IN': "সঠিক ঝুঁকি মূল্যায়নের জন্য এই ফলাফলগুলি আপনার চিকিৎসকের সাথে আলোচনা করুন।"
        }
        return risk_messages.get(language, risk_messages['en-IN'])

    def _generate_basic_followup(self, structured_data, language):
        """Generate basic follow-up actions"""
        followup_messages = {
            'en-IN': "Schedule a follow-up appointment with your healthcare provider to discuss these results.",
            'hi-IN': "इन परिणामों पर चर्चा करने के लिए अपने डॉक्टर के साथ फॉलो-अप अपॉइंटमेंट लें।",
            'ta-IN': "இந்த முடிவுகளைப் பற்றி விவாதிக்க உங்கள் மருத்துவருடன் பின்தொடர்தல் சந்திப்பை ஏற்பாடு செய்யுங்கள்।",
            'te-IN': "ఈ ఫలితాలను చర్చించడానికి మీ వైద్యుడితో ఫాలో-అప్ అపాయింట్మెంట్ షెడ్యూల్ చేయండి।",
            'bn-IN': "এই ফলাফলগুলি নিয়ে আলোচনা করতে আপনার চিকিৎসকের সাথে ফলো-আপ অ্যাপয়েন্টমেন্ট নির্ধারণ করুন।"
        }
        return followup_messages.get(language, followup_messages['en-IN'])

    def _extract_structured_data(self, text, language):
        """Extract structured data from medical text"""
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
            
        structured_data = {
            'test_results': [],
            'abnormal_values': [],
            'medications': [],
            'patient_info': {}
        }
        
        # Extract test results using regex patterns
        test_patterns = [
            r'(\w+)\s*:\s*([0-9.]+)\s*([a-zA-Z/%]+)?',
            r'(\w+)\s*=\s*([0-9.]+)\s*([a-zA-Z/%]+)?',
            r'(\w+)\s+([0-9.]+)\s*([a-zA-Z/%]+)?'
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                test_name = match.group(1).strip()
                value = match.group(2).strip()
                unit = match.group(3).strip() if match.group(3) else ""
                
                structured_data['test_results'].append({
                    'name': test_name,
                    'value': value,
                    'unit': unit
                })
        
        # Extract medication information
        medication_keywords = ['tablet', 'capsule', 'syrup', 'injection', 'mg', 'ml']
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in medication_keywords):
                structured_data['medications'].append(line.strip())
        
        # Extract patient information
        patient_patterns = [
            r'name\s*:\s*([^\n]+)',
            r'age\s*:\s*([0-9]+)',
            r'gender\s*:\s*([^\n]+)',
            r'patient\s*id\s*:\s*([^\n]+)'
        ]
        
        for pattern in patient_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key = pattern.split('\\')[0].replace('s*', '').replace(':', '')
                structured_data['patient_info'][key] = match.group(1).strip()
        
        return structured_data

    def _combine_analyses(self, comprehensive_analysis, structured_data, language):
        """Combine AI-generated analysis with structured data"""
        if comprehensive_analysis.get('success'):
            # Use AI-generated analysis as primary
            result = comprehensive_analysis.copy()
            
            # Add structured data as additional information
            result['structured_data'] = structured_data
            
            return result
        else:
            # Fallback to structured analysis
            return self._fallback_analysis("", language)

    def _get_error_message(self, language):
        """Get error message in specified language"""
        error_messages = {
            'en-IN': "Unable to process the medical report. Please try again or consult with your healthcare provider.",
            'hi-IN': "मेडिकल रिपोर्ट को प्रोसेस करने में असमर्थ। कृपया पुनः प्रयास करें या अपने डॉक्टर से सलाह लें।",
            'ta-IN': "மருத்துவ அறிக்கையை செயலாக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும் அல்லது உங்கள் மருத்துவரை அணுகவும்.",
            'te-IN': "వైద్య నివేదికను ప్రాసెస్ చేయలేకపోయింది. దయచేసి మళ్లీ ప్రయత్నించండి లేదా మీ వైద్యుడిని సంప్రదించండి।",
            'bn-IN': "চিকিৎসা রিপোর্ট প্রক্রিয়াজাত করতে অক্ষম। অনুগ্রহ করে আবার চেষ্টা করুন বা আপনার চিকিৎসকের সাথে পরামর্শ করুন।"
        }
        return error_messages.get(language, error_messages['en-IN'])
