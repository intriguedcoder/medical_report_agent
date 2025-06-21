class MedicalKnowledgeBase:
    def __init__(self):
        self.normal_ranges = {
            'glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL', 'hindi': 'ग्लूकोज'},
            'hemoglobin': {'min': 12, 'max': 15, 'unit': 'g/dL', 'hindi': 'हीमोग्लोबिन'},
            'cholesterol': {'min': 0, 'max': 200, 'unit': 'mg/dL', 'hindi': 'कोलेस्ट्रॉल'},
            'blood_pressure_systolic': {'min': 90, 'max': 120, 'unit': 'mmHg', 'hindi': 'रक्तचाप'},
            'blood_pressure_diastolic': {'min': 60, 'max': 80, 'unit': 'mmHg', 'hindi': 'रक्तचाप'},
            'wbc': {'min': 4000, 'max': 11000, 'unit': 'cells/μL', 'hindi': 'श्वेत रक्त कोशिका'},
            'rbc': {'min': 4.5, 'max': 5.5, 'unit': 'million cells/μL', 'hindi': 'लाल रक्त कोशिका'}
        }
        
        self.critical_thresholds = {
            'glucose': {'critical_high': 200, 'critical_low': 50},
            'hemoglobin': {'critical_low': 8},
            'blood_pressure_systolic': {'critical_high': 180, 'critical_low': 70}
        }
        
        self.medical_terms = {
            'diabetes': 'मधुमेह',
            'hypertension': 'उच्च रक्तचाप',
            'anemia': 'खून की कमी',
            'normal': 'सामान्य',
            'high': 'ज्यादा',
            'low': 'कम'
        }
    
    def get_normal_range(self, parameter):
        return self.normal_ranges.get(parameter.lower(), None)
    
    def is_critical(self, parameter, value):
        thresholds = self.critical_thresholds.get(parameter.lower(), {})
        if 'critical_high' in thresholds and value > thresholds['critical_high']:
            return True
        if 'critical_low' in thresholds and value < thresholds['critical_low']:
            return True
        return False
    
    def get_hindi_term(self, english_term):
        return self.medical_terms.get(english_term.lower(), english_term)
