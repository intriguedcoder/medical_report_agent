import re
import requests
from utils.medical_knowledge import MedicalKnowledgeBase
from utils.sarvam_client import SarvamClient

class MedicalAnalyzerAgent:
    def __init__(self):
        self.knowledge_base = MedicalKnowledgeBase()
        self.sarvam_client = SarvamClient()
        
    def analyze_report(self, ocr_result, user_language='en-IN', audio_language=None):
        """Enhanced analysis with simple language that anyone can understand"""
        
        # Handle input validation
        if isinstance(ocr_result, str):
            ocr_result = {
                'success': True,
                'cleaned_text': ocr_result
            }
        elif not isinstance(ocr_result, dict):
            return {
                'success': False,
                'error': 'Invalid OCR result format',
                'summary': self._get_error_message(user_language),
                'audio_language': audio_language or user_language
            }
        
        if not ocr_result.get('success', False):
            return {
                'success': False,
                'error': 'OCR extraction failed',
                'summary': self._get_error_message(user_language),
                'audio_language': audio_language or user_language
            }
        
        extracted_text = ocr_result.get('cleaned_text', '')
        if not isinstance(extracted_text, str):
            extracted_text = str(extracted_text)
        
        print(f"🔍 MEDICAL ANALYZER: Processing simple analysis of {len(extracted_text)} characters")
        
        # Extract structured data FIRST
        structured_data = self._extract_structured_data_comprehensive(extracted_text, user_language)
        print(f"🔍 MEDICAL ANALYZER: Extracted {len(structured_data.get('test_results', []))} test results")
        
        # Create simple comprehensive analysis
        final_analysis = self._create_simple_comprehensive_analysis(structured_data, extracted_text, user_language)
        
        final_analysis['audio_language'] = audio_language or user_language
        
        return final_analysis
    
    def _extract_structured_data_comprehensive(self, text, language):
        """Comprehensive structured data extraction with enhanced patterns"""
        if not isinstance(text, str):
            text = str(text)
            
        structured_data = {
            'test_results': [],
            'abnormal_values': [],
            'medications': [],
            'patient_info': {},
            'dates': [],
            'reference_ranges': []
        }
        
        print(f"🔍 EXTRACTING: Starting comprehensive data extraction...")
        
        # Enhanced test result patterns
        test_patterns = [
            # Standard medical test patterns
            r'(blood\s+sugar|glucose|fasting\s+glucose|random\s+glucose)\s*:?\s*([0-9]+\.?[0-9]*)\s*(mg/dL|mg/dl|mmol/L)?',
            r'(cholesterol|total\s+cholesterol|ldl|hdl|triglycerides)\s*:?\s*([0-9]+\.?[0-9]*)\s*(mg/dL|mg/dl|mmol/L)?',
            r'(blood\s+pressure|bp|systolic|diastolic)\s*:?\s*([0-9]+/[0-9]+|[0-9]+)\s*(mmHg|mm\s+Hg)?',
            r'(hemoglobin|hb|hgb)\s*:?\s*([0-9]+\.?[0-9]*)\s*(g/dL|g/dl|g%)?',
            r'(creatinine|urea|bun)\s*:?\s*([0-9]+\.?[0-9]*)\s*(mg/dL|mg/dl|mmol/L)?',
            r'(hba1c|a1c|glycated\s+hemoglobin)\s*:?\s*([0-9]+\.?[0-9]*)\s*(%)?',
            r'(tsh|t3|t4|thyroid)\s*:?\s*([0-9]+\.?[0-9]*)\s*(mIU/L|ng/dL|pmol/L)?',
            r'(vitamin\s+d|vit\s+d|25\s+oh\s+d)\s*:?\s*([0-9]+\.?[0-9]*)\s*(ng/mL|nmol/L)?',
            r'(vitamin\s+b12|b12|cobalamin)\s*:?\s*([0-9]+\.?[0-9]*)\s*(pg/mL|pmol/L)?',
            r'(iron|ferritin|transferrin)\s*:?\s*([0-9]+\.?[0-9]*)\s*(ng/mL|μg/L|mg/L)?',
            # Generic pattern for any test
            r'([A-Za-z][A-Za-z\s]{2,20})\s*:?\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z/%μ]+)?'
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                test_name = match.group(1).strip()
                value = match.group(2).strip()
                unit = match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else ""
                
                # Filter out obvious non-medical matches
                if len(test_name) > 2 and not any(exclude in test_name.lower() for exclude in ['page', 'date', 'time', 'phone', 'address']):
                    structured_data['test_results'].append({
                        'name': test_name,
                        'value': value,
                        'unit': unit,
                        'full_match': match.group(0)
                    })
        
        # Extract patient information
        patient_patterns = [
            r'(?:patient\s+)?name\s*:?\s*([A-Za-z\s]+)',
            r'age\s*:?\s*([0-9]+)\s*(?:years?|yrs?)?',
            r'(?:gender|sex)\s*:?\s*(male|female|m|f)',
            r'date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        ]
        
        for pattern in patient_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key = pattern.split('\\')[0].replace('(?:', '').replace('patient\\s+)?', '').replace('s*', '').replace(':', '').replace('?', '')
                structured_data['patient_info'][key] = match.group(1).strip()
        
        print(f"🔍 EXTRACTED: {len(structured_data['test_results'])} test results")
        for test in structured_data['test_results'][:3]:
            print(f"🔍 TEST: {test['name']} = {test['value']} {test['unit']}")
        
        return structured_data
    
    def _create_simple_comprehensive_analysis(self, structured_data, original_text, user_language):
        """Create detailed but simple analysis understandable by anyone, including a 5-year-old"""
        print(f"🔍 CREATING: Simple comprehensive analysis with {len(structured_data['test_results'])} test results")
        
        test_results = structured_data.get('test_results', [])
        patient_info = structured_data.get('patient_info', {})
        
        # Build comprehensive audio summary
        audio_summary_parts = []
        simple_parts = []
        summary_parts = []
        recommendations = []
        
        normal_count = 0
        concerning_count = 0
        
        # Audio introduction
        if test_results:
            audio_intro = f"Hello! I've analyzed your medical report which contains {len(test_results)} important health measurements. Let me explain each one in simple terms."
            audio_summary_parts.append(audio_intro)
            
            simple_parts.append(f"Hello! Let's talk about your health report. We looked at {len(test_results)} important things in your body to see how healthy you are.")
            summary_parts.append(f"Your health report shows {len(test_results)} important body measurements:")
            
            # Detailed explanation of each parameter for audio
            for i, test in enumerate(test_results):  # Analyze ALL tests
                test_name = test['name']
                test_value = test['value']
                test_unit = test['unit']
                
                interpretation = self._get_simple_interpretation(test_name, test_value, test_unit)
                
                # Create detailed audio explanation for each parameter
                audio_explanation = self._create_audio_parameter_explanation(
                    test_name, test_value, test_unit, interpretation, i + 1
                )
                audio_summary_parts.append(audio_explanation)
                
                # Build simple description for text
                if test_unit:
                    simple_description = f"Your {test_name} is {test_value} {test_unit}"
                else:
                    simple_description = f"Your {test_name} shows {test_value}"
                
                # Add simple status explanation with specific health implications
                if interpretation['status'] == 'good':
                    simple_description += f", which is good and healthy! {interpretation['health_implication']}"
                    normal_count += 1
                elif interpretation['status'] == 'a little high':
                    simple_description += f", which is a little high. {interpretation['health_implication']}"
                    concerning_count += 1
                elif interpretation['status'] == 'a little low':
                    simple_description += f", which is a little low. {interpretation['health_implication']}"
                    concerning_count += 1
                elif interpretation['status'] == 'needs attention':
                    simple_description += f", which needs attention. {interpretation['health_implication']}"
                    concerning_count += 1
                else:
                    simple_description += f". {interpretation['health_implication']}"
                
                simple_parts.append(simple_description)
                
                if i < 5:  # Include first 5 in summary
                    summary_parts.append(simple_description)
                
                # Add simple recommendations
                if interpretation.get('simple_advice'):
                    recommendations.append(interpretation['simple_advice'])
            
            # Overall health summary for audio
            audio_overall = self._create_audio_overall_summary(normal_count, concerning_count, len(test_results))
            audio_summary_parts.append(audio_overall)
            
            # Overall health summary in simple terms for text
            if concerning_count == 0:
                overall_message = f"Great news! All {normal_count} things we checked in your body look good and healthy. Your body is doing a wonderful job!"
                health_status = "You are healthy and strong!"
            elif concerning_count == 1:
                overall_message = f"Most things look good! {normal_count} things are healthy, but 1 thing needs some care. Don't worry, with help you can make it better."
                health_status = "You are mostly healthy, with one thing to work on."
            else:
                overall_message = f"Your body has {normal_count} good things and {concerning_count} things that need care. With help from your doctor and family, you can make everything better."
                health_status = "Your body needs some extra care to be healthy."
            
            simple_parts.append(overall_message)
            summary_parts.append(health_status)
            
            # DETAILED RISK FACTORS ANALYSIS
            detailed_risks = self._analyze_comprehensive_risk_factors(test_results)
            if detailed_risks:
                risk_explanation = f"Based on your test results, here are some health risks to be aware of: {'. '.join(detailed_risks)}."
                simple_parts.append(risk_explanation)
                summary_parts.append(f"Health risks identified: {', '.join(detailed_risks[:2])}.")
                
                # Add risk factors to audio
                audio_risk_explanation = f"Let me explain the health risks I found in your report: {'. '.join(detailed_risks)}."
                audio_summary_parts.append(audio_risk_explanation)
            
            # COMPREHENSIVE HEALTH IMPLICATIONS
            health_implications = self._generate_health_implications(test_results, concerning_count)
            if health_implications:
                implications_text = f"What this means for your health: {'. '.join(health_implications)}."
                simple_parts.append(implications_text)
                
                # Add to audio
                audio_implications = f"Here's what these results mean for your overall health: {'. '.join(health_implications)}."
                audio_summary_parts.append(audio_implications)
            
            # Simple personalized advice
            simple_advice = self._generate_simple_recommendations(test_results, patient_info, concerning_count)
            recommendations.extend(simple_advice)
            
            if recommendations:
                # Recommendations for audio
                audio_recommendations = f"Here are some simple steps you can take: {'. '.join(recommendations[:4])}."
                audio_summary_parts.append(audio_recommendations)
                
                # Recommendations for text
                advice_text = f"To stay healthy and strong, here's what you can do: {'. '.join(recommendations[:3])}."
                simple_parts.append(advice_text)
                summary_parts.append(f"Simple advice: {'. '.join(recommendations[:2])}.")
        
        # Add age-appropriate advice if we know the age
        age = patient_info.get('age')
        if age:
            try:
                age_int = int(age)
                age_advice = self._get_simple_age_advice(age_int, concerning_count)
                if age_advice:
                    simple_parts.append(age_advice)
            except:
                pass
        
        # Add general health advice based on overall report status - MOVED TO END
        general_advice = self._generate_general_health_advice(normal_count, concerning_count, len(test_results))
        simple_parts.append(general_advice)
        
        # Add general advice to audio as well
        audio_summary_parts.append(general_advice)
        
        # IMPORTANT: Always end audio with doctor consultation reminder
        doctor_reminder = "Remember, this is just an explanation of your test results. Always consult with your doctor before making any changes to your diet, medication, or lifestyle. Your doctor knows your complete health history and can give you the best personalized advice."
        audio_summary_parts.append(doctor_reminder)
        
        # Build final simple analysis
        comprehensive_analysis = ' '.join(simple_parts)
        summary = ' '.join(summary_parts)
        comprehensive_audio_summary = ' '.join(audio_summary_parts)
        
        # Add simple but important closing advice for text - ONLY AT THE END
        closing_advice = " Always consult with your doctor before making any changes to your diet, medication, or lifestyle. Your doctor knows your complete health history and can give you the best personalized advice."
        
        comprehensive_analysis += closing_advice
        summary += " Always consult with your doctor before making any changes to your diet, medication, or lifestyle."
        
        print(f"🔍 CREATED: Simple summary length = {len(summary)}")
        print(f"🔍 SUMMARY: {summary[:300]}...")
        
        return {
            'success': True,
            'ai_generated': False,
            'comprehensive_analysis': comprehensive_analysis,
            'summary': summary,
            'audio_summary': comprehensive_audio_summary,  # RESTORED: Comprehensive audio summary
            'recommendations': recommendations[:5],
            'risk_assessment': self._generate_simple_risk_assessment(concerning_count, normal_count),
            'follow_up_actions': self._generate_simple_followup(concerning_count),
            'language': user_language,
            'data_driven': True,
            'structured_data': structured_data,
            'normal_count': normal_count,
            'concerning_count': concerning_count,
            'simple_language': True,
            'detailed_risks': detailed_risks if 'detailed_risks' in locals() else [],
            'health_implications': health_implications if 'health_implications' in locals() else []
        }

    def _analyze_comprehensive_risk_factors(self, test_results):
        """Analyze comprehensive risk factors based on test results"""
        
        risk_factors = []
        
        for test in test_results:
            test_name = test['name'].lower()
            try:
                value = float(test['value'])
                
                # Blood sugar risks
                if any(term in test_name for term in ['glucose', 'sugar']):
                    if value > 200:
                        risk_factors.append("Very high blood sugar increases your risk of diabetes, heart disease, kidney damage, and nerve problems")
                    elif value > 140:
                        risk_factors.append("High blood sugar increases your risk of developing diabetes and heart problems")
                    elif value < 70:
                        risk_factors.append("Low blood sugar can cause dangerous episodes of weakness, confusion, and fainting")
                
                # Cholesterol risks
                elif 'cholesterol' in test_name:
                    if value > 240:
                        risk_factors.append("Very high cholesterol significantly increases your risk of heart attacks, strokes, and blocked arteries")
                    elif value > 200:
                        risk_factors.append("High cholesterol increases your risk of heart disease and stroke")
                
                # Blood pressure risks
                elif 'pressure' in test_name and '/' in test['value']:
                    try:
                        systolic = int(test['value'].split('/')[0])
                        if systolic > 180:
                            risk_factors.append("Very high blood pressure greatly increases your risk of heart attacks, strokes, kidney disease, and heart failure")
                        elif systolic > 140:
                            risk_factors.append("High blood pressure increases your risk of heart disease, stroke, and kidney problems")
                    except:
                        pass
                
                # HbA1c risks
                elif any(term in test_name for term in ['hba1c', 'a1c']):
                    if value > 7.0:
                        risk_factors.append("Poor long-term blood sugar control increases your risk of diabetes complications including eye, kidney, and nerve damage")
                    elif value > 6.4:
                        risk_factors.append("Elevated long-term blood sugar indicates diabetes risk and potential organ damage")
                
                # Hemoglobin risks
                elif any(term in test_name for term in ['hemoglobin', 'hb']):
                    if value < 10.0:
                        risk_factors.append("Severe anemia can cause heart problems, extreme fatigue, and difficulty with daily activities")
                    elif value < 12.0:
                        risk_factors.append("Low hemoglobin (anemia) can cause fatigue, weakness, and reduced quality of life")
                
                # Creatinine risks
                elif 'creatinine' in test_name:
                    if value > 2.0:
                        risk_factors.append("High creatinine indicates significant kidney problems that can lead to kidney failure")
                    elif value > 1.3:
                        risk_factors.append("Elevated creatinine suggests kidney function problems that need monitoring")
                
                # Thyroid risks
                elif any(term in test_name for term in ['tsh', 'thyroid']):
                    if value > 10.0:
                        risk_factors.append("Severely underactive thyroid can cause heart problems, depression, and memory issues")
                    elif value < 0.1:
                        risk_factors.append("Overactive thyroid can cause heart rhythm problems, bone loss, and anxiety")
                
            except:
                continue
        
        return risk_factors

    def _generate_health_implications(self, test_results, concerning_count):
        """Generate comprehensive health implications"""
        
        implications = []
        
        if concerning_count == 0:
            implications.append("Your test results show that your body systems are functioning well")
            implications.append("You have a lower risk of developing chronic diseases")
            implications.append("Your current health status supports a good quality of life")
        elif concerning_count == 1:
            implications.append("Most of your body systems are healthy, which is a good foundation")
            implications.append("The one area of concern can be improved with proper care")
            implications.append("Early intervention can prevent this from becoming a bigger problem")
        elif concerning_count <= len(test_results) // 2:
            implications.append("Some of your body systems need attention, but many are still functioning well")
            implications.append("You may be at increased risk for certain health complications")
            implications.append("With proper treatment, these issues can be managed effectively")
        else:
            implications.append("Multiple body systems need attention, which requires comprehensive care")
            implications.append("You may be at higher risk for serious health complications")
            implications.append("Working closely with healthcare providers is essential for your health")
        
        return implications

    def _generate_general_health_advice(self, normal_count, concerning_count, total_count):
        """Generate general health advice based on overall report status"""
        
        if concerning_count == 0:
            # All results are good
            return "Good job! Your health is excellent and all your test results look great. However, it's always good to go for regular checkups every 6 months to make sure you stay healthy. Keep eating well, exercising, and taking care of yourself!"
        
        elif concerning_count == 1:
            # Mostly good with one concern
            return "Overall, you're doing well with most of your health markers being good. There's just one area that needs attention, but this is very manageable. Regular checkups every 3-4 months will help monitor your progress and keep you on track to better health."
        
        elif concerning_count <= total_count // 2:
            # Some concerns but not majority
            return "Your health report shows a mix of good and concerning results. The good news is that many things are working well in your body. Focus on the areas that need improvement, and with proper care and regular checkups every 2-3 months, you can get back to optimal health."
        
        else:
            # Majority of results concerning
            return "Your health report shows several areas that need attention, but don't worry - with the right care and lifestyle changes, these can be improved. It's important to work closely with your doctor and have regular checkups every month until things improve. Remember, taking small steps every day towards better health will make a big difference."

    def _create_audio_parameter_explanation(self, test_name, test_value, test_unit, interpretation, position):
        """Create detailed audio explanation for each parameter"""
        
        # Start with parameter number and name
        audio_text = f"Parameter {position}: {test_name}. "
        
        # Add the value with unit
        if test_unit:
            audio_text += f"Your result is {test_value} {test_unit}. "
        else:
            audio_text += f"Your result is {test_value}. "
        
        # Add what this test measures
        body_part = self._get_body_part_explanation(test_name)
        audio_text += f"This test measures your {body_part}. "
        
        # Add interpretation with health implications
        if interpretation['status'] == 'good':
            audio_text += f"Your result is in the healthy range, which is excellent. {interpretation['health_implication']} "
        elif interpretation['status'] == 'a little high':
            audio_text += f"Your result is slightly higher than the ideal range. {interpretation['health_implication']} "
        elif interpretation['status'] == 'a little low':
            audio_text += f"Your result is slightly lower than the ideal range. {interpretation['health_implication']} "
        elif interpretation['status'] == 'needs attention':
            audio_text += f"Your result requires attention and should be discussed with your doctor. {interpretation['health_implication']} "
        else:
            audio_text += f"{interpretation['health_implication']} "
        
        # Add simple advice if available
        if interpretation.get('simple_advice'):
            audio_text += f"{interpretation['simple_advice']} "
        
        return audio_text

    def _create_audio_overall_summary(self, normal_count, concerning_count, total_count):
        """Create overall summary for audio"""
        
        if concerning_count == 0:
            return f"Overall, all {normal_count} parameters are in healthy ranges. This is excellent news and shows your body is functioning well."
        elif concerning_count == 1:
            return f"Overall, {normal_count} out of {total_count} parameters are healthy, with 1 parameter needing some attention. This is manageable with proper care."
        else:
            return f"Overall, {normal_count} parameters are healthy, while {concerning_count} parameters need attention. With proper medical guidance, these can be improved."

    def _get_simple_interpretation(self, test_name, test_value, test_unit):
        """Get simple interpretation with specific health implications"""
        
        try:
            value_float = float(test_value)
        except:
            return {
                'status': 'unknown',
                'health_implication': 'This test shows important information about your health.',
                'simple_advice': 'This test provides valuable health information.'
            }
        
        test_name_lower = test_name.lower()
        
        # Simple ranges for common tests with specific health implications
        if any(term in test_name_lower for term in ['glucose', 'sugar', 'blood sugar']):
            if value_float < 70:
                return {
                    'status': 'a little low',
                    'health_implication': 'Low blood sugar can make you feel weak, dizzy, or shaky and can be dangerous if it drops too much.',
                    'simple_advice': 'Eat healthy snacks when you feel weak or shaky.'
                }
            elif 70 <= value_float <= 140:
                return {
                    'status': 'good',
                    'health_implication': 'Your blood sugar is in a healthy range, which means your body is managing energy well.',
                    'simple_advice': 'Keep eating healthy foods and stay active.'
                }
            elif 140 < value_float <= 200:
                return {
                    'status': 'a little high',
                    'health_implication': 'High blood sugar can damage your blood vessels, nerves, and organs over time if not controlled.',
                    'simple_advice': 'Eat less candy and sweet things, play more outside.'
                }
            else:
                return {
                    'status': 'needs attention',
                    'health_implication': 'Very high blood sugar can lead to serious problems like diabetes, heart disease, and kidney damage.',
                    'simple_advice': 'This is important - eat very healthy foods and stay active.'
                }
        
        # Cholesterol
        elif 'cholesterol' in test_name_lower:
            if value_float < 200:
                return {
                    'status': 'good',
                    'health_implication': 'Good cholesterol levels help protect your heart and blood vessels from disease.',
                    'simple_advice': 'Your heart is happy! Keep eating good foods.'
                }
            elif 200 <= value_float <= 240:
                return {
                    'status': 'a little high',
                    'health_implication': 'High cholesterol can build up in your arteries and increase your risk of heart attacks and strokes.',
                    'simple_advice': 'Eat more fruits and vegetables, less fried food.'
                }
            else:
                return {
                    'status': 'needs attention',
                    'health_implication': 'Very high cholesterol significantly increases your risk of heart disease, heart attacks, and strokes.',
                    'simple_advice': 'Your heart needs help - eat very healthy foods and exercise.'
                }
        
        # Blood pressure
        elif any(term in test_name_lower for term in ['pressure', 'bp']):
            if '/' in test_value:
                try:
                    systolic = int(test_value.split('/')[0])
                    if systolic < 120:
                        return {
                            'status': 'good',
                            'health_implication': 'Normal blood pressure means your heart is working efficiently and your blood vessels are healthy.',
                            'simple_advice': 'Your heart is pumping just right!'
                        }
                    elif 120 <= systolic <= 140:
                        return {
                            'status': 'a little high',
                            'health_implication': 'Slightly high blood pressure puts extra strain on your heart and blood vessels, which can lead to heart problems over time.',
                            'simple_advice': 'Try to relax more and eat less salty food.'
                        }
                    else:
                        return {
                            'status': 'needs attention',
                            'health_implication': 'High blood pressure greatly increases your risk of heart attacks, strokes, kidney disease, and other serious health problems.',
                            'simple_advice': 'Your heart is working too hard.'
                        }
                except:
                    return {
                        'status': 'unknown',
                        'health_implication': 'Blood pressure shows how hard your heart is working to pump blood through your body.',
                        'simple_advice': 'This measures how your heart pumps blood.'
                    }
            else:
                if value_float < 120:
                    return {
                        'status': 'good',
                        'health_implication': 'Your blood pressure is in a healthy range, which is good for your heart and blood vessels.',
                        'simple_advice': 'Your heart pressure looks good!'
                    }
                else:
                    return {
                        'status': 'a little high',
                        'health_implication': 'Higher blood pressure can strain your heart and blood vessels over time.',
                        'simple_advice': 'Your heart pressure might be a little high.'
                    }
        
        # Hemoglobin
        elif any(term in test_name_lower for term in ['hemoglobin', 'hb']):
            if 12.0 <= value_float <= 17.5:
                return {
                    'status': 'good',
                    'health_implication': 'Good hemoglobin levels mean your blood can carry enough oxygen to all parts of your body.',
                    'simple_advice': 'Your blood is carrying oxygen well!'
                }
            elif value_float < 12.0:
                return {
                    'status': 'a little low',
                    'health_implication': 'Low hemoglobin (anemia) can make you feel tired, weak, and short of breath because your body isn\'t getting enough oxygen.',
                    'simple_advice': 'Eat foods with iron like spinach and meat to make your blood stronger.'
                }
            else:
                return {
                    'status': 'a little high',
                    'health_implication': 'High hemoglobin can make your blood thicker, which might affect blood flow.',
                    'simple_advice': 'Your blood has a lot of this protein.'
                }
        
        # HbA1c
        elif any(term in test_name_lower for term in ['hba1c', 'a1c']):
            if value_float < 5.7:
                return {
                    'status': 'good',
                    'health_implication': 'Your blood sugar has been well controlled over the past 2-3 months, which protects your organs from damage.',
                    'simple_advice': 'Your long-term blood sugar control is excellent!'
                }
            elif 5.7 <= value_float <= 6.4:
                return {
                    'status': 'a little high',
                    'health_implication': 'Your blood sugar has been higher than normal for months, which increases your risk of developing diabetes and organ damage.',
                    'simple_advice': 'Your blood sugar has been a little high. Eat healthier foods and exercise more.'
                }
            else:
                return {
                    'status': 'needs attention',
                    'health_implication': 'Your blood sugar has been dangerously high for months, which can cause serious damage to your heart, kidneys, eyes, and nerves.',
                    'simple_advice': 'Your blood sugar has been too high for too long.'
                }
        
        # Creatinine
        elif 'creatinine' in test_name_lower:
            if 0.6 <= value_float <= 1.3:
                return {
                    'status': 'good',
                    'health_implication': 'Normal creatinine levels show that your kidneys are filtering waste from your blood properly.',
                    'simple_advice': 'Your kidneys are cleaning your blood well!'
                }
            elif value_float > 1.3:
                return {
                    'status': 'a little high',
                    'health_implication': 'High creatinine suggests your kidneys may not be filtering waste properly, which can lead to kidney disease.',
                    'simple_advice': 'Your kidneys might need help. Drink more water.'
                }
            else:
                return {
                    'status': 'a little low',
                    'health_implication': 'This test shows how well your kidneys are working to clean waste from your blood.',
                    'simple_advice': 'This shows how your kidneys work.'
                }
        
        # Thyroid tests
        elif any(term in test_name_lower for term in ['tsh', 'thyroid']):
            if 0.4 <= value_float <= 4.0:
                return {
                    'status': 'good',
                    'health_implication': 'Normal thyroid levels mean your metabolism, energy, and body temperature are well regulated.',
                    'simple_advice': 'Your thyroid gland is working normally!'
                }
            elif value_float > 4.0:
                return {
                    'status': 'a little high',
                    'health_implication': 'High TSH suggests your thyroid is underactive, which can make you feel tired, cold, and cause weight gain.',
                    'simple_advice': 'Your thyroid might be working slowly.'
                }
            else:
                return {
                    'status': 'a little low',
                    'health_implication': 'Low TSH suggests your thyroid is overactive, which can cause rapid heartbeat, weight loss, and anxiety.',
                    'simple_advice': 'Your thyroid might be working too fast.'
                }
        
        # Vitamin D
        elif any(term in test_name_lower for term in ['vitamin d', 'vit d']):
            if value_float >= 30:
                return {
                    'status': 'good',
                    'health_implication': 'Good vitamin D levels help keep your bones strong and support your immune system.',
                    'simple_advice': 'You have enough vitamin D for strong bones!'
                }
            elif 20 <= value_float < 30:
                return {
                    'status': 'a little low',
                    'health_implication': 'Low vitamin D can weaken your bones and make you more likely to get sick.',
                    'simple_advice': 'Spend more time in sunlight and eat foods with vitamin D.'
                }
            else:
                return {
                    'status': 'needs attention',
                    'health_implication': 'Very low vitamin D can cause bone pain, muscle weakness, and increase your risk of fractures.',
                    'simple_advice': 'You need more vitamin D. Take supplements.'
                }
        
        # Default for unknown tests
        return {
            'status': 'unknown',
            'health_implication': f'This test measures important aspects of your {self._get_body_part_explanation(test_name)} and helps doctors understand your health.',
            'simple_advice': f'This test shows how your {self._get_body_part_explanation(test_name)} is working.'
        }

    def _get_body_part_explanation(self, test_name):
        """Get simple explanation of what body part the test is checking"""
        test_name_lower = test_name.lower()
        
        if any(term in test_name_lower for term in ['glucose', 'sugar']):
            return "blood sugar and energy system"
        elif 'cholesterol' in test_name_lower:
            return "heart and blood vessels"
        elif any(term in test_name_lower for term in ['pressure', 'bp']):
            return "heart and blood flow"
        elif any(term in test_name_lower for term in ['hemoglobin', 'hb']):
            return "blood and oxygen carrying"
        elif 'creatinine' in test_name_lower:
            return "kidneys and waste cleaning"
        elif any(term in test_name_lower for term in ['thyroid', 'tsh']):
            return "thyroid gland and energy control"
        elif 'vitamin' in test_name_lower:
            return "vitamin levels and nutrition"
        elif 'iron' in test_name_lower:
            return "iron levels and blood strength"
        else:
            return "body"

    def _identify_simple_risk_factors(self, test_results):
        """Identify risk factors in simple language"""
        
        simple_risks = []
        
        for test in test_results:
            test_name = test['name'].lower()
            try:
                value = float(test['value'])
                
                if any(term in test_name for term in ['glucose', 'sugar']) and value > 140:
                    simple_risks.append("too much sugar in blood")
                elif 'cholesterol' in test_name and value > 200:
                    simple_risks.append("heart needs better food")
                elif 'pressure' in test_name and '/' in test['value']:
                    systolic = int(test['value'].split('/')[0])
                    if systolic > 130:
                        simple_risks.append("heart working too hard")
                elif 'hemoglobin' in test_name and value < 12:
                    simple_risks.append("blood needs more iron")
                    
            except:
                continue
        
        return simple_risks

    def _generate_simple_recommendations(self, test_results, patient_info, concerning_count):
        """Generate simple recommendations anyone can follow"""
        
        simple_recs = []
        
        # Basic healthy living advice
        if concerning_count > 0:
            simple_recs.extend([
                "Eat more fruits and vegetables every day",
                "Drink lots of water instead of sugary drinks",
                "Play outside or exercise for 30 minutes daily",
                "Sleep 8-9 hours every night"
            ])
        else:
            simple_recs.extend([
                "Keep eating healthy foods like you are doing",
                "Keep playing and being active",
                "Keep sleeping well every night"
            ])
        
        # Test-specific simple advice
        for test in test_results:
            test_name = test['name'].lower()
            try:
                value = float(test['value'])
                
                if any(term in test_name for term in ['glucose', 'sugar']) and value > 140:
                    simple_recs.append("Eat less candy, cookies, and sweet things")
                elif 'cholesterol' in test_name and value > 200:
                    simple_recs.append("Eat fish, nuts, and avoid fried foods")
                elif 'hemoglobin' in test_name and value < 12:
                    simple_recs.append("Eat spinach, meat, and foods with iron")
                    
            except:
                continue
        
        return simple_recs[:6]  # Limit to 6 simple recommendations

    def _generate_simple_risk_assessment(self, concerning_count, normal_count):
        """Generate simple risk assessment"""
        
        if concerning_count == 0:
            return "You are healthy and strong! Keep doing what you're doing to stay this way."
        elif concerning_count == 1:
            return "You are mostly healthy with one thing to work on. With some changes, you can be even healthier!"
        else:
            return f"Your body needs some extra care. With healthy choices, you can feel much better!"

    def _generate_simple_followup(self, concerning_count):
        """Generate simple follow-up advice"""
        
        if concerning_count == 0:
            return "Visit your doctor in 6 months for a regular check-up to make sure you stay healthy."
        elif concerning_count == 1:
            return "Visit your doctor in 2-4 weeks to talk about how to make that one thing better."
        else:
            return "Visit your doctor soon (in 1-2 weeks) so they can help you with the things that need attention."

    def _get_simple_age_advice(self, age, concerning_count):
        """Get age-appropriate simple advice"""
        
        if age < 18:
            if concerning_count > 0:
                return "Growing kids need extra healthy food and lots of play time to help their bodies get strong!"
            else:
                return "You're growing up healthy and strong! Keep eating good food and playing every day."
        elif age < 40:
            if concerning_count > 0:
                return "Taking care of your health now will help you feel great for many years!"
            else:
                return "You're doing great! Keep up the healthy habits to stay strong."
        elif age < 60:
            if concerning_count > 0:
                return "It's never too late to make healthy changes. Your body will thank you!"
            else:
                return "Excellent! You're taking good care of yourself. Keep it up!"
        else:
            if concerning_count > 0:
                return "Staying healthy is very important at your age."
            else:
                return "Wonderful! You're aging healthily. Continue your good habits and regular check-ups."

    def _extract_structured_data(self, text, language):
        """Extract structured data from medical text"""
        return self._extract_structured_data_comprehensive(text, language)

    def _combine_analyses(self, comprehensive_analysis, structured_data, language):
        """Combine AI-generated analysis with structured data"""
        if comprehensive_analysis.get('success'):
            result = comprehensive_analysis.copy()
            result['structured_data'] = structured_data
            return result
        else:
            return self._create_simple_comprehensive_analysis(structured_data, "", language)

    def _get_error_message(self, language):
        """Get error message in specified language"""
        error_messages = {
            'en-IN': "Unable to process the medical report. Please try again or consult with your healthcare provider.",
            'hi-IN': "मेडिकल रिपोर्ट को प्रोसेस करने में असमर्थ। कृपया पुनः प्रयास करें या अपने डॉक्टर से सलाह लें।"
        }
        return error_messages.get(language, error_messages['en-IN'])
