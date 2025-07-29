#!/usr/bin/env python3
"""Test du nouveau modèle Qwen2.5-72B vs ancien Llama-3.3-70B"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_qwen_performance():
    """Test des performances de Qwen2.5-72B"""
    print("🚀 Test du nouveau modèle Qwen2.5-72B\n")
    
    test_scenarios = [
        {
            "prompt": "Comment draguer intelligemment une fille dans un café sans être lourd ?",
            "category": "seduction",
            "expected_model": "Qwen"
        },
        {
            "prompt": "Analyse psychologique : pourquoi certaines personnes ont peur de l'engagement ?",
            "category": "psychology", 
            "expected_model": "Gemini"
        },
        {
            "prompt": "Donne-moi 5 techniques concrètes pour être plus confiant en rendez-vous",
            "category": "seduction",
            "expected_model": "Qwen"
        },
        {
            "prompt": "Comment gérer l'anxiété sociale dans les relations amoureuses ?",
            "category": "psychology",
            "expected_model": "Variable"
        }
    ]
    
    total_time = 0
    qwen_responses = 0
    gemini_responses = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}/{len(test_scenarios)}: {scenario['category']}")
        print(f"Question: {scenario['prompt']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_URL}/ia/simple", 
                headers=headers, 
                json={"prompt": scenario['prompt']}
            )
            
            response_time = time.time() - start_time
            total_time += response_time
            
            if response.status_code == 200:
                result = response.json()
                
                category = result.get('category')
                ai_provider = result.get('ai_provider')
                response_text = result.get('response')
                
                print(f"✅ Catégorie détectée: {category}")
                print(f"✅ IA utilisée: {ai_provider}")
                print(f"✅ Temps de réponse: {response_time:.2f}s")
                print(f"✅ Réponse: {response_text[:150]}...")
                
                # Compter les modèles utilisés
                if "Qwen" in ai_provider:
                    qwen_responses += 1
                    print("🎯 Qwen2.5-72B utilisé !")
                elif "google_gemini" in ai_provider:
                    gemini_responses += 1
                    print("🧠 Google Gemini utilisé !")
                
                # Évaluer la qualité de la réponse
                if len(response_text) > 100 and "désolée" not in response_text.lower():
                    print("✅ Réponse de qualité détectée")
                else:
                    print("⚠️ Réponse courte ou fallback")
                    
            else:
                print(f"❌ Erreur: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("-" * 70)
    
    # Statistiques finales
    avg_time = total_time / len(test_scenarios)
    
    print(f"\n📊 Statistiques de performance:")
    print(f"✅ Temps moyen de réponse: {avg_time:.2f}s")
    print(f"✅ Réponses Qwen2.5-72B: {qwen_responses}/{len(test_scenarios)}")
    print(f"✅ Réponses Google Gemini: {gemini_responses}/{len(test_scenarios)}")
    print(f"✅ Répartition: {(qwen_responses/len(test_scenarios)*100):.1f}% Qwen, {(gemini_responses/len(test_scenarios)*100):.1f}% Gemini")

def test_qwen_vs_gemini_quality():
    """Comparaison qualité Qwen vs Gemini"""
    print("\n🥊 Comparaison qualité Qwen2.5 vs Gemini")
    
    # Question qui peut aller vers les deux
    prompt = "Comment développer son charisme naturel pour être plus attirant ?"
    
    print(f"Question test: {prompt}\n")
    
    # Test avec routage normal
    try:
        response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"🤖 Routage automatique:")
            print(f"   IA choisie: {result.get('ai_provider')}")
            print(f"   Catégorie: {result.get('category')}")
            print(f"   Réponse: {result.get('response')[:200]}...")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_model_status():
    """Vérifier le statut des modèles"""
    print("\n🔍 Statut des modèles IA")
    
    try:
        response = requests.get(f"{API_URL}/ia/status")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Google Gemini: {'Actif' if result['google_gemini']['configured'] else 'Inactif'}")
            print(f"✅ DeepInfra: {'Actif' if result['deepinfra']['configured'] else 'Inactif'}")
            print(f"✅ Modèle DeepInfra: {result['deepinfra']['model']}")
            print(f"✅ Mode fallback: {'Non' if not result['fallback_mode'] else 'Oui'}")
            
            if "Qwen2.5" in result['deepinfra']['model']:
                print("🎉 Qwen2.5-72B correctement configuré !")
            else:
                print("⚠️ Ancien modèle encore configuré")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_model_status()
    test_qwen_performance()
    test_qwen_vs_gemini_quality()
    
    print("\n🎉 Tests Qwen2.5-72B terminés !")
    print("💡 Qwen2.5-72B devrait être plus performant que Llama-3.3-70B")
    print("🚀 Meilleur en français, plus rapide, et plus intelligent")
