#!/usr/bin/env python3
"""
API Description Attractive - MeetVoice
Génère des descriptions attractives de personnes pour profils de rencontre
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from database import get_database_service
import logging

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeetVoice Description Attractive", version="1.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8083", 
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8083",
        "https://aaaazealmmmma.duckdns.org",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"],
    expose_headers=["Content-Length", "Content-Type"],
)

# Service de base de données
db_service = get_database_service()

# Modèles de données
class PersonneInput(BaseModel):
    prenom: str = Field(..., description="Prénom de la personne")
    physique: str = Field(..., description="Description physique (taille, corpulence, couleur cheveux, etc.)")
    gouts: str = Field(..., description="Goûts et centres d'intérêt")
    recherche: Literal["amical", "amoureuse", "libertin"] = Field(..., description="Type de relation recherchée")
    user_id: Optional[str] = Field(default="anonymous", description="ID utilisateur")
    style_description: Optional[Literal["elegant", "decontracte", "seducteur", "authentique"]] = Field(
        default="authentique", 
        description="Style de description souhaité"
    )
    longueur: Optional[Literal["courte", "moyenne", "longue"]] = Field(
        default="moyenne",
        description="Longueur de la description"
    )

class DescriptionResponse(BaseModel):
    description: str
    conseils_amelioration: List[str]
    mots_cles_attractifs: List[str]
    score_attractivite: int
    style_utilise: str
    processing_time: float
    provider: str

# Templates de descriptions par type de recherche
TEMPLATES_DESCRIPTIONS = {
    "amical": {
        "intro": [
            "Salut ! Je suis {prenom}, une personne {adjectif_positif} qui adore {activite_principale}.",
            "Hello ! {prenom} ici, {description_courte} et toujours partant(e) pour {activite_sociale}.",
            "Coucou ! Je m'appelle {prenom}, {trait_caractere} qui cherche à élargir son cercle d'amis."
        ],
        "corps": [
            "Physiquement, je suis {physique_reformule}. Ce qui me passionne vraiment, c'est {gouts_reformules}.",
            "Côté look, {physique_reformule}. J'adore {gouts_reformules} et je suis toujours curieux(se) de découvrir de nouvelles choses.",
            "Je me décrirais comme {physique_reformule}. Mes passions ? {gouts_reformules} !"
        ],
        "conclusion": [
            "Si tu cherches quelqu'un avec qui partager de bons moments et des discussions enrichissantes, n'hésite pas !",
            "Toujours partant(e) pour de nouvelles aventures amicales et des découvertes ensemble !",
            "Si tu aimes {activite_commune}, on va sûrement bien s'entendre !"
        ]
    },
    
    "amoureuse": {
        "intro": [
            "Je suis {prenom}, {age_approximatif} ans, et je crois encore aux belles rencontres.",
            "Bonjour, je m'appelle {prenom}. {trait_romantique} qui cherche une connexion authentique.",
            "Salut ! {prenom}, {description_courte} en quête d'une relation sincère et complice."
        ],
        "corps": [
            "Physiquement, {physique_reformule}. J'ai une passion pour {gouts_reformules}, ce qui rend ma vie riche et épanouie.",
            "Je suis {physique_reformule} avec un cœur grand comme ça ! J'adore {gouts_reformules} et je rêve de partager ces moments avec quelqu'un de spécial.",
            "Côté apparence, {physique_reformule}. Ce qui m'anime au quotidien : {gouts_reformules}."
        ],
        "conclusion": [
            "Je recherche quelqu'un avec qui construire de beaux projets et partager les petits bonheurs du quotidien.",
            "Si tu cherches une relation basée sur la complicité, le respect et la tendresse, écris-moi !",
            "Prêt(e) à découvrir si nous sommes faits l'un pour l'autre ?"
        ]
    },
    
    "libertin": {
        "intro": [
            "Salut, je suis {prenom}, {description_sensuelle} qui assume pleinement sa sensualité.",
            "Hello ! {prenom}, {trait_confiant} à la recherche de rencontres sans tabous.",
            "Coucou, {prenom} ici. {description_courte} et ouverte d'esprit."
        ],
        "corps": [
            "Physiquement, {physique_reformule_sensuel}. J'aime {gouts_reformules} et je cultive l'art de vivre pleinement.",
            "Côté charme, {physique_reformule_sensuel}. Mes plaisirs : {gouts_reformules} et les expériences qui éveillent les sens.",
            "Je suis {physique_reformule_sensuel} avec une personnalité {trait_seducteur}. Passionné(e) par {gouts_reformules}."
        ],
        "conclusion": [
            "Je cherche des personnes ouvertes pour des moments complices et sans prise de tête.",
            "Si tu aimes l'authenticité et les plaisirs partagés, on devrait se rencontrer !",
            "Prêt(e) pour des échanges sincères et des découvertes mutuelles ?"
        ]
    }
}

# Dictionnaires de reformulation
REFORMULATIONS = {
    "physique": {
        "grand": ["élancé", "de belle taille", "avec une stature imposante"],
        "petit": ["de taille moyenne", "compact", "avec un charme discret"],
        "mince": ["svelte", "avec une silhouette fine", "élégamment mince"],
        "sportif": ["athlétique", "en forme", "avec une silhouette tonique"],
        "ronde": ["avec des formes généreuses", "voluptueuse", "aux courbes harmonieuses"],
        "brun": ["aux cheveux châtains", "avec une chevelure sombre", "brun aux reflets dorés"],
        "blond": ["aux cheveux clairs", "avec une chevelure dorée", "blond naturel"],
        "yeux bleus": ["au regard azur", "aux yeux couleur océan", "avec des yeux perçants"],
        "yeux verts": ["au regard émeraude", "aux yeux verts profonds", "avec des yeux envoûtants"],
        "yeux marron": ["au regard chocolat", "aux yeux noisette", "avec des yeux chaleureux"]
    },
    
    "gouts": {
        "sport": ["l'activité physique", "le bien-être par le mouvement", "les défis sportifs"],
        "lecture": ["les bons livres", "l'évasion littéraire", "les histoires captivantes"],
        "cinema": ["le 7ème art", "les belles histoires à l'écran", "les soirées cinéma"],
        "musique": ["les mélodies qui touchent l'âme", "l'univers musical", "les concerts et festivals"],
        "voyage": ["la découverte de nouveaux horizons", "l'exploration du monde", "les escapades dépaysantes"],
        "cuisine": ["l'art culinaire", "les saveurs du monde", "les plaisirs de la table"],
        "nature": ["les grands espaces", "la beauté de la nature", "les balades en plein air"],
        "art": ["l'expression artistique", "la beauté sous toutes ses formes", "les créations inspirantes"]
    }
}

class DescriptionGenerator:
    def __init__(self):
        self.templates = TEMPLATES_DESCRIPTIONS
        self.reformulations = REFORMULATIONS
    
    def reformuler_physique(self, physique: str, style_recherche: str = "amical") -> str:
        """Reformule la description physique de manière attractive"""
        physique_lower = physique.lower()
        elements_reformules = []
        
        for mot_cle, reformulations in self.reformulations["physique"].items():
            if mot_cle in physique_lower:
                if style_recherche == "libertin" and mot_cle in ["mince", "sportif", "ronde"]:
                    # Version plus sensuelle pour le libertin
                    if mot_cle == "mince":
                        elements_reformules.append("à la silhouette élégante et désirable")
                    elif mot_cle == "sportif":
                        elements_reformules.append("au corps sculpté et athlétique")
                    elif mot_cle == "ronde":
                        elements_reformules.append("aux courbes sensuelles et assumées")
                else:
                    elements_reformules.append(reformulations[0])
        
        if not elements_reformules:
            return "avec un charme naturel"
        
        return ", ".join(elements_reformules)
    
    def reformuler_gouts(self, gouts: str) -> str:
        """Reformule les goûts de manière attractive"""
        gouts_lower = gouts.lower()
        elements_reformules = []
        
        for mot_cle, reformulations in self.reformulations["gouts"].items():
            if mot_cle in gouts_lower:
                elements_reformules.append(reformulations[0])
        
        if not elements_reformules:
            # Reformulation générique
            return f"tout ce qui rend la vie belle, notamment {gouts}"
        
        return ", ".join(elements_reformules)
    
    def generer_description(self, personne: PersonneInput) -> Dict:
        """Génère une description attractive complète"""
        start_time = time.time()
        
        try:
            # Sélectionner le template selon le type de recherche
            template = self.templates[personne.recherche]
            
            # Reformuler les éléments
            physique_reformule = self.reformuler_physique(personne.physique, personne.recherche)
            gouts_reformules = self.reformuler_gouts(personne.gouts)
            
            # Variables pour le template
            variables = {
                "prenom": personne.prenom,
                "physique_reformule": physique_reformule,
                "physique_reformule_sensuel": physique_reformule.replace("charme naturel", "charme magnétique"),
                "gouts_reformules": gouts_reformules,
                "adjectif_positif": self._get_adjectif_positif(),
                "trait_caractere": self._get_trait_caractere(),
                "trait_romantique": self._get_trait_romantique(),
                "trait_confiant": self._get_trait_confiant(),
                "trait_seducteur": self._get_trait_seducteur(),
                "description_courte": self._get_description_courte(),
                "description_sensuelle": self._get_description_sensuelle(),
                "activite_principale": self._extraire_activite_principale(personne.gouts),
                "activite_sociale": self._get_activite_sociale(),
                "activite_commune": self._extraire_activite_commune(personne.gouts),
                "age_approximatif": "20-35"  # Générique
            }
            
            # Construire la description
            if personne.longueur == "courte":
                description = self._generer_description_courte(template, variables)
            elif personne.longueur == "longue":
                description = self._generer_description_longue(template, variables)
            else:
                description = self._generer_description_moyenne(template, variables)
            
            # Générer conseils et mots-clés
            conseils = self._generer_conseils(personne)
            mots_cles = self._extraire_mots_cles(description)
            score = self._calculer_score_attractivite(description, personne)
            
            processing_time = time.time() - start_time
            
            return {
                "description": description,
                "conseils_amelioration": conseils,
                "mots_cles_attractifs": mots_cles,
                "score_attractivite": score,
                "style_utilise": personne.style_description,
                "processing_time": processing_time,
                "provider": "description_generator"
            }
            
        except Exception as e:
            logger.error(f"Erreur génération description: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _generer_description_moyenne(self, template: Dict, variables: Dict) -> str:
        """Génère une description de longueur moyenne"""
        intro = template["intro"][0].format(**variables)
        corps = template["corps"][0].format(**variables)
        conclusion = template["conclusion"][0].format(**variables)
        
        return f"{intro} {corps} {conclusion}"
    
    def _generer_description_courte(self, template: Dict, variables: Dict) -> str:
        """Génère une description courte"""
        intro = template["intro"][0].format(**variables)
        conclusion = template["conclusion"][0].format(**variables)
        
        return f"{intro} {conclusion}"
    
    def _generer_description_longue(self, template: Dict, variables: Dict) -> str:
        """Génère une description longue"""
        intro = template["intro"][0].format(**variables)
        corps1 = template["corps"][0].format(**variables)
        corps2 = template["corps"][1].format(**variables) if len(template["corps"]) > 1 else ""
        conclusion = template["conclusion"][0].format(**variables)
        
        return f"{intro} {corps1} {corps2} {conclusion}".replace("  ", " ")
    
    def _get_adjectif_positif(self) -> str:
        adjectifs = ["dynamique", "optimiste", "bienveillante", "curieuse", "passionnée"]
        import random
        return random.choice(adjectifs)
    
    def _get_trait_caractere(self) -> str:
        traits = ["une personne authentique", "quelqu'un de spontané", "une âme créative"]
        import random
        return random.choice(traits)
    
    def _get_trait_romantique(self) -> str:
        traits = ["Une romantique dans l'âme", "Quelqu'un qui croit aux belles histoires", "Une personne sensible"]
        import random
        return random.choice(traits)
    
    def _get_trait_confiant(self) -> str:
        traits = ["une personne assumée", "quelqu'un de confiant", "une personnalité affirmée"]
        import random
        return random.choice(traits)
    
    def _get_trait_seducteur(self) -> str:
        traits = ["magnétique", "envoûtante", "irrésistible", "captivante"]
        import random
        return random.choice(traits)
    
    def _get_description_courte(self) -> str:
        descriptions = ["une personne épanouie", "quelqu'un d'authentique", "une personnalité attachante"]
        import random
        return random.choice(descriptions)
    
    def _get_description_sensuelle(self) -> str:
        descriptions = ["une femme qui assume sa féminité", "une personnalité magnétique", "quelqu'un de naturellement séduisant"]
        import random
        return random.choice(descriptions)
    
    def _extraire_activite_principale(self, gouts: str) -> str:
        """Extrait l'activité principale des goûts"""
        gouts_lower = gouts.lower()
        if "sport" in gouts_lower:
            return "bouger et me dépenser"
        elif "lecture" in gouts_lower:
            return "me plonger dans de bons livres"
        elif "voyage" in gouts_lower:
            return "découvrir de nouveaux endroits"
        elif "musique" in gouts_lower:
            return "écouter de la musique"
        else:
            return "profiter de la vie"
    
    def _get_activite_sociale(self) -> str:
        activites = ["de nouvelles expériences", "des sorties entre amis", "des découvertes culturelles"]
        import random
        return random.choice(activites)
    
    def _extraire_activite_commune(self, gouts: str) -> str:
        """Extrait une activité commune des goûts"""
        gouts_lower = gouts.lower()
        if "sport" in gouts_lower:
            return "les activités sportives"
        elif "cinema" in gouts_lower:
            return "les soirées cinéma"
        elif "cuisine" in gouts_lower:
            return "les plaisirs culinaires"
        else:
            return "les belles découvertes"
    
    def _generer_conseils(self, personne: PersonneInput) -> List[str]:
        """Génère des conseils d'amélioration"""
        conseils = []
        
        if len(personne.physique) < 20:
            conseils.append("Ajoutez plus de détails sur votre apparence pour vous démarquer")
        
        if len(personne.gouts) < 30:
            conseils.append("Développez davantage vos centres d'intérêt pour susciter plus d'intérêt")
        
        if personne.recherche == "amoureuse":
            conseils.append("Mentionnez vos valeurs et ce que vous recherchez dans une relation")
        
        if not conseils:
            conseils.append("Votre profil est bien équilibré !")
        
        return conseils
    
    def _extraire_mots_cles(self, description: str) -> List[str]:
        """Extrait les mots-clés attractifs de la description"""
        mots_attractifs = [
            "authentique", "passionné", "dynamique", "bienveillant", "curieux",
            "élégant", "charme", "complice", "épanoui", "créatif"
        ]
        
        mots_trouves = []
        description_lower = description.lower()
        
        for mot in mots_attractifs:
            if mot in description_lower:
                mots_trouves.append(mot)
        
        return mots_trouves[:5]  # Maximum 5 mots-clés
    
    def _calculer_score_attractivite(self, description: str, personne: PersonneInput) -> int:
        """Calcule un score d'attractivité sur 100"""
        score = 50  # Score de base
        
        # Longueur optimale
        if 100 <= len(description) <= 300:
            score += 20
        elif len(description) > 300:
            score += 10
        
        # Diversité des goûts
        if len(personne.gouts.split(",")) >= 3:
            score += 15
        
        # Description physique détaillée
        if len(personne.physique) > 30:
            score += 15
        
        return min(score, 100)

