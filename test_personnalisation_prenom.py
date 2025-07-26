#!/usr/bin/env python3
"""
Test de la personnalisation avec le prénom
"""

import requests

def test_personnalisation():
    url = "http://localhost:8012/ia"
    
    print("👤 TEST PERSONNALISATION AVEC PRÉNOM")
    print("=" * 60)
    
    # Test sans prénom
    print("\n1. SANS PRÉNOM:")
    print("-" * 30)
    
    try:
        response = requests.post(url, json={
            "prompt": "Bonjour Sophie !",
            "include_audio": False
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RÉPONSE: {result['response']}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec prénom
    print("\n2. AVEC PRÉNOM 'Marc':")
    print("-" * 30)
    
    try:
        response = requests.post(url, json={
            "prompt": "Bonjour Sophie !",
            "prenom": "Marc",
            "include_audio": False
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RÉPONSE: {result['response']}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test heure avec prénom
    print("\n3. HEURE AVEC PRÉNOM 'Julie':")
    print("-" * 30)
    
    try:
        response = requests.post(url, json={
            "prompt": "Quelle heure il est ?",
            "prenom": "Julie",
            "include_audio": False
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RÉPONSE: {result['response']}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test question complexe avec prénom
    print("\n4. QUESTION COMPLEXE AVEC PRÉNOM 'Alex':")
    print("-" * 30)
    
    try:
        response = requests.post(url, json={
            "prompt": "Comment aborder une fille qui me plaît ?",
            "prenom": "Alex",
            "include_audio": False
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RÉPONSE: {result['response'][:200]}...")
            
            # Vérifier si le prénom est utilisé
            if "Alex" in result['response']:
                print("🎯 PRÉNOM UTILISÉ DANS LA RÉPONSE !")
            else:
                print("⚠️ Prénom pas utilisé dans cette réponse")
                
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_personnalisation()
