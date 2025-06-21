from flask import Blueprint, render_template, session, jsonify, request
from utils.translations import UI_TRANSLATIONS, AUDIO_LANGUAGES
from utils.helpers import get_ui_language, get_audio_language

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Enhanced web interface with audio language selection"""
    ui_lang = get_ui_language()
    audio_lang = get_audio_language()
    ui_text = UI_TRANSLATIONS.get(ui_lang, UI_TRANSLATIONS['en-IN'])
    
    return render_template('index.html', 
                         ui_text=ui_text,
                         current_ui_lang=ui_lang,
                         current_audio_lang=audio_lang,
                         audio_languages=AUDIO_LANGUAGES,
                         ui_text_json=jsonify(ui_text).get_data(as_text=True))

@main_bp.route('/set_ui_language', methods=['POST'])
def set_ui_language():
    """Set UI language in session"""
    data = request.get_json()
    language = data.get('language', 'en-IN')
    
    if language == 'auto':
        language = 'en-IN'
    
    session['ui_language'] = language
    # If audio language is not set, default to UI language
    if 'audio_language' not in session:
        session['audio_language'] = language
    
    return jsonify({'success': True, 'language': language})

@main_bp.route('/set_audio_language', methods=['POST'])
def set_audio_language():
    """Set audio language in session"""
    data = request.get_json()
    language = data.get('language', get_ui_language())
    
    session['audio_language'] = language
    return jsonify({'success': True, 'audio_language': language})

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Swasthya Saathi Lite',
        'version': '1.0.0'
    })
