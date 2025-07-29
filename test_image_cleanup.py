#!/usr/bin/env python3
"""Test du système de nettoyage automatique des images"""

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

def test_image_cleanup_system():
    """Test du système de nettoyage automatique"""
    print("🧹 Test du système de nettoyage automatique des images\n")
    
    # 1. Vérifier le statut initial du cache
    print("1️⃣ Statut initial du cache:")
    try:
        response = requests.get(f"{API_URL}/ia/cache/status")
        if response.status_code == 200:
            result = response.json()
            print(f"   Images en cache: {result.get('images_in_cache')}")
            print(f"   Taille totale: {result.get('total_size_mb')} MB")
            print(f"   Dernier nettoyage: {result.get('last_cleanup')} secondes")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 2. Générer quelques images pour tester
    print("\n2️⃣ Génération d'images de test:")
    
    test_prompts = [
        "Photo de profil homme souriant",
        "Image motivationnelle confiance",
        "Portrait femme élégante"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"   Génération {i}/3: {prompt}")
        try:
            response = requests.post(
                f"{API_URL}/ia/image-simple", 
                headers=headers, 
                json={
                    "prompt": prompt,
                    "style": "portrait",
                    "size": "512x512"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"   ✅ Image générée en {result.get('processing_time')}s")
                    if 'cleanup_info' in result:
                        print(f"   🗑️ {result.get('cleanup_info')}")
                else:
                    print(f"   ❌ Erreur: {result.get('error')}")
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Petit délai entre les générations
        time.sleep(1)
    
    # 3. Vérifier le statut du cache après génération
    print("\n3️⃣ Statut du cache après génération:")
    try:
        response = requests.get(f"{API_URL}/ia/cache/status")
        if response.status_code == 200:
            result = response.json()
            print(f"   Images en cache: {result.get('images_in_cache')}")
            print(f"   Taille totale: {result.get('total_size_mb')} MB")
            
            if result.get('cache_details'):
                print("   Détails du cache:")
                for detail in result.get('cache_details'):
                    print(f"     - ID: {detail.get('id')}, Âge: {detail.get('age_seconds')}s, Taille: {detail.get('size_kb')} KB")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 4. Forcer le nettoyage
    print("\n4️⃣ Test du nettoyage forcé:")
    try:
        response = requests.post(f"{API_URL}/ia/cache/cleanup")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result.get('message')}")
            print(f"   Images supprimées: {result.get('images_removed')}")
            print(f"   Images restantes: {result.get('images_remaining')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 5. Vérifier le statut final
    print("\n5️⃣ Statut final du cache:")
    try:
        response = requests.get(f"{API_URL}/ia/cache/status")
        if response.status_code == 200:
            result = response.json()
            print(f"   Images en cache: {result.get('images_in_cache')}")
            print(f"   Taille totale: {result.get('total_size_mb')} MB")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_memory_efficiency():
    """Test de l'efficacité mémoire"""
    print("\n💾 Test d'efficacité mémoire:")
    
    # Générer une image et vérifier qu'elle est bien supprimée
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{API_URL}/ia/image-simple", 
            headers=headers, 
            json={
                "prompt": "Test efficacité mémoire",
                "style": "realistic",
                "size": "512x512"
            }
        )
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                image_size = len(result.get('image', ''))
                print(f"   ✅ Image générée: {image_size} caractères base64")
                print(f"   ✅ Temps de génération: {generation_time:.2f}s")
                print(f"   ✅ Temps API: {result.get('processing_time')}s")
                
                # Vérifier que l'image n'est plus en cache
                cache_response = requests.get(f"{API_URL}/ia/cache/status")
                if cache_response.status_code == 200:
                    cache_result = cache_response.json()
                    print(f"   ✅ Images restantes en cache: {cache_result.get('images_in_cache')}")
                    
                    if cache_result.get('images_in_cache') == 0:
                        print("   🎉 Nettoyage automatique parfait !")
                    else:
                        print("   ⚠️ Des images restent en cache")
            else:
                print(f"   ❌ Erreur génération: {result.get('error')}")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_image_cleanup_system()
    test_memory_efficiency()
    
    print("\n🎉 Tests de nettoyage terminés !")
    print("💡 Le système supprime automatiquement les images après envoi")
    print("🧹 Nettoyage automatique toutes les 60 secondes pour les images > 5 minutes")