# Instance du générateur
description_generator = DescriptionGenerator()

@app.post("/description/generer", response_model=DescriptionResponse)
async def generer_description(personne: PersonneInput):
    """Génère une description attractive d'une personne"""
    try:
        logger.info(f"🎯 Génération description pour {personne.prenom} (recherche: {personne.recherche})")
        
        # Générer la description
        result = description_generator.generer_description(personne)
        
        # Enregistrer en base de données
        try:
            conversation_id = db_service.log_conversation(
                prompt=f"Description de {personne.prenom}: {personne.physique} | {personne.gouts}",
                response=result["description"],
                provider="description_generator",
                processing_time=result["processing_time"],
                user_id=personne.user_id,
                system_prompt=f"Génération description {personne.recherche}",
                fallback_used=False,
                cost=0.001,
                voice_settings={"type": "description", "recherche": personne.recherche},
                audio_generated=False
            )
            logger.info(f"✅ Description enregistrée: conversation_id={conversation_id}")
        except Exception as db_error:
            logger.warning(f"⚠️ Erreur enregistrement BDD: {db_error}")
        
        return DescriptionResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Erreur génération description: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/description/exemples")
async def get_exemples_descriptions():
    """Retourne des exemples de descriptions par type de recherche"""
    exemples = {}
    
    for type_recherche in ["amical", "amoureuse", "libertin"]:
        exemple_personne = PersonneInput(
            prenom="Alex",
            physique="taille moyenne, sportif, cheveux bruns, yeux verts",
            gouts="sport, cinéma, voyage, cuisine",
            recherche=type_recherche,
            longueur="moyenne"
        )
        
        result = description_generator.generer_description(exemple_personne)
        exemples[type_recherche] = {
            "description": result["description"],
            "score": result["score_attractivite"]
        }
    
    return {
        "exemples": exemples,
        "conseils_generaux": [
            "Soyez authentique et positif",
            "Mentionnez vos passions avec enthousiasme", 
            "Évitez les clichés et soyez spécifique",
            "Adaptez le ton selon le type de relation recherchée"
        ]
    }

@app.get("/description/stats")
async def get_description_stats():
    """Statistiques de l'API de description"""
    return {
        "api": "Description Attractive",
        "version": "1.0",
        "types_recherche": ["amical", "amoureuse", "libertin"],
        "styles_disponibles": ["elegant", "decontracte", "seducteur", "authentique"],
        "longueurs": ["courte", "moyenne", "longue"],
        "score_max": 100,
        "features": [
            "Reformulation intelligente du physique",
            "Adaptation du ton selon la recherche",
            "Conseils d'amélioration personnalisés",
            "Score d'attractivité",
            "Mots-clés attractifs"
        ]
    }

@app.get("/")
async def root():
    return {
        "api": "MeetVoice Description Attractive",
        "description": "Génère des descriptions attractives pour profils de rencontre",
        "endpoint_principal": "/description/generer",
        "exemples": "/description/exemples",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
