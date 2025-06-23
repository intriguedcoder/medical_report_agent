# 🩺Health-Partner: A Medical Report AI Analyzer

**AI-powered, multilingual, patient-friendly medical report analysis and explanation system.**

---

## 🚩 What Problem Does It Solve?

- **Medical reports are hard to understand:** Most people struggle with medical jargon, numbers, and technical terms.
- **Language and literacy barriers:** Many patients in India and elsewhere do not read English or understand medical terms.
- **Accessibility:** Visually impaired, elderly, or low-literacy users need audio explanations.
- **Actionable advice:** Patients rarely get clear, actionable next steps from their reports.

> **This project democratizes medical knowledge, making reports understandable, accessible, and actionable for everyone.**

---

## ✨ Key Features

- **🖼️ Image-to-Text:** Extracts text from medical report images using advanced OCR.
- **🤖 AI Medical Analysis:** Interprets test results, explains their meaning, and summarizes risks in plain language.
- **🌐 Multilingual Support:** Translates explanations into 11+ Indian languages using Sarvam-Translate.
- **🔊 Voice Summaries:** Generates natural-sounding audio explanations in the user's language using Sarvam TTS.
- **✅ Actionable Recommendations:** Provides simple, practical health advice and follow-up suggestions.
- **👨‍⚕️ Patient-Centric:** Tailors explanations for age, context, and language.
- **🛠️ API-First:** Easily integrates with web/mobile apps or hospital systems.
- **⚡ Scalable Automation:** Supports advanced workflows and patient follow-up via Bhindi AI orchestration.

---

## 🏗️ How It Works

1. **Image Upload & Validation**
   - User uploads a medical report image via the web/app or API.
   - File is validated for type, size, and uniqueness.

2. **OCR Extraction**
   - The `OCRAgent` uses Tesseract (with multiple medical-optimized configs) to extract and clean text from the image.

3. **Language Detection**
   - The system detects the report's language to support multilingual output.

4. **Medical Analysis**
   - The `MedicalAnalyzerAgent`:
     - Extracts test names, values, units, and patient info.
     - Interprets each test (good, high, low, needs attention).
     - Explains health implications and risks in simple language.
     - Generates a summary, detailed analysis, recommendations, and follow-up actions.

5. **Translation**
   - The `TranslationAgent` uses Sarvam-Translate to localize the analysis and advice into the user's chosen language.

6. **Voice Synthesis**
   - The `VoiceAgent` uses Sarvam TTS to generate a clear, concise audio summary in the user's language and a native-sounding voice.

7. **Response Delivery**
   - The orchestrator assembles the translated text and audio.
   - The user receives:
     - A readable summary and detailed explanation.
     - An audio file for listening.
     - Clear, actionable health advice.

---

## 📦 Integration & Scalability

- **API-First Design:** Seamless integration with web/mobile apps or hospital systems.
- **Automated Workflows:** Supports patient follow-up and advanced orchestration via Bhindi AI.

---

## 👥 Who Is This For?

- Patients and families seeking to understand their medical reports.
- Healthcare providers aiming to improve patient communication.
- Developers building accessible health-tech solutions.



**Empowering patients, one report at a time.**
