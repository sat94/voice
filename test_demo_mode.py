#!/usr/bin/env python3
"""Test du mode démo avec différentes catégories de questions"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Questions de test pour le mode démo
demo_questions = [
    # Séduction
    {
        "prompt": "Comment draguer une fille dans un café ?",
        "expected_category": "seduction"
    },
    {
        "prompt": "Je manque de confiance pour aborder quelqu'un",
        "expected_category": "seduction"
    },
    
    # Psychologie
    {
        "prompt": "J'ai de l'anxiété avant mes rendez-vous",
        "expected_category": "psychology"
    },
    {
        "prompt": "Mes émotions sont contradictoires en amour",
        "expected_category": "psychology"
    },
    
    # Sexologie
    {
        "prompt": "Qu'est-ce que la libido exactement ?",
        "expected_category": "sexology"
    },
    
    # Amitié
    {
        "prompt": "Mon ami me donne des conseils relationnels",
        "expected_category": "friendship"
    },
    
    # Général
    {
        "prompt": "Comment dire bonjour à quelqu'un qui me plaît ?",
        "expected_category": "general"
    }
]

def test_demo_responses():
    """Test les réponses du mode démo"""
    print("🎭 Test du mode démo - Réponses intelligentes sans clés API\n")
    
    for i, test in enumerate(demo_questions, 1):
        print(f"Test {i}/{len(demo_questions)}")
        print(f"Question: {test['prompt']}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/simple", 
                headers=headers, 
                json={"prompt": test['prompt']}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                category = result.get('category')
                ai_provider = result.get('ai_provider')
                response_text = result.get('response')
                
                print(f"✅ Catégorie: {category}")
                print(f"✅ Fournisseur: {ai_provider}")
                print(f"✅ Réponse: {response_text}")
                
                # Vérifier que c'est bien le mode démo
                if ai_provider == "demo_mode":
                    print("🎭 Mode démo actif !")
                else:
                    print(f"⚠️ Mode inattendu: {ai_provider}")
                
            else:
                print(f"❌ Erreur: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("-" * 60)

def test_demo_with_audio():
    """Test du mode démo avec génération audio"""
    print("\n🔊 Test du mode démo avec audio")
    
    test_prompt = "Comment être plus confiant en rendez-vous ?"
    
    try:
        response = requests.post(
            f"{API_URL}/ia", 
            headers=headers, 
            json={
                "prompt": test_prompt,
                "include_prompt_audio": False  # Éviter l'audio du prompt
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Question: {test_prompt}")
            print(f"✅ Catégorie: {result.get('category')}")
            print(f"✅ Fournisseur: {result.get('ai_provider')}")
            print(f"✅ Réponse: {result.get('response')}")
            print(f"✅ Audio généré: {'Oui' if result.get('response_audio') else 'Non'}")
            print(f"✅ Temps: {result.get('processing_time')}s")
            
            if result.get('response_audio'):
                audio_size = len(result.get('response_audio', ''))
                print(f"✅ Taille audio: {audio_size} caractères (base64)")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_demo_responses()
    test_demo_with_audio()
