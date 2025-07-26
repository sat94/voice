#!/usr/bin/env python3
"""
Test de la nouvelle description avec motivation et paragraphes
"""

import requests
import json

def test_description_avec_motivation():
    """Test des nouvelles descriptions avec motivation"""
    
    url = "http://localhost:8012/description"
    
    # Test données de Serge
    data_serge = {
        "prenom": "Serge",
        "physique": "Sexe: Homme. Taille: 180cm. Poids: 80kg. Yeux: Noisette. Cheveux: Noir. Style cheveux: Rasé. Lunettes: Aucune. Origine: Métisse",
        "gouts": "Caractère: Intelligent, Sportif, Déterminé, Charismatique, Réfléchi. Hobbies: Sport En Salle, Échecs, Course À Pied, Aviron, Pilotage. Sorties: Boite De Nuit, Restaurant, Pub, Cinéma. Films: Action, Horreur, Science-Fiction, Fantasy. Musique: Pop, R&B, Rock, Country. Langues: Français, Anglais, Espagnol",
        "recherche": "amical",
        "longueur": "moyenne",
        "user_id": "test_motivation"
    }
    
    print("🎯 Test Description AMICAL avec motivation")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=data_serge)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📊 Score: {result['score_attractivite']}/100")
            print(f"⏱️ Temps: {result['processing_time']:.2f}s")
            print("\n📝 DESCRIPTION GÉNÉRÉE:")
            print("-" * 40)
            print(result['description'])
            print("-" * 40)
            print(f"\n💡 Conseils: {', '.join(result['conseils_amelioration'])}")
            print(f"🏷️ Mots-clés: {', '.join(result['mots_cles_attractifs'])}")
            
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    
    # Test version AMOUREUSE
    data_serge["recherche"] = "amoureuse"
    data_serge["longueur"] = "longue"
    
    print("💕 Test Description AMOUREUSE avec motivation")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=data_serge)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📊 Score: {result['score_attractivite']}/100")
            print(f"⏱️ Temps: {result['processing_time']:.2f}s")
            print("\n📝 DESCRIPTION GÉNÉRÉE:")
            print("-" * 40)
            print(result['description'])
            print("-" * 40)
            print(f"\n💡 Conseils: {', '.join(result['conseils_amelioration'])}")
            print(f"🏷️ Mots-clés: {', '.join(result['mots_cles_attractifs'])}")
            
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    
    # Test version LIBERTIN
    data_serge["recherche"] = "libertin"
    data_serge["longueur"] = "tres_longue"
    
    print("🔥 Test Description LIBERTIN avec motivation (500 mots)")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=data_serge)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📊 Score: {result['score_attractivite']}/100")
            print(f"⏱️ Temps: {result['processing_time']:.2f}s")
            print(f"📏 Longueur: {len(result['description'])} caractères")
            print("\n📝 DESCRIPTION GÉNÉRÉE:")
            print("-" * 40)
            print(result['description'])
            print("-" * 40)
            print(f"\n💡 Conseils: {', '.join(result['conseils_amelioration'])}")
            print(f"🏷️ Mots-clés: {', '.join(result['mots_cles_attractifs'])}")
            
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_description_avec_motivation()
