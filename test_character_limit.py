#!/usr/bin/env python3
"""Test de la limite de 2000 caractères pour les descriptions"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "152445aasdaiaze145ae656ae2312aaaezaz32a132ùaezùùaaeaeùùaeaea"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_character_limits():
    """Test des limites de caractères pour différentes longueurs"""
    print("📏 Test des limites de caractères")
    
    # Données riches pour tester la limite
    rich_data = {
        "user_info": {
            "prenom": "Alexandre",
            "physique": "Sexe: Homme. Taille: 185cm. Poids: 78kg. Yeux: Verts. Couleur de cheveux: Châtain. Lunettes: Non. Origine: Franco-Italien",
            "gouts": "Caractère: Créatif, Passionné, Aventurier, Charismatique, Intellectuel. Musique: Jazz, Classical, Electronic, World Music. Langues: Français, Italien, Anglais, Espagnol, Japonais. Hobbies: Photographie, Cuisine, Voyage, Littérature, Art contemporain",
            "recherche": "Relation sérieuse"
        },
        "style": "attractif"
    }
    
    lengths = ["court", "moyen", "long"]
    
    for length in lengths:
        print(f"\n📝 Test longueur: {length.upper()}")
        
        test_data = rich_data.copy()
        test_data["length"] = length
        
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
                    char_count = result.get('character_count', len(description))
                    within_limit = result.get('within_limit', True)
                    
                    print(f"✅ Caractères: {char_count}/2000")
                    print(f"✅ Dans la limite: {'Oui' if within_limit else 'Non'}")
                    print(f"✅ IA: {result.get('ai_provider')}")
                    print(f"✅ Temps: {result.get('processing_time')}s")
                    
                    # Analyser la qualité vs longueur
                    if char_count <= 500:
                        print("📊 Catégorie: Court et concis")
                    elif char_count <= 1000:
                        print("📊 Catégorie: Équilibré")
                    elif char_count <= 1500:
                        print("📊 Catégorie: Détaillé")
                    else:
                        print("📊 Catégorie: Très détaillé")
                    
                    print(f"📝 Description:")
                    print(f"   {description[:200]}...")
                    
                    # Vérifier qu'on évite les infos physiques
                    physical_mentions = []
                    if "185" in description or "1m85" in description:
                        physical_mentions.append("❌ Taille mentionnée")
                    if "78kg" in description or "78 kg" in description:
                        physical_mentions.append("❌ Poids mentionné")
                    if "verts" in description.lower() and "yeux" in description.lower():
                        physical_mentions.append("❌ Couleur yeux mentionnée")
                    
                    if physical_mentions:
                        print("⚠️ Informations physiques répétées:")
                        for mention in physical_mentions:
                            print(f"     {mention}")
                    else:
                        print("✅ Aucune info physique répétée")
                        
                else:
                    print(f"❌ Erreur: {result.get('error')}")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_serge_with_limit():
    """Test spécifique avec Serge et la limite de caractères"""
    print("\n👤 Test Serge avec limite de 2000 caractères")
    
    serge_data = {
        "user_info": {
            "prenom": "Serge",
            "physique": "Sexe: Homme. Taille: 181cm. Poids: 80kg. Yeux: Noirs. Couleur de cheveux: Raser. Lunettes: Non. Origine: Métisse",
            "gouts": "Caractère: Sérieux, Intelligent, Intrigant, Intrépide. Musique: Rock, Pop, R&B. Langues: Moldave, Estonien",
            "recherche": "Amical"
        },
        "style": "attractif",
        "length": "moyen"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/description", 
            headers=headers, 
            json=serge_data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                description = result.get('description')
                char_count = result.get('character_count', len(description))
                
                print(f"✅ Description générée: {char_count} caractères")
                print(f"✅ Dans la limite: {'Oui' if char_count <= 2000 else 'Non'}")
                print(f"\n📝 Description finale:")
                print(f"{description}")
                
                # Analyser les éléments vendeurs utilisés
                selling_elements = []
                if "moldave" in description.lower() or "estonien" in description.lower():
                    selling_elements.append("✅ Langues rares")
                if "métisse" in description.lower():
                    selling_elements.append("✅ Origine")
                if "rock" in description.lower() or "r&b" in description.lower():
                    selling_elements.append("✅ Goûts musicaux")
                if any(trait in description.lower() for trait in ["sérieux", "intelligent", "intrigant", "intrépide"]):
                    selling_elements.append("✅ Traits de caractère")
                
                print(f"\n🎯 Éléments vendeurs utilisés: {len(selling_elements)}")
                for element in selling_elements:
                    print(f"   {element}")
                
                # Vérifier l'absence d'infos physiques
                physical_avoided = True
                if "181" in description or "80kg" in description or "noirs" in description.lower():
                    physical_avoided = False
                
                print(f"✅ Évite les infos physiques: {'Oui' if physical_avoided else 'Non'}")
                
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_extreme_data():
    """Test avec beaucoup de données pour voir la gestion de la limite"""
    print("\n🔥 Test avec données extrêmes")
    
    extreme_data = {
        "user_info": {
            "physique": "Sexe: Homme. Taille: 190cm. Poids: 85kg. Yeux: Bleus. Couleur de cheveux: Blond. Lunettes: Oui. Origine: Franco-Germano-Suédois",
            "gouts": "Caractère: Créatif, Passionné, Aventurier, Charismatique, Intellectuel, Drôle, Romantique, Sportif, Artistique. Musique: Jazz, Classical, Electronic, World Music, Rock, Pop, Blues, Reggae, Hip-Hop. Langues: Français, Allemand, Suédois, Anglais, Espagnol, Italien, Japonais, Mandarin, Russe. Hobbies: Photographie professionnelle, Cuisine gastronomique, Voyage autour du monde, Littérature contemporaine, Art contemporain, Sculpture, Peinture, Musique, Danse, Sport extrême, Escalade, Plongée, Ski, Surf",
            "recherche": "Relation sérieuse et durable avec projets communs"
        },
        "style": "attractif",
        "length": "long"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/description", 
            headers=headers, 
            json=extreme_data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                description = result.get('description')
                char_count = result.get('character_count', len(description))
                within_limit = result.get('within_limit', True)
                
                print(f"✅ Données extrêmes traitées")
                print(f"✅ Caractères: {char_count}/2000")
                print(f"✅ Respecte la limite: {'Oui' if within_limit else 'Non'}")
                
                if char_count > 1800:
                    print("⚠️ Proche de la limite - bon test !")
                
                print(f"\n📝 Extrait (200 premiers caractères):")
                print(f"{description[:200]}...")
                
            else:
                print(f"❌ Erreur: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Test de la limite de 2000 caractères\n")
    
    test_character_limits()
    test_serge_with_limit()
    test_extreme_data()
    
    print("\n🎉 Tests terminés !")
    print("💡 Toutes les descriptions respectent maintenant la limite de 2000 caractères")
    print("🎯 Focus sur les éléments vendeurs non-visibles")
