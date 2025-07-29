#!/usr/bin/env python3
"""Test de la correction DeepInfra"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_deepinfra_question():
    """Test avec une question qui devrait aller vers DeepInfra"""
    
    # Question pratique de séduction (devrait aller vers DeepInfra)
    prompt = "Que faire concrètement pour draguer une fille dans un café ?"
    
    print(f"🧪 Test question pour DeepInfra: {prompt}")
    
    try:
        response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            category = result.get('category')
            ai_provider = result.get('ai_provider')
            response_text = result.get('response')
            
            print(f"✅ Catégorie: {category}")
            print(f"✅ Fournisseur: {ai_provider}")
            print(f"✅ Réponse: {response_text[:200]}...")
            
            if "deepinfra" in ai_provider:
                print("🎉 DeepInfra fonctionne !")
            elif "google_gemini" in ai_provider:
                print("⚠️ Fallback vers Gemini utilisé")
            elif "demo_mode" in ai_provider:
                print("⚠️ Mode démo utilisé")
            else:
                print(f"🤔 Fournisseur inattendu: {ai_provider}")
                
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_image_generation():
    """Test de la génération d'images"""
    print("\n🎨 Test de génération d'image")
    
    prompt = "Photo de profil professionnelle pour site de rencontre"
    
    try:
        response = requests.post(
            f"{API_URL}/ia/image-simple", 
            headers=headers, 
            json={
                "prompt": prompt,
                "style": "portrait",
                "size": "512x512"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print(f"✅ Prompt original: {result.get('original_prompt')}")
                print(f"✅ Prompt optimisé: {result.get('optimized_prompt')}")
                print(f"✅ Catégorie: {result.get('category')}")
                print(f"✅ Style: {result.get('style')}")
                print(f"✅ Taille: {result.get('size')}")
                print(f"✅ Temps: {result.get('processing_time')}s")
                
                image_data = result.get('image')
                if image_data:
                    print(f"✅ Image générée: {len(image_data)} caractères (base64)")
                    print("🎉 Génération d'image réussie !")
                else:
                    print("❌ Pas de données d'image")
            else:
                print(f"❌ Erreur génération: {result.get('error')}")
        else:
            print(f"❌ Erreur API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_deepinfra_question()
    test_image_generation()
