import logging
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client untuk mengelola koneksi dan model Gemini AI"""
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.apikey_gemini)
        self.model = None
        self.model_used = None
    
    def get_model(self):
        """Mendapatkan model Gemini yang tersedia dengan fallback"""
        if self.model is not None:
            return self.model, self.model_used
        
        model_names = [
            'gemini-2.5-pro',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_used = model_name
                logger.info(f"✅ Menggunakan model: {model_name}")
                return self.model, self.model_used
            except Exception as e:
                logger.warning(f"Model {model_name} tidak tersedia: {e}")
                continue
        
        raise Exception("Tidak ada model Gemini yang tersedia. Pastikan API key valid dan model tersedia.")
    
    def generate_content(self, prompt: str):
        """Generate content menggunakan model Gemini"""
        model, _ = self.get_model()
        return model.generate_content(prompt)
    
    def generate_content_stream(self, prompt: str):
        """Generate content dengan streaming menggunakan model Gemini"""
        model, _ = self.get_model()
        return model.generate_content(prompt, stream=True)
    
    @property
    def model_name(self):
        """Mendapatkan nama model yang digunakan"""
        if self.model_used is None:
            self.get_model()
        return self.model_used

