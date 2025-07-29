#!/usr/bin/env python3
"""Test de la recherche web améliorée avec DuckDuckGo"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_improved_search():
    """Test de la recherche améliorée"""
    print("🔍 Test de recherche web améliorée (DuckDuckGo + Fallback)")
    
    search_queries = [
        "conseils séduction moderne",
        "psychologie des relations",
        "meilleurs sites de rencontre 2024"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Recherche: {query}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/web-search", 
                headers=headers, 
                json={
                    "query": query,
                    "max_results": 3,
                    "open_browser": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Résultats trouvés: {result.get('results_count')}")
                    print(f"✅ Navigateur ouvert: {'Oui' if result.get('browser_opened') else 'Non'}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    # Afficher les résultats
                    for i, res in enumerate(result.get('results', []), 1):
                        print(f"   {i}. {res.get('title')[:60]}...")
                        print(f"      URL: {res.get('url')}")
                        print(f"      Source: {res.get('source', 'Web')}")
                        if res.get('snippet'):
                            print(f"      Extrait: {res.get('snippet')[:100]}...")
                        
                    if result.get('browser_opened'):
                        print("🌐 Premier résultat ouvert dans votre navigateur !")
                        
                    # Analyser la source des résultats
                    sources = [res.get('source', 'Web') for res in result.get('results', [])]
                    if any('DuckDuckGo' in s for s in sources):
                        print("✅ Recherche DuckDuckGo réussie")
                    elif any('Actualités' in s for s in sources):
                        print("⚠️ Fallback vers actualités utilisé")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_meetvoice_specific_searches():
    """Test de recherches spécifiques à MeetVoice"""
    print("\n💕 Test de recherches spécifiques MeetVoice")
    
    meetvoice_queries = [
        "comment draguer sur Tinder",
        "premiers messages site de rencontre",
        "profil parfait application rencontre",
        "psychologie attraction physique"
    ]
    
    for query in meetvoice_queries:
        print(f"\n💕 Recherche MeetVoice: {query}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/web-search", 
                headers=headers, 
                json={
                    "query": query,
                    "max_results": 2,
                    "open_browser": False  # Pas d'ouverture pour ce test
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Résultats: {result.get('results_count')}")
                    
                    for i, res in enumerate(result.get('results', []), 1):
                        print(f"   {i}. {res.get('title')[:50]}...")
                        
                    # Évaluer la pertinence
                    titles = [res.get('title', '').lower() for res in result.get('results', [])]
                    relevant_keywords = ['tinder', 'rencontre', 'séduction', 'profil', 'message', 'attraction']
                    
                    relevance = sum(1 for title in titles for keyword in relevant_keywords if keyword in title)
                    if relevance > 0:
                        print(f"✅ Pertinence: {relevance} mots-clés trouvés")
                    else:
                        print("⚠️ Résultats peu pertinents")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_combined_ia_search():
    """Test combiné IA + Recherche pour une question complète"""
    print("\n🤖🔍 Test combiné IA + Recherche web")
    
    question = "Comment améliorer mon profil Tinder pour avoir plus de matchs ?"
    
    print(f"Question complète: {question}")
    
    # 1. Réponse IA
    try:
        ia_response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={"prompt": question}
        )
        
        if ia_response.status_code == 200:
            ia_result = ia_response.json()
            print(f"\n🤖 Réponse IA:")
            print(f"   Modèle: {ia_result.get('ai_provider')}")
            print(f"   Réponse: {ia_result.get('response')[:200]}...")
        
    except Exception as e:
        print(f"❌ Erreur IA: {e}")
    
    # 2. Recherche complémentaire
    try:
        search_response = requests.post(
            f"{API_URL}/ia/web-search", 
            headers=headers, 
            json={
                "query": "optimiser profil Tinder conseils 2024",
                "max_results": 3,
                "open_browser": True
            }
        )
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            print(f"\n🔍 Recherche complémentaire:")
            print(f"   Résultats: {search_result.get('results_count')}")
            
            if search_result.get('results'):
                print("   Sources trouvées:")
                for res in search_result.get('results')[:2]:
                    print(f"   - {res.get('title')[:50]}...")
            
            if search_result.get('browser_opened'):
                print("🌐 Ressources complémentaires ouvertes dans le navigateur !")
        
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")

if __name__ == "__main__":
    test_improved_search()
    test_meetvoice_specific_searches()
    test_combined_ia_search()
    
    print("\n🎉 Tests de recherche améliorée terminés !")
    print("💡 DuckDuckGo + Fallback actualités pour une couverture maximale")
    print("🌐 Ouverture automatique des résultats pertinents")
