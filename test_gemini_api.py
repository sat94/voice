#!/usr/bin/env python3
"""Test de Google Gemini via l'API"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_gemini_question():
    """Test avec une question qui devrait aller vers Gemini"""
    
    # Question psychologique complexe (devrait aller vers Gemini)
    prompt = "Pourquoi est-ce que je ressens de l'anxiété avant chaque rendez-vous ? Peux-tu m'expliquer les mécanismes psychologiques ?"
    
    print(f"🧪 Test question pour Gemini: {prompt}")
    
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
            
            if "google_gemini" in ai_provider:
                print("🎉 Google Gemini fonctionne !")
            elif "demo_mode" in ai_provider:
                print("⚠️ Mode démo utilisé")
            else:
                print(f"🤔 Fournisseur inattendu: {ai_provider}")
                
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_routing():
    """Test du routage"""
    prompt = "Qu'est-ce que l'anxiété d'un point de vue psychologique ?"
    
    try:
        response = requests.post(
            f"{API_URL}/ia/routing-test", 
            headers=headers, 
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n🎯 Routage pour: {prompt}")
            print(f"✅ Catégorie: {result.get('category')}")
            print(f"✅ IA recommandée: {result.get('recommended_ai')}")
        else:
            print(f"❌ Erreur routage: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur routage: {e}")

if __name__ == "__main__":
    test_routing()
    test_gemini_question()
