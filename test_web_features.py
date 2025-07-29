#!/usr/bin/env python3
"""Test des fonctionnalités web : recherche, actualités, navigation"""

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

def test_web_search():
    """Test de la recherche web avec ouverture automatique"""
    print("🔍 Test de recherche web")
    
    search_queries = [
        "conseils séduction 2024",
        "psychologie des relations amoureuses",
        "sites de rencontre français"
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
                    "open_browser": True  # Ouverture automatique
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Résultats trouvés: {result.get('results_count')}")
                    print(f"✅ Navigateur ouvert: {'Oui' if result.get('browser_opened') else 'Non'}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    # Afficher les premiers résultats
                    for i, res in enumerate(result.get('results', [])[:2], 1):
                        print(f"   {i}. {res.get('title')[:60]}...")
                        print(f"      URL: {res.get('url')}")
                        
                    if result.get('browser_opened'):
                        print("🌐 Page ouverte automatiquement dans votre navigateur !")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        # Pause entre les recherches
        time.sleep(2)

def test_news_search():
    """Test de recherche d'actualités"""
    print("\n📰 Test de recherche d'actualités")
    
    news_topics = [
        "actualités relations amoureuses",
        "psychologie couple 2024",
        "tendances rencontres"
    ]
    
    for topic in news_topics:
        print(f"\n📰 Actualités: {topic}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/news", 
                headers=headers, 
                json={
                    "topic": topic,
                    "category": "general",
                    "max_results": 3,
                    "open_browser": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Articles trouvés: {result.get('articles_count')}")
                    print(f"✅ Navigateur ouvert: {'Oui' if result.get('browser_opened') else 'Non'}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    # Afficher les articles
                    for i, article in enumerate(result.get('articles', [])[:2], 1):
                        print(f"   {i}. {article.get('title')[:60]}...")
                        print(f"      Source: {article.get('source')}")
                        
                    if result.get('browser_opened'):
                        print("📰 Article ouvert automatiquement dans votre navigateur !")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        time.sleep(2)

def test_browse_url():
    """Test de navigation directe vers une URL"""
    print("\n🌐 Test de navigation directe")
    
    test_urls = [
        {
            "url": "https://www.meetic.fr",
            "description": "Site de rencontre Meetic"
        },
        {
            "url": "https://www.psychologies.com",
            "description": "Magazine Psychologies"
        }
    ]
    
    for test in test_urls:
        print(f"\n🌐 Navigation: {test['description']}")
        print(f"   URL: {test['url']}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/browse", 
                headers=headers, 
                json={
                    "url": test['url'],
                    "action": "open",
                    "open_browser": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Navigation réussie")
                    print(f"✅ Navigateur ouvert: {'Oui' if result.get('browser_opened') else 'Non'}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    if result.get('browser_opened'):
                        print("🌐 Site ouvert automatiquement dans votre navigateur !")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        time.sleep(2)

def test_screenshot_feature():
    """Test de la fonctionnalité screenshot"""
    print("\n📸 Test de capture d'écran")
    
    try:
        response = requests.post(
            f"{API_URL}/ia/browse", 
            headers=headers, 
            json={
                "url": "https://www.google.com",
                "action": "screenshot",
                "open_browser": False  # Pas d'ouverture pour le screenshot
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print(f"✅ Screenshot réussi")
                print(f"✅ Temps: {result.get('processing_time')}s")
                
                if result.get('screenshot'):
                    screenshot_size = len(result.get('screenshot'))
                    print(f"✅ Taille screenshot: {screenshot_size} caractères (base64)")
                    
                    # Sauvegarder le screenshot
                    import base64
                    screenshot_data = base64.b64decode(result.get('screenshot'))
                    with open('test_screenshot.png', 'wb') as f:
                        f.write(screenshot_data)
                    print("✅ Screenshot sauvegardé: test_screenshot.png")
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_combined_ia_web():
    """Test combiné IA + Web"""
    print("\n🤖🌐 Test combiné IA + Web")
    
    # Question qui nécessite une recherche web
    prompt = "Quelles sont les dernières tendances en matière de rencontres en ligne en 2024 ?"
    
    print(f"Question: {prompt}")
    
    # 1. Demander à l'IA
    try:
        ia_response = requests.post(
            f"{API_URL}/ia/simple", 
            headers=headers, 
            json={"prompt": prompt}
        )
        
        if ia_response.status_code == 200:
            ia_result = ia_response.json()
            print(f"\n🤖 Réponse IA ({ia_result.get('ai_provider')}):")
            print(f"   {ia_result.get('response')[:150]}...")
        
    except Exception as e:
        print(f"❌ Erreur IA: {e}")
    
    # 2. Rechercher des infos complémentaires
    try:
        web_response = requests.post(
            f"{API_URL}/ia/web-search", 
            headers=headers, 
            json={
                "query": "tendances rencontres en ligne 2024",
                "max_results": 2,
                "open_browser": True
            }
        )
        
        if web_response.status_code == 200:
            web_result = web_response.json()
            print(f"\n🔍 Recherche web complémentaire:")
            print(f"   Résultats: {web_result.get('results_count')}")
            print(f"   Navigateur ouvert: {'Oui' if web_result.get('browser_opened') else 'Non'}")
            
            if web_result.get('browser_opened'):
                print("🌐 Informations complémentaires ouvertes dans votre navigateur !")
        
    except Exception as e:
        print(f"❌ Erreur Web: {e}")

if __name__ == "__main__":
    print("🚀 Test complet des fonctionnalités web MeetVoice\n")
    
    test_web_search()
    test_news_search()
    test_browse_url()
    test_screenshot_feature()
    test_combined_ia_web()
    
    print("\n🎉 Tests web terminés !")
    print("💡 Les pages s'ouvrent automatiquement dans votre navigateur")
    print("📸 Screenshot sauvegardé: test_screenshot.png")
