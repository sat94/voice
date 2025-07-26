#!/usr/bin/env python3
"""
Test de la version PREMIUM (toujours longue)
"""

import requests

def test_premium():
    url = "http://localhost:8012/description"
    
    # Test simple sans paramètre longueur
    data = {
        "prenom": "Sophie",
        "physique": "Grande, sportive, cheveux châtains, yeux verts",
        "gouts": "Yoga, cuisine, voyages, photographie",
        "recherche": "amoureuse"
    }
    
    print("💎 TEST VERSION PREMIUM (Service Payant)")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"💎 Score PREMIUM: {result['score_attractivite']}/100")
            print(f"⏱️ Temps: {result['processing_time']:.3f}s")
            print(f"📏 Longueur: {len(result['description'])} caractères")
            print(f"📊 Mots: ~{len(result['description'].split())} mots")
            print("\n📝 DESCRIPTION PREMIUM GÉNÉRÉE:")
            print("-" * 60)
            print(result['description'])
            print("-" * 60)
            print(f"\n💡 Conseils: {', '.join(result['conseils_amelioration'])}")
            print(f"🏷️ Mots-clés: {', '.join(result['mots_cles_attractifs'])}")
            
            # Vérifier que c'est bien la version complète
            if len(result['description']) > 500:
                print("\n✅ VERSION PREMIUM CONFIRMÉE (>500 caractères)")
            else:
                print("\n⚠️ Description plus courte que prévu")
                
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_premium()
