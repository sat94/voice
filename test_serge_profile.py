#!/usr/bin/env python3
"""Test avec les vraies données de Serge pour générer une description attractive"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_serge_profile():
    """Test avec les vraies données de Serge"""
    print("👤 Test avec les données réelles de Serge")
    
    # Données exactes de Serge
    serge_data = {
        "user_info": {
            "prenom": "Serge",
            "physique": "Sexe: Homme. Taille: 181cm. Poids: 80kg. Yeux: Noirs. Couleur de cheveux: Raser. Lunettes: Non. Origine: Métisse",
            "gouts": "Caractère: Sérieux, Intelligent, Intrigant, Intrépide. Musique: Rock, Pop, R&B. Langues: Moldave, Estonien",
            "recherche": "Amical",
            "user_id": "34ad8d1d-43a9-4bb6-b849-bbbc49679e18"
        },
        "style": "attractif",
        "length": "moyen"
    }
    
    print("📝 Données envoyées:")
    print(f"   Physique: {serge_data['user_info']['physique']}")
    print(f"   Goûts: {serge_data['user_info']['gouts']}")
    print(f"   Recherche: {serge_data['user_info']['recherche']}")
    
    try:
        response = requests.post(
            f"{API_URL}/description", 
            headers=headers, 
            json=serge_data
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print(f"\n✅ NOUVELLE DESCRIPTION AMÉLIORÉE:")
                print(f"   Style: {result.get('style')}")
                print(f"   IA: {result.get('ai_provider')}")
                print(f"   Temps: {result.get('processing_time')}s")
                print(f"\n📝 Description:")
                print(f"   {result.get('description')}")
                
                # Analyser la qualité
                description = result.get('description', '')
                
                print(f"\n📊 Analyse de qualité:")
                
                # Vérifier l'utilisation des données spécifiques
                specific_elements = []
                if "181" in description or "1m81" in description:
                    specific_elements.append("✅ Taille mentionnée")
                if "métisse" in description.lower():
                    specific_elements.append("✅ Origine mentionnée")
                if "moldave" in description.lower() or "estonien" in description.lower():
                    specific_elements.append("✅ Langues mentionnées")
                if "rock" in description.lower() or "r&b" in description.lower():
                    specific_elements.append("✅ Goûts musicaux mentionnés")
                if "sérieux" in description.lower() or "intelligent" in description.lower() or "intrigant" in description.lower():
                    specific_elements.append("✅ Caractère mentionné")
                
                # Vérifier l'absence de clichés
                cliches_found = []
                if "découvrir de nouvelles choses" in description.lower():
                    cliches_found.append("❌ Cliché 'découvrir de nouvelles choses'")
                if "rencontrer des gens" in description.lower():
                    cliches_found.append("❌ Cliché 'rencontrer des gens'")
                if "nouvelles aventures" in description.lower():
                    cliches_found.append("❌ Cliché 'nouvelles aventures'")
                
                print(f"   Éléments spécifiques utilisés: {len(specific_elements)}/5")
                for element in specific_elements:
                    print(f"     {element}")
                
                if cliches_found:
                    print(f"   Clichés détectés: {len(cliches_found)}")
                    for cliche in cliches_found:
                        print(f"     {cliche}")
                else:
                    print(f"   ✅ Aucun cliché détecté")
                
                # Score global
                score = len(specific_elements) * 20 - len(cliches_found) * 10
                print(f"\n🎯 Score d'attractivité: {score}/100")
                
                if score >= 80:
                    print("🔥 EXCELLENT - Profil très attractif !")
                elif score >= 60:
                    print("👍 BON - Profil attractif")
                elif score >= 40:
                    print("⚠️ MOYEN - Peut être amélioré")
                else:
                    print("❌ FAIBLE - Nécessite des améliorations")
                    
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_different_styles_serge():
    """Test des différents styles avec les données de Serge"""
    print("\n🎨 Test des différents styles pour Serge")
    
    base_data = {
        "user_info": {
            "prenom": "Serge",
            "physique": "Sexe: Homme. Taille: 181cm. Poids: 80kg. Yeux: Noirs. Couleur de cheveux: Raser. Lunettes: Non. Origine: Métisse",
            "gouts": "Caractère: Sérieux, Intelligent, Intrigant, Intrépide. Musique: Rock, Pop, R&B. Langues: Moldave, Estonien",
            "recherche": "Amical"
        },
        "length": "moyen"
    }
    
    styles = ["attractif", "mystérieux", "drôle", "sincère"]
    
    for style in styles:
        print(f"\n🎭 Style: {style.upper()}")
        
        test_data = base_data.copy()
        test_data["style"] = style
        
        try:
            response = requests.post(
                f"{API_URL}/description", 
                headers=headers, 
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    description = result.get('description')
                    print(f"✅ {description}")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Test des descriptions améliorées pour Serge\n")
    
    test_serge_profile()
    test_different_styles_serge()
    
    print("\n🎉 Tests terminés !")
    print("💡 Les descriptions devraient maintenant être beaucoup plus attractives et personnalisées !")
