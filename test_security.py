#!/usr/bin/env python3
"""
Script de test pour vérifier la sécurité de l'API MeetVoice TTS
"""

import requests
import json

# Configuration
API_BASE_URL = "http://184.174.39.187:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"
WRONG_API_KEY = "wrong_key_123"

def test_with_api_key(api_key, description):
    """Teste l'API avec une clé donnée"""
    print(f"\n🔍 {description}")
    print("-" * 50)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test de l'endpoint racine
    try:
        response = requests.get(f"{API_BASE_URL}/", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Succès: {data.get('message', data.get('api', 'API accessible'))}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_without_api_key():
    """Teste l'API sans clé"""
    print(f"\n🔍 Test sans clé API")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_security_endpoint():
    """Teste l'endpoint de sécurité"""
    print(f"\n🔍 Test endpoint de sécurité")
    print("-" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/security/test", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sécurité validée!")
            print(f"   IP détectée: {data.get('your_ip')}")
            print(f"   IP autorisée: {data.get('authorized_ip')}")
            print(f"   Accès accordé: {data.get('access_granted')}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_question_endpoint():
    """Teste un endpoint de question"""
    print(f"\n🔍 Test endpoint question")
    print("-" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/inscription/question/1", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Question 1 accessible (fichier audio retourné)")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Taille: {len(response.content)} bytes")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    print("🔒 TEST DE SÉCURITÉ API MEETVOICE TTS")
    print("=" * 60)
    
    # Test sans clé API
    test_without_api_key()
    
    # Test avec mauvaise clé API
    test_with_api_key(WRONG_API_KEY, "Test avec mauvaise clé API")
    
    # Test avec bonne clé API
    test_with_api_key(API_KEY, "Test avec bonne clé API")
    
    # Test endpoint de sécurité
    test_security_endpoint()
    
    # Test endpoint de question
    test_question_endpoint()
    
    print(f"\n🎯 RÉSUMÉ")
    print("=" * 60)
    print("✅ L'API devrait être accessible uniquement avec:")
    print(f"   - IP autorisée: 81.220.68.196")
    print(f"   - Clé API: {API_KEY}")
    print("❌ Tous les autres accès devraient être refusés")
