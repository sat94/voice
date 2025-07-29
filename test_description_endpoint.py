#!/usr/bin/env python3
"""Test de l'endpoint /description pour générer des descriptions de profil"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_description_basic():
    """Test basique de génération de description"""
    print("📝 Test basique de génération de description")
    
    try:
        response = requests.post(
            f"{API_URL}/description", 
            headers=headers, 
            json={
                "user_info": {},
                "style": "attractif",
                "length": "moyen"
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print(f"✅ Description générée:")
                print(f"   Style: {result.get('style')}")
                print(f"   Longueur: {result.get('length')}")
                print(f"   IA utilisée: {result.get('ai_provider')}")
                print(f"   Temps: {result.get('processing_time')}s")
                print(f"   Description: {result.get('description')}")
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_description_with_info():
    """Test avec informations utilisateur"""
    print("\n👤 Test avec informations utilisateur")
    
    user_profiles = [
        {
            "name": "Profil homme sportif",
            "data": {
                "user_info": {
                    "age": 28,
                    "interests": ["sport", "voyage", "cuisine"],
                    "profession": "ingénieur",
                    "personality": ["drôle", "aventurier", "loyal"],
                    "relationship_goals": "relation sérieuse"
                },
                "style": "attractif",
                "length": "moyen"
            }
        },
        {
            "name": "Profil femme artistique",
            "data": {
                "user_info": {
                    "age": 25,
                    "interests": ["art", "musique", "lecture"],
                    "profession": "graphiste",
                    "personality": ["créative", "sensible", "indépendante"],
                    "relationship_goals": "rencontres ouvertes"
                },
                "style": "mystérieux",
                "length": "court"
            }
        }
    ]
    
    for profile in user_profiles:
        print(f"\n🎯 {profile['name']}:")
        
        try:
            response = requests.post(
                f"{API_URL}/description", 
                headers=headers, 
                json=profile['data']
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Style: {result.get('style')}")
                    print(f"✅ IA: {result.get('ai_provider')}")
                    print(f"✅ Description: {result.get('description')}")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_different_styles():
    """Test des différents styles de description"""
    print("\n🎨 Test des différents styles")
    
    styles = ["attractif", "drôle", "mystérieux", "sincère"]
    
    base_info = {
        "user_info": {
            "age": 30,
            "interests": ["cinéma", "randonnée"],
            "profession": "développeur"
        },
        "length": "court"
    }
    
    for style in styles:
        print(f"\n🎭 Style: {style}")
        
        try:
            test_data = base_info.copy()
            test_data["style"] = style
            
            response = requests.post(
                f"{API_URL}/description", 
                headers=headers, 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Description {style}: {result.get('description')}")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_different_lengths():
    """Test des différentes longueurs"""
    print("\n📏 Test des différentes longueurs")
    
    lengths = ["court", "moyen", "long"]
    
    base_info = {
        "user_info": {
            "age": 26,
            "interests": ["yoga", "photographie"],
            "profession": "professeure"
        },
        "style": "sincère"
    }
    
    for length in lengths:
        print(f"\n📝 Longueur: {length}")
        
        try:
            test_data = base_info.copy()
            test_data["length"] = length
            
            response = requests.post(
                f"{API_URL}/description", 
                headers=headers, 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    description = result.get('description')
                    word_count = len(description.split())
                    print(f"✅ Description ({word_count} mots): {description}")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_frontend_compatibility():
    """Test de compatibilité avec le frontend Vue.js"""
    print("\n🖥️ Test de compatibilité frontend")
    
    # Simuler les données que le frontend pourrait envoyer
    frontend_data = {
        "user_info": {
            "age": "27",  # String comme souvent en frontend
            "interests": "sport, musique, voyage",  # String au lieu d'array
            "profession": "marketing",
            "personality": "sociable, optimiste",
            "relationship_goals": "relation sérieuse"
        },
        "style": "attractif",
        "length": "moyen"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/description", 
            headers=headers, 
            json=frontend_data
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print(f"✅ Compatible avec frontend")
                print(f"✅ Description: {result.get('description')}")
                print(f"✅ Infos utilisées: {'Oui' if result.get('user_info_used') else 'Non'}")
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Test complet de l'endpoint /description\n")
    
    test_description_basic()
    test_description_with_info()
    test_different_styles()
    test_different_lengths()
    test_frontend_compatibility()
    
    print("\n🎉 Tests terminés !")
    print("💡 L'endpoint /description est maintenant disponible pour votre frontend Vue.js")
