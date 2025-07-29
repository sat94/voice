#!/usr/bin/env python3
"""Test simple de Google Gemini"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini():
    """Test direct de Google Gemini"""
    try:
        google_key = os.getenv('GOOGLE_API_KEY')
        print(f"Clé Google: {google_key[:10]}..." if google_key else "Pas de clé")
        
        if not google_key:
            print("❌ Pas de clé Google API")
            return
        
        genai.configure(api_key=google_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "Réponds en français : Comment aborder quelqu'un qu'on trouve attirant ?"
        
        print(f"🧪 Test Gemini avec: {prompt}")
        response = model.generate_content(prompt)
        print(f"✅ Réponse: {response.text}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_gemini()
