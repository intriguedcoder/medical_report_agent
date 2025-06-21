import requests
import json
import os
import time
from typing import Dict, Any, Optional

class BhindiOrchestrator:
    def __init__(self, external_agent_api_key: str = None, base_url: str = None):
        self.external_agent_api_key = external_agent_api_key or os.getenv('BHINDI_EXTERNAL_AGENT_API_KEY')
        # Try different possible API endpoints for external agents
        self.bhindi_api_base = base_url or os.getenv('BHINDI_API_BASE', "https://api.bhindi.io")
        
        if not self.external_agent_api_key:
            raise ValueError("Bhindi External Agent API key is required")
        
        self.workflow_templates = {
            'medical_analysis': 'medical_report_workflow',
            'patient_followup': 'patient_care_workflow',
            'report_generation': 'comprehensive_report_workflow'
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "BhindiOrchestrator/1.0",
        })

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for external agent"""
        return {
            "Authorization": f"Bearer {self.external_agent_api_key}",
            "X-Agent-Type": "external",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and authentication"""
        try:
            response = self.session.get(
                f"{self.bhindi_api_base}/health",
                headers=self._get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful"}
            elif response.status_code == 401:
                return {"success": False, "error": "Invalid API key"}
            else:
                return {"success": False, "error": f"API returned status {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to Bhindi API"}
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}

    def orchestrate_medical_workflow(self, ocr_result: Dict, user_language: str = "en", user_preferences: Dict = None) -> Dict[str, Any]:
        """Use Bhindi AI to orchestrate the complete medical analysis workflow"""
        
        if user_preferences is None:
            user_preferences = {}
        
        # Enhanced workflow configuration
        workflow_config = {
            "workflow_name": "medical_report_analysis",
            "workflow_id": f"medical_{int(time.time())}",
            "external_agent_id": "medical_orchestrator",
            "agents": [
                {
                    "agent_id": "data_processor_1",
                    "agent_type": "data_processor",
                    "task": "process_medical_text",
                    "input_data": {
                        "text": ocr_result.get('cleaned_text', ''),
                        "metadata": ocr_result.get('metadata', {})
                    },
                    "config": {
                        "language": user_language,
                        "processing_mode": "medical"
                    }
                },
                {
                    "agent_id": "analyzer_1",
                    "agent_type": "sarvam_analyzer", 
                    "task": "generate_comprehensive_analysis",
                    "depends_on": ["data_processor_1"],
                    "config": {
                        "model": "sarvam-m",
                        "language": user_language,
                        "analysis_depth": "comprehensive"
                    }
                },
                {
                    "agent_id": "formatter_1",
                    "agent_type": "report_formatter",
                    "task": "format_patient_report", 
                    "depends_on": ["analyzer_1"],
                    "config": {
                        "format": user_preferences.get("format", "patient_friendly"),
                        "language": user_language,
                        "include_recommendations": True
                    }
                }
            ],
            "output_config": {
                "format": "comprehensive_medical_report",
                "include_audio": user_preferences.get("include_audio", False),
                "language": user_language
            }
        }
        
        # Add voice generation if requested
        if user_preferences.get("include_audio", False):
            workflow_config["agents"].append({
                "agent_id": "voice_generator_1",
                "agent_type": "voice_generator",
                "task": "create_audio_summary",
                "depends_on": ["formatter_1"],
                "config": {
                    "voice_model": "sarvam_tts",
                    "language": user_language,
                    "voice_style": "professional"
                }
            })
        
        return self._execute_bhindi_workflow(workflow_config)

    def _execute_bhindi_workflow(self, workflow_config: Dict) -> Dict[str, Any]:
        """Execute the workflow using Bhindi AI with proper error handling"""
        
        # Validate workflow first
        if not self._validate_workflow_config(workflow_config):
            return {"success": False, "error": "Invalid workflow configuration"}
        
        try:
            # Try different endpoint patterns
            endpoints_to_try = [
                f"{self.bhindi_api_base}/api/v1/workflows/execute",
                f"{self.bhindi_api_base}/v1/workflows/execute",
                f"{self.bhindi_api_base}/workflows/execute",
                f"{self.bhindi_api_base}/external/workflows/execute"
            ]
            
            last_error = None
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.post(
                        endpoint,
                        json=workflow_config,
                        headers=self._get_auth_headers(),
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "success": True,
                            "workflow_id": result.get("workflow_id"),
                            "data": result,
                            "endpoint_used": endpoint
                        }
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        break
                        
                except requests.exceptions.ConnectionError:
                    continue  # Try next endpoint
                except Exception as e:
                    last_error = str(e)
                    continue
            
            return {
                "success": False, 
                "error": last_error or "All API endpoints failed",
                "tried_endpoints": endpoints_to_try
            }
                
        except Exception as e:
            return {"success": False, "error": f"Workflow execution error: {str(e)}"}

    def _validate_workflow_config(self, config: Dict) -> bool:
        """Validate workflow configuration"""
        required_fields = ['workflow_name', 'agents']
        
        if not all(field in config for field in required_fields):
            return False
        
        if not isinstance(config['agents'], list) or len(config['agents']) == 0:
            return False
        
        # Validate agent dependencies
        agent_ids = [agent.get('agent_id') for agent in config['agents']]
        for agent in config['agents']:
            if 'depends_on' in agent:
                if not all(dep in agent_ids for dep in agent['depends_on']):
                    return False
        
        return True

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a running workflow"""
        try:
            response = self.session.get(
                f"{self.bhindi_api_base}/workflows/{workflow_id}/status",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "status": response.json()}
            else:
                return {"success": False, "error": f"Status check failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Status check error: {str(e)}"}

    def create_patient_followup_workflow(self, analysis_result: Dict, patient_contact: str) -> Dict[str, Any]:
        """Create automated follow-up workflow for patients"""
        
        followup_config = {
            "workflow_name": "patient_followup_automation",
            "workflow_id": f"followup_{int(time.time())}",
            "trigger": "medical_analysis_complete",
            "external_agent_id": "medical_orchestrator",
            "agents": [
                {
                    "agent_id": "scheduler_1",
                    "agent_type": "scheduler",
                    "task": "schedule_followup_reminder",
                    "config": {
                        "reminder_time": "+7 days",
                        "contact_method": "whatsapp",
                        "patient_contact": patient_contact
                    }
                },
                {
                    "agent_id": "content_generator_1",
                    "agent_type": "content_generator",
                    "task": "create_followup_message",
                    "depends_on": ["scheduler_1"],
                    "config": {
                        "template": "health_checkup_reminder",
                        "personalization": analysis_result.get('recommendations', []),
                        "language": analysis_result.get('language', 'en')
                    }
                }
            ],
            "output_config": {
                "format": "followup_schedule",
                "notification_enabled": True
            }
        }
        
        return self._execute_bhindi_workflow(followup_config)

    def __del__(self):
        """Clean up session"""
        if hasattr(self, 'session'):
            self.session.close()


# Usage example
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = BhindiOrchestrator(
        external_agent_api_key="your_external_agent_api_key_here"
    )
    
    # Test connection first
    connection_test = orchestrator.test_connection()
    print(f"Connection test: {connection_test}")
    
    if connection_test.get("success"):
        # Example OCR result
        ocr_result = {
            "cleaned_text": "Patient medical report text here...",
            "metadata": {"document_type": "medical_report", "date": "2025-06-21"}
        }
        
        # Execute medical workflow
        result = orchestrator.orchestrate_medical_workflow(
            ocr_result=ocr_result,
            user_language="en",
            user_preferences={"format": "detailed", "include_audio": True}
        )
        
        print(f"Workflow result: {result}")
        
        # If successful, check status
        if result.get("success") and result.get("workflow_id"):
            status = orchestrator.get_workflow_status(result["workflow_id"])
            print(f"Workflow status: {status}")
