#!/usr/bin/env python3
"""Test script pour l'endpoint /ia"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_ia_simple():
    """Test de l'endpoint /ia/simple"""
    print("🧪 Test de l'endpoint /ia/simple")
    
    data = {
        "prompt": "Je suis timide, comment aborder une fille qui me plaît ?"
    }
    
    try:
        response = requests.post(f"{API_URL}/ia/simple", headers=headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Catégorie détectée: {result.get('category')}")
            print(f"✅ Fournisseur IA: {result.get('ai_provider')}")
            print(f"✅ Réponse: {result.get('response')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_ia_complete():
    """Test de l'endpoint /ia complet"""
    print("\n🧪 Test de l'endpoint /ia complet")
    
    data = {
        "prompt": "Comment gérer mon stress avant un rendez-vous ?",
        "include_prompt_audio": False  # Pour éviter les gros fichiers audio
    }
    
    try:
        response = requests.post(f"{API_URL}/ia", headers=headers, json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Catégorie détectée: {result.get('category')}")
            print(f"✅ Fournisseur IA: {result.get('ai_provider')}")
            print(f"✅ Réponse: {result.get('response')}")
            print(f"✅ Audio de réponse: {'Oui' if result.get('response_audio') else 'Non'}")
            print(f"✅ Temps de traitement: {result.get('processing_time')}s")
        else:
            print(f"❌ Erreur: {response.text}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_ia_simple()
    test_ia_complete()
