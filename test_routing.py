#!/usr/bin/env python3
"""Test du routage intelligent des questions vers les bonnes IA"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Questions de test pour différentes catégories
test_questions = [
    # Questions psychologiques (devraient aller vers Gemini)
    {
        "prompt": "Pourquoi est-ce que je ressens de l'anxiété avant chaque rendez-vous ?",
        "expected_ai": "google_gemini",
        "category": "psychology"
    },
    {
        "prompt": "Comment expliquer mes émotions contradictoires en amour ?",
        "expected_ai": "google_gemini", 
        "category": "psychology"
    },
    
    # Questions de séduction pratique (devraient aller vers DeepInfra)
    {
        "prompt": "Que faire pour draguer une fille dans un bar ?",
        "expected_ai": "deepinfra",
        "category": "seduction"
    },
    {
        "prompt": "Comment aborder quelqu'un que je trouve attirant ?",
        "expected_ai": "deepinfra",
        "category": "seduction"
    },
    
    # Questions sexologiques (devraient aller vers Gemini)
    {
        "prompt": "Qu'est-ce que la libido et comment ça fonctionne ?",
        "expected_ai": "google_gemini",
        "category": "sexology"
    },
    
    # Questions d'amitié (équilibré)
    {
        "prompt": "Mon ami me soutient dans mes difficultés relationnelles",
        "expected_ai": "variable",
        "category": "friendship"
    },
    
    # Questions générales
    {
        "prompt": "Comment développer ma confiance en soi ?",
        "expected_ai": "google_gemini",
        "category": "general"
    }
]

def test_routing():
    """Test le routage pour chaque question"""
    print("🧪 Test du routage intelligent des questions\n")
    
    correct_predictions = 0
    total_tests = len(test_questions)
    
    for i, test in enumerate(test_questions, 1):
        print(f"Test {i}/{total_tests}")
        print(f"Question: {test['prompt']}")
        
        try:
            response = requests.post(f"{API_URL}/ia/routing-test", headers=headers, json={"prompt": test['prompt']})
            
            if response.status_code == 200:
                result = response.json()
                
                detected_category = result.get('category')
                recommended_ai = result.get('recommended_ai')
                
                print(f"✅ Catégorie détectée: {detected_category}")
                print(f"✅ IA recommandée: {recommended_ai}")
                
                # Vérifier si la prédiction est correcte
                if test['expected_ai'] == 'variable':
                    print(f"✅ Résultat variable accepté")
                    correct_predictions += 1
                elif recommended_ai == test['expected_ai']:
                    print(f"✅ Prédiction correcte!")
                    correct_predictions += 1
                else:
                    print(f"❌ Prédiction incorrecte (attendu: {test['expected_ai']})")
                
            else:
                print(f"❌ Erreur API: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("-" * 50)
    
    # Résumé
    accuracy = (correct_predictions / total_tests) * 100
    print(f"\n📊 Résultats du routage:")
    print(f"Prédictions correctes: {correct_predictions}/{total_tests}")
    print(f"Précision: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("🎉 Excellent routage!")
    elif accuracy >= 60:
        print("👍 Bon routage, peut être amélioré")
    else:
        print("⚠️ Routage à améliorer")

if __name__ == "__main__":
    test_routing()
