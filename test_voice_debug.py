#!/usr/bin/env python3
"""Debug de la synthèse vocale"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_tts_only():
    """Test de l'endpoint TTS seul"""
    print("🔊 Test de l'endpoint TTS seul")
    
    try:
        response = requests.post(
            f"{API_URL}/tts", 
            headers=headers, 
            json={
                "text": "Bonjour, test de synthèse vocale",
                "voice_id": "denise"
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ TTS fonctionne")
            print(f"✅ Audio généré: {'Oui' if result.get('audio') else 'Non'}")
            if result.get('audio'):
                audio_size = len(result.get('audio'))
                print(f"✅ Taille audio: {audio_size} caractères")
        else:
            print(f"❌ Erreur TTS: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_ia_with_voice():
    """Test de l'endpoint IA avec synthèse vocale"""
    print("\n🤖🔊 Test de l'endpoint IA avec voix")
    
    try:
        response = requests.post(
            f"{API_URL}/ia", 
            headers=headers, 
            json={
                "prompt": "Comment être confiant ?",
                "include_prompt_audio": False,
                "voice": "denise"
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ IA répond: {result.get('response', '')[:100]}...")
            print(f"✅ Audio de réponse: {'Oui' if result.get('response_audio') else 'Non'}")
            
            if result.get('response_audio'):
                audio_size = len(result.get('response_audio'))
                print(f"✅ Taille audio: {audio_size} caractères")
                
                # Sauvegarder l'audio pour test
                import base64
                audio_data = base64.b64decode(result.get('response_audio'))
                with open('test_ia_voice.mp3', 'wb') as f:
                    f.write(audio_data)
                print("✅ Audio sauvegardé: test_ia_voice.mp3")
            else:
                print("❌ Pas d'audio généré")
        else:
            print(f"❌ Erreur IA: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_ia_simple():
    """Test de l'endpoint IA simple (sans voix)"""
    print("\n🤖 Test de l'endpoint IA simple")
    
    try:
        response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={
                "prompt": "Donne-moi un conseil rapide pour être plus confiant"
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ IA répond: {result.get('response', '')[:150]}...")
            print(f"✅ Fournisseur: {result.get('ai_provider')}")
        else:
            print(f"❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_voices_list():
    """Test de la liste des voix"""
    print("\n🎤 Test de la liste des voix")
    
    try:
        response = requests.get(f"{API_URL}/voices")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Voix disponibles: {len(result.get('voices', []))}")
            
            # Afficher quelques voix françaises
            french_voices = [v for v in result.get('voices', []) if 'fr' in v.get('locale', '').lower()]
            print(f"✅ Voix françaises: {len(french_voices)}")
            
            for voice in french_voices[:3]:
                print(f"   - {voice.get('name')} ({voice.get('gender')})")
        else:
            print(f"❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_voices_list()
    test_tts_only()
    test_ia_simple()
    test_ia_with_voice()
    
    print("\n🎉 Tests de debug terminés !")
    print("💡 Vérifiez les fichiers audio générés")
