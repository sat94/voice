#!/usr/bin/env python3
"""
Test du langage corrigé selon le type de relation
"""

import requests

def test_langage_corrige():
    url = "http://localhost:8012/description"
    
    data_base = {
        "prenom": "Alex",
        "physique": "Taille moyenne, sportif, cheveux bruns, yeux noisette",
        "gouts": "Sport, cinéma, voyages, cuisine, lecture",
        "user_id": "test_langage"
    }
    
    # Test AMICAL (langage approprié)
    print("👫 TEST AMICAL - Langage approprié")
    print("=" * 50)
    
    data_amical = {**data_base, "recherche": "amical"}
    
    try:
        response = requests.post(url, json=data_amical)
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print("📝 CONCLUSION AMICAL:")
            print("-" * 30)
            # Extraire juste la conclusion
            description = result['description']
            lines = description.split('\n\n')
            conclusion = lines[-1] if lines else description
            print(conclusion)
            print("-" * 30)
            
            # Vérifier qu'il n'y a pas d'ambiguïté
            if "bons moments" in conclusion.lower():
                print("⚠️ ATTENTION: 'bons moments' peut être mal interprété")
            else:
                print("✅ Langage approprié pour l'amitié")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    
    # Test AMOUREUX (langage romantique)
    print("💕 TEST AMOUREUX - Langage romantique")
    print("=" * 50)
    
    data_amoureux = {**data_base, "recherche": "amoureuse"}
    
    try:
        response = requests.post(url, json=data_amoureux)
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print("📝 CONCLUSION AMOUREUSE:")
            print("-" * 30)
            description = result['description']
            lines = description.split('\n\n')
            conclusion = lines[-1] if lines else description
            print(conclusion)
            print("-" * 30)
            
            if "histoire d'amour" in conclusion.lower():
                print("✅ Langage romantique approprié")
            else:
                print("⚠️ Pourrait être plus romantique")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    
    # Test LIBERTIN (langage direct OK)
    print("🔥 TEST LIBERTIN - Langage direct approprié")
    print("=" * 50)
    
    data_libertin = {**data_base, "recherche": "libertin"}
    
    try:
        response = requests.post(url, json=data_libertin)
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print("📝 CONCLUSION LIBERTIN:")
            print("-" * 30)
            description = result['description']
            lines = description.split('\n\n')
            conclusion = lines[-1] if lines else description
            print(conclusion)
            print("-" * 30)
            
            if "bons moments" in conclusion.lower():
                print("✅ Langage direct approprié pour le libertinage")
            else:
                print("ℹ️ Langage adapté au contexte libertin")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_langage_corrige()
