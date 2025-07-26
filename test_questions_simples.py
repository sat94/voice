#!/usr/bin/env python3
"""
Test des questions simples avec gestes humains
"""

import requests
import json

def test_questions_simples():
    url = "http://localhost:8012/ia"
    
    questions = [
        "Quelle heure il est ?",
        "Quel jour nous sommes ?",
        "Bonjour Sophie !",
        "Quel âge as-tu ?",
        "Où habites-tu ?",
        "Comment améliorer ma confiance ?"  # Question complexe pour Gemini
    ]
    
    print("🤖 TEST QUESTIONS SIMPLES AVEC GESTES HUMAINS")
    print("=" * 60)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. QUESTION: {question}")
        print("-" * 40)
        
        try:
            response = requests.post(url, json={
                "prompt": question,
                "include_audio": False
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RÉPONSE: {result['response']}")
                print(f"📊 Provider: {result['provider']}")
                print(f"⏱️ Temps: {result['processing_time']:.3f}s")
                
                # Vérifier si c'est une réponse avec geste
                if "*" in result['response']:
                    print("🎭 GESTE DÉTECTÉ !")
                    
            else:
                print(f"❌ Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_questions_simples()
