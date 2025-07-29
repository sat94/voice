#!/usr/bin/env python3
"""Test des multiples modèles IA avec routage intelligent"""

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

# Questions de test pour différents modèles
test_questions = [
    # Questions complexes (devraient aller vers Gemini)
    {
        "prompt": "Peux-tu analyser les mécanismes psychologiques complexes derrière la jalousie en couple et expliquer comment les neurosciences modernes comprennent ce phénomène ?",
        "expected_model": "google_gemini",
        "category": "psychology",
        "complexity": "high"
    },
    
    # Questions pratiques (devraient aller vers Llama)
    {
        "prompt": "Que faire concrètement pour aborder une fille dans un café ?",
        "expected_model": "meta-llama",
        "category": "seduction",
        "complexity": "low"
    },
    
    # Questions nuancées (devraient aller vers Qwen)
    {
        "prompt": "Compare et analyse les différentes approches culturelles de la séduction entre l'Europe et l'Asie, en tenant compte des nuances sociales",
        "expected_model": "Qwen",
        "category": "general",
        "complexity": "high"
    },
    
    # Questions médicales (devraient aller vers Gemini)
    {
        "prompt": "Qu'est-ce que la dysfonction érectile d'un point de vue médical et quels sont les traitements recommandés ?",
        "expected_model": "google_gemini",
        "category": "sexology",
        "complexity": "medium"
    },
    
    # Questions courtes (pourraient aller vers modèle léger)
    {
        "prompt": "Comment dire bonjour à quelqu'un qui me plaît ?",
        "expected_model": "variable",
        "category": "seduction",
        "complexity": "low"
    }
]

def test_routing_intelligence():
    """Test le routage intelligent pour chaque question"""
    print("🧪 Test du routage intelligent multi-modèles\n")
    
    results = []
    
    for i, test in enumerate(test_questions, 1):
        print(f"Test {i}/{len(test_questions)}")
        print(f"Question: {test['prompt'][:80]}...")
        print(f"Complexité: {test['complexity']}")
        
        # Test du routage
        try:
            routing_response = requests.post(
                f"{API_URL}/ia/routing-test", 
                headers=headers, 
                json={"prompt": test['prompt']}
            )
            
            if routing_response.status_code == 200:
                routing_result = routing_response.json()
                print(f"✅ Catégorie: {routing_result.get('category')}")
                print(f"✅ IA recommandée: {routing_result.get('recommended_ai')}")
            
        except Exception as e:
            print(f"❌ Erreur routage: {e}")
        
        # Test de la réponse complète
        try:
            start_time = time.time()
            
            ia_response = requests.post(
                f"{API_URL}/ia/simple", 
                headers=headers, 
                json={"prompt": test['prompt']}
            )
            
            response_time = time.time() - start_time
            
            if ia_response.status_code == 200:
                ia_result = ia_response.json()
                ai_provider = ia_result.get('ai_provider', 'unknown')
                response_text = ia_result.get('response', '')
                
                print(f"✅ Fournisseur utilisé: {ai_provider}")
                print(f"✅ Temps de réponse: {response_time:.2f}s")
                print(f"✅ Réponse: {response_text[:100]}...")
                
                results.append({
                    "question": test['prompt'][:50] + "...",
                    "expected": test['expected_model'],
                    "actual": ai_provider,
                    "category": ia_result.get('category'),
                    "response_time": response_time,
                    "complexity": test['complexity']
                })
                
            else:
                print(f"❌ Erreur API: {ia_response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur IA: {e}")
        
        print("-" * 80)
    
    # Analyse des résultats
    print("\n📊 Analyse des performances:")
    
    # Temps de réponse par complexité
    high_complexity = [r for r in results if r['complexity'] == 'high']
    low_complexity = [r for r in results if r['complexity'] == 'low']
    
    if high_complexity:
        avg_high = sum(r['response_time'] for r in high_complexity) / len(high_complexity)
        print(f"⏱️ Temps moyen questions complexes: {avg_high:.2f}s")
    
    if low_complexity:
        avg_low = sum(r['response_time'] for r in low_complexity) / len(low_complexity)
        print(f"⏱️ Temps moyen questions simples: {avg_low:.2f}s")
    
    # Distribution des modèles utilisés
    providers = {}
    for result in results:
        provider = result['actual'].split('(')[0].strip()
        providers[provider] = providers.get(provider, 0) + 1
    
    print(f"\n🤖 Distribution des modèles utilisés:")
    for provider, count in providers.items():
        percentage = (count / len(results)) * 100
        print(f"  {provider}: {count}/{len(results)} ({percentage:.1f}%)")
    
    return results

def test_specific_model():
    """Test d'un modèle spécifique"""
    print("\n🎯 Test d'un modèle spécifique")
    
    test_prompt = "Donne-moi 3 conseils rapides pour être plus confiant en rendez-vous"
    
    try:
        response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={"prompt": test_prompt}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Modèle utilisé: {result.get('ai_provider')}")
            print(f"✅ Réponse: {result.get('response')}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    results = test_routing_intelligence()
    test_specific_model()
