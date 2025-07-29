#!/usr/bin/env python3
"""Test complet de toutes les fonctionnalités MeetVoice"""

import requests
import json
import base64
import time

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_complete_ia_workflow():
    """Test du workflow complet IA + Audio"""
    print("🎯 Test workflow complet IA + Audio")
    
    prompt = "Comment être plus confiant lors d'un premier rendez-vous ?"
    
    try:
        response = requests.post(
            f"{API_URL}/ia", 
            headers=headers, 
            json={
                "prompt": prompt,
                "include_prompt_audio": False,
                "voice": "denise"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Question: {prompt}")
            print(f"✅ Catégorie: {result.get('category')}")
            print(f"✅ IA utilisée: {result.get('ai_provider')}")
            print(f"✅ Réponse: {result.get('response')[:150]}...")
            print(f"✅ Audio généré: {'Oui' if result.get('response_audio') else 'Non'}")
            print(f"✅ Temps total: {result.get('processing_time')}s")
            
            # Sauvegarder l'audio pour test
            if result.get('response_audio'):
                audio_data = base64.b64decode(result.get('response_audio'))
                with open('test_response.mp3', 'wb') as f:
                    f.write(audio_data)
                print("✅ Audio sauvegardé: test_response.mp3")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_image_for_dating():
    """Test génération d'image pour site de rencontre"""
    print("\n📸 Test génération d'image pour dating")
    
    scenarios = [
        {
            "prompt": "Photo de profil homme confiant et souriant",
            "style": "portrait",
            "expected_category": "seduction"
        },
        {
            "prompt": "Image motivationnelle pour confiance en soi",
            "style": "artistic",
            "expected_category": "psychology"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎨 Scénario: {scenario['prompt']}")
        
        try:
            response = requests.post(
                f"{API_URL}/ia/image", 
                headers=headers, 
                json={
                    "prompt": scenario['prompt'],
                    "style": scenario['style'],
                    "size": "512x512"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    print(f"✅ Catégorie détectée: {result.get('category')}")
                    print(f"✅ Prompt optimisé: {result.get('optimized_prompt')[:100]}...")
                    print(f"✅ Style: {result.get('style')}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    # Sauvegarder l'image
                    image_data = base64.b64decode(result.get('image'))
                    filename = f"test_image_{scenario['style']}.png"
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    print(f"✅ Image sauvegardée: {filename}")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_ai_routing_performance():
    """Test des performances du routage IA"""
    print("\n⚡ Test performances routage IA")
    
    test_cases = [
        {"prompt": "Pourquoi je stresse avant un date ?", "expected": "psychology"},
        {"prompt": "Comment aborder une fille ?", "expected": "seduction"},
        {"prompt": "Qu'est-ce que la libido ?", "expected": "sexology"},
        {"prompt": "Mon ami me conseille", "expected": "friendship"}
    ]
    
    total_time = 0
    successful_routes = 0
    
    for case in test_cases:
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_URL}/ia/simple", 
                headers=headers, 
                json={"prompt": case['prompt']}
            )
            
            response_time = time.time() - start_time
            total_time += response_time
            
            if response.status_code == 200:
                result = response.json()
                category = result.get('category')
                ai_provider = result.get('ai_provider')
                
                print(f"✅ '{case['prompt'][:30]}...' → {category} via {ai_provider.split('(')[0]} ({response_time:.2f}s)")
                
                if category == case['expected']:
                    successful_routes += 1
            else:
                print(f"❌ Erreur pour: {case['prompt']}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    avg_time = total_time / len(test_cases)
    accuracy = (successful_routes / len(test_cases)) * 100
    
    print(f"\n📊 Résultats performances:")
    print(f"✅ Temps moyen: {avg_time:.2f}s")
    print(f"✅ Précision routage: {accuracy:.1f}%")
    print(f"✅ Routes réussies: {successful_routes}/{len(test_cases)}")

def test_api_status():
    """Test du statut de l'API"""
    print("\n🔍 Statut de l'API")
    
    try:
        response = requests.get(f"{API_URL}/ia/status")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Google Gemini: {'✓' if result['google_gemini']['configured'] else '✗'}")
            print(f"✅ DeepInfra: {'✓' if result['deepinfra']['configured'] else '✗'}")
            print(f"✅ Mode fallback: {'✗' if result['fallback_mode'] else '✓'}")
            print(f"✅ Fichier .env: {'✓' if result['env_file_loaded'] else '✗'}")
        else:
            print(f"❌ Erreur statut: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Test complet des fonctionnalités MeetVoice API\n")
    
    test_api_status()
    test_ai_routing_performance()
    test_complete_ia_workflow()
    test_image_for_dating()
    
    print("\n🎉 Tests terminés ! Vérifiez les fichiers générés :")
    print("   - test_response.mp3 (audio de réponse)")
    print("   - test_image_portrait.png (image portrait)")
    print("   - test_image_artistic.png (image artistique)")
