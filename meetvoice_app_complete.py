#!/usr/bin/env python3
"""
MeetVoice App Complète - Tout-en-un
- TTS (Text-to-Speech)
- IA Chat (Gemini + DeepInfra)
- Description Attractive
- Questions d'inscription
- WebSocket temps réel
- Base de données PostgreSQL
"""

import asyncio
import json
import time
import base64
import hashlib
import os
import re
from typing import Dict, List, Optional, Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

import edge_tts
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import speech_recognition as sr
import io
import tempfile
import wave
from database import get_database_service
import logging

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App principale
app = FastAPI(title="MeetVoice App Complète", version="3.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8083",
        "http://localhost:8085",  # Frontend Vue.js
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8083",
        "http://127.0.0.1:8085",  # Frontend Vue.js
        "https://aaaazealmmmma.duckdns.org",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"],
    expose_headers=["Content-Length", "Content-Type"],
)

# Service de base de données
db_service = get_database_service()

# Configuration APIs externes
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DEEPINFRA_API_KEY = os.getenv('DEEPINFRA_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ================================
# MODÈLES DE DONNÉES
# ================================

class TTSRequest(BaseModel):
    text: str
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
    rate: str = "+0%"
    pitch: str = "+0Hz"

class IARequest(BaseModel):
    prompt: str = Field(..., description="Question/prompt pour l'IA")
    system_prompt: str = Field(default="Tu es Sophie, coach de séduction experte et bienveillante.", description="Prompt système")
    include_audio: bool = Field(default=True, description="Inclure la réponse audio")
    user_id: Optional[str] = Field(default="anonymous", description="ID utilisateur")
    prenom: Optional[str] = Field(default=None, description="Prénom de l'utilisateur pour personnaliser")
    voice: str = Field(default="Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)", description="Voix TTS")
    rate: str = Field(default="+0%", description="Vitesse de la voix")
    pitch: str = Field(default="+0Hz", description="Hauteur de la voix")

class DescriptionRequest(BaseModel):
    prenom: str = Field(..., description="Prénom de la personne")
    physique: str = Field(..., description="Description physique")
    gouts: str = Field(..., description="Goûts et centres d'intérêt")
    recherche: str = Field(..., description="Type de relation recherchée")
    user_id: str = Field(default="anonymous", description="ID utilisateur")
    style_description: str = Field(default="authentique", description="Style de description")
    # longueur supprimée - TOUJOURS version premium longue (service payant)

    @field_validator('recherche')
    @classmethod
    def validate_recherche(cls, v):
        v_lower = v.lower()
        if v_lower not in ["amical", "amoureuse", "libertin"]:
            raise ValueError("recherche doit être 'amical', 'amoureuse' ou 'libertin'")
        return v_lower

    @field_validator('style_description')
    @classmethod
    def validate_style(cls, v):
        v_lower = v.lower()
        if v_lower not in ["elegant", "decontracte", "seducteur", "authentique"]:
            raise ValueError("style_description doit être 'elegant', 'decontracte', 'seducteur' ou 'authentique'")
        return v_lower

    # Validateur longueur supprimé - toujours version premium

class FeedbackRequest(BaseModel):
    conversation_id: int
    rating: int  # 1-5
    comment: str = ""
    category: str = "general"
    improvement_suggestion: str = ""
    user_id: str = None

# ================================
# GESTIONNAIRE WEBSOCKET
# ================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"🔗 WebSocket connecté: {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"❌ WebSocket déconnecté: {user_id}")
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Erreur envoi WebSocket: {e}")
                self.disconnect(user_id)
                return False
        return False

manager = ConnectionManager()

# ================================
# FONCTIONS TTS
# ================================

async def generer_audio_tts(texte: str, voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)", rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Génère l'audio TTS avec Edge TTS"""
    try:
        # Nettoyer le texte
        texte_clean = re.sub(r'[^\w\s\.,!?;:-]', '', texte)
        
        # Générer l'audio
        communicate = edge_tts.Communicate(texte_clean, voice, rate=rate, pitch=pitch)
        audio_data = b""
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data
        
    except Exception as e:
        logger.error(f"Erreur TTS: {e}")
        return b""

async def generer_audio_tts_streaming(texte: str, voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)", rate: str = "+0%", pitch: str = "+0Hz"):
    """Génère l'audio TTS en streaming"""
    try:
        # Nettoyer le texte
        texte_clean = re.sub(r'[^\w\s\.,!?;:-]', '', texte)

        # Générer l'audio en streaming
        communicate = edge_tts.Communicate(texte_clean, voice, rate=rate, pitch=pitch)

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    except Exception as e:
        logger.error(f"Erreur TTS streaming: {e}")
        yield b""

async def transcrire_audio(audio_file: UploadFile) -> str:
    """Transcrit un fichier audio en texte"""
    try:
        # Lire le contenu du fichier audio
        audio_content = await audio_file.read()

        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name

        # Utiliser speech_recognition pour transcrire
        recognizer = sr.Recognizer()

        with sr.AudioFile(temp_file_path) as source:
            audio_data = recognizer.record(source)

        # Transcription avec Google Speech Recognition (gratuit)
        try:
            text = recognizer.recognize_google(audio_data, language='fr-FR')
            logger.info(f"🎤 Transcription: {text[:50]}...")
            return text
        except sr.UnknownValueError:
            return "Je n'ai pas pu comprendre l'audio"
        except sr.RequestError as e:
            logger.error(f"Erreur service transcription: {e}")
            return "Erreur de transcription"

    except Exception as e:
        logger.error(f"Erreur transcription audio: {e}")
        raise Exception(f"Erreur transcription: {str(e)}")
    finally:
        # Nettoyer le fichier temporaire
        try:
            os.unlink(temp_file_path)
        except:
            pass

# ================================
# FONCTIONS IA
# ================================

def repondre_questions_simples(prompt: str, prenom: str = None) -> str:
    """Répond aux questions simples personnalisées avec le prénom"""
    import datetime

    prompt_lower = prompt.lower()
    now = datetime.datetime.now()

    # Personnalisation avec le prénom
    nom = f" {prenom}" if prenom else ""

    # Salutations (priorité haute pour éviter confusion avec date)
    if any(word in prompt_lower for word in ["salut", "bonjour", "bonsoir", "hello", "hi", "coucou"]):
        if now.hour < 12:
            return f"Bonjour{nom} ! Ravie de te rencontrer ! Comment puis-je t'aider dans tes rencontres ?"
        elif now.hour < 18:
            return f"Salut{nom} ! Enchantée ! Prêt(e) à parler séduction ?"
        else:
            return f"Bonsoir{nom} ! Parfait timing pour une conversation coquine... Que puis-je faire pour toi ? 😉"

    # Questions sur l'heure
    elif any(word in prompt_lower for word in ["heure", "temps", "time", "quelle heure"]):
        heure = now.strftime("%H:%M")
        if now.hour >= 20 or now.hour <= 6:
            return f"Il est {heure}{nom}. Parfait pour une conversation intime ! 😉"
        else:
            return f"Il est {heure}{nom}. Une bonne heure pour faire connaissance !"

    # Questions sur la date/jour
    elif any(word in prompt_lower for word in ["jour", "date", "aujourd'hui", "quel jour", "nous sommes"]):
        jour = now.strftime("%A %d %B %Y")
        jour_fr = {
            "Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
            "Thursday": "jeudi", "Friday": "vendredi", "Saturday": "samedi", "Sunday": "dimanche",
            "January": "janvier", "February": "février", "March": "mars", "April": "avril",
            "May": "mai", "June": "juin", "July": "juillet", "August": "août",
            "September": "septembre", "October": "octobre", "November": "novembre", "December": "décembre"
        }
        for en, fr in jour_fr.items():
            jour = jour.replace(en, fr)

        if "vendredi" in jour or "samedi" in jour:
            return f"Nous sommes {jour}{nom}. Parfait pour planifier un rendez-vous ! 💕"
        else:
            return f"Nous sommes {jour}{nom}. Une belle journée pour faire de nouvelles rencontres !"

    # Questions météo
    elif any(word in prompt_lower for word in ["météo", "temps", "pluie", "soleil", "weather"]):
        return f"Peu importe le temps qu'il fait{nom}, l'important c'est la chimie entre nous ! Parlons plutôt de toi 😊"

    # Questions sur l'âge
    elif any(word in prompt_lower for word in ["âge", "age", "ans", "vieux", "vieille", "quel âge"]):
        return f"Une femme ne révèle jamais son âge{nom} ! Mais j'ai l'expérience qu'il faut pour t'aider à séduire 😉"

    # Questions sur la localisation
    elif any(word in prompt_lower for word in ["où", "habite", "vis", "location", "ville"]):
        return f"Je suis partout où il y a des cœurs à conquérir{nom} ! L'important c'est qu'on puisse discuter de tes rencontres."

    return None  # Pas une question simple

def appeler_gemini(prompt: str, system_prompt: str, prenom: str = None) -> str:
    """Appelle l'API Gemini avec gestion des questions simples personnalisées"""
    try:
        # D'abord vérifier si c'est une question simple
        reponse_simple = repondre_questions_simples(prompt, prenom)
        if reponse_simple:
            return reponse_simple

        # Sinon, utiliser Gemini avec un prompt enrichi
        model = genai.GenerativeModel('gemini-1.5-flash')

        # System prompt adapté au contexte site de rencontre avec personnalisation
        prenom_info = f"\n\nL'utilisateur s'appelle {prenom}. Utilise son prénom de temps en temps pour personnaliser tes réponses." if prenom else ""

        system_enrichi = f"""{system_prompt}

CONTEXTE: Nous sommes sur un site de rencontre. L'utilisateur cherche des conseils pour séduire, draguer, ou améliorer ses relations amoureuses/amicales/libertines.

Réponds de manière naturelle et directe, avec une pointe de complicité. Ramène toujours la conversation vers la séduction, les rencontres, ou les relations.{prenom_info}"""

        full_prompt = f"{system_enrichi}\n\nUtilisateur: {prompt}"

        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        logger.error(f"Erreur Gemini: {e}")
        raise Exception(f"Erreur Gemini: {str(e)}")

def appeler_deepinfra(prompt: str, system_prompt: str) -> str:
    """Appelle l'API DeepInfra"""
    try:
        url = "https://api.deepinfra.com/v1/openai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Erreur DeepInfra: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Erreur DeepInfra: {e}")
        raise Exception(f"Erreur DeepInfra: {str(e)}")

async def call_ai_hybrid(prompt: str, system_prompt: str, prenom: str = None) -> dict:
    """Appelle l'IA avec fallback automatique et personnalisation"""
    start_time = time.time()

    try:
        # Essayer Gemini d'abord avec personnalisation
        response = appeler_gemini(prompt, system_prompt, prenom)
        processing_time = time.time() - start_time
        
        return {
            "response": response,
            "provider": "gemini",
            "fallback_used": False,
            "cost": 0.0,  # Gemini gratuit
            "processing_time": processing_time
        }
        
    except Exception as gemini_error:
        logger.warning(f"Gemini échoué, fallback vers DeepInfra: {gemini_error}")
        
        try:
            # Fallback vers DeepInfra
            response = appeler_deepinfra(prompt, system_prompt)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "provider": "deepinfra",
                "fallback_used": True,
                "cost": 0.003,
                "processing_time": processing_time
            }
            
        except Exception as deepinfra_error:
            logger.error(f"Tous les providers IA ont échoué: {deepinfra_error}")
            raise HTTPException(status_code=503, detail="Service IA temporairement indisponible")

# ================================
# FONCTIONS DESCRIPTION ATTRACTIVE
# ================================

def generer_description_attractive(personne: DescriptionRequest) -> dict:
    """Génère une description attractive pour profil de rencontre"""
    
    # Templates par type de recherche - Version améliorée
    templates = {
        "amical": {
            "intro": "Salut ! Moi c'est {prenom}, {physique_reformule}.",
            "corps": "Dans la vie, {gouts_reformules}. J'aime les gens authentiques et les moments de partage.",
            "motivation": "Je suis ici parce que je crois qu'on n'a jamais assez d'amis sincères dans la vie. Après avoir déménagé récemment, ou simplement par envie d'élargir mon cercle social, je cherche des personnes avec qui créer de vraies connexions amicales.",
            "conclusion": "Si tu cherches une amitié sincère, des sorties sympas et des conversations enrichissantes, on devrait faire connaissance !",
            "extension": "Ce qui me caractérise ? J'ai cette capacité à voir le positif dans chaque situation et à transformer les moments ordinaires en souvenirs mémorables. Mes amis disent de moi que je suis quelqu'un sur qui on peut compter, toujours prêt à aider ou à partager un fou rire.\n\nJ'adore découvrir de nouveaux endroits, que ce soit un petit restaurant caché dans une ruelle ou un sentier de randonnée perdu en montagne. La spontanéité fait partie de ma personnalité - je peux aussi bien proposer une soirée cinéma improvisée qu'un week-end à l'aventure.\n\nJe crois fermement que les meilleures amitiés naissent des moments simples : un café qui se prolonge, une conversation qui nous fait oublier l'heure, ou ces instants où on rit tellement qu'on en a mal au ventre. Si tu es du genre à apprécier l'authenticité, les discussions profondes autant que les délires, et que tu cherches quelqu'un avec qui créer de vrais liens d'amitié, alors on a sûrement plein de choses à partager !"
        },
        "amoureuse": {
            "intro": "Je suis {prenom}, {physique_reformule}, et je crois encore aux belles rencontres.",
            "corps": "Dans la vie, {gouts_reformules}. J'aime profiter des petits plaisirs et partager mes passions.",
            "motivation": "Je suis ici parce que je suis prêt(e) à rencontrer quelqu'un de spécial. Après avoir pris le temps de me connaître et de savoir ce que je veux vraiment, je me sens prêt(e) à construire une relation authentique et durable avec la bonne personne.",
            "conclusion": "Je recherche quelqu'un avec qui construire une belle histoire d'amour et partager les joies de la vie à deux.",
            "extension": "Je suis de ceux qui pensent que l'amour, le vrai, se construit jour après jour dans les petites attentions et les grands projets partagés. J'aime ces matins où on se réveille avec l'envie de découvrir le monde à deux, ces soirées où on se raconte nos rêves en regardant les étoiles, et ces moments de complicité où un simple regard suffit à se comprendre. Dans une relation, je valorise la communication, l'humour et cette capacité à grandir ensemble tout en gardant sa propre personnalité. J'ai cette vision romantique de l'amour où chaque jour peut être une nouvelle aventure, où on se soutient dans les défis et où on célèbre ensemble les victoires, même les plus petites. Je rêve de ces week-ends où on se perd dans une nouvelle ville, de ces soirées cuisine où on invente des recettes improbables, et de ces projets fous qu'on réalise à deux. Si tu cherches quelqu'un avec qui écrire une belle histoire, quelqu'un qui croit encore aux papillons dans le ventre et aux projets d'avenir partagés, alors peut-être qu'on est faits pour se rencontrer."
        },
        "libertin": {
            "intro": "Salut, moi c'est {prenom}, {physique_reformule}, et j'assume pleinement qui je suis.",
            "corps": "Dans la vie, {gouts_reformules}. J'aime les plaisirs de la vie et les expériences enrichissantes.",
            "motivation": "Je suis ici parce que je vis ma sexualité de manière épanouie et décomplexée. Je cherche des personnes qui, comme moi, assument leurs désirs et souhaitent explorer de nouvelles expériences dans un cadre de respect mutuel et de bienveillance.",
            "conclusion": "Si tu cherches quelqu'un avec qui passer de bons moments intenses et découvrir de nouveaux plaisirs, contacte-moi !",
            "extension": "Je suis quelqu'un qui vit sa sexualité de manière épanouie et décomplexée, toujours dans le respect et la bienveillance. Pour moi, la séduction est un art qui se cultive, fait de regards complices, de conversations stimulantes et de cette chimie particulière qui naît entre deux personnes qui se comprennent. J'apprécie les rencontres authentiques où on peut être soi-même sans jugement, où la complicité se construit naturellement et où chacun peut exprimer ses désirs en toute liberté. Je privilégie la qualité à la quantité, préférant des connexions vraies et intenses aux relations superficielles. L'intelligence et l'humour sont pour moi des aphrodisiaques puissants - j'adore ces conversations qui commencent autour d'un verre et qui nous mènent vers des territoires inexplorés. Je crois en l'importance du consentement, de la communication et de cette capacité à créer ensemble des moments uniques et mémorables. Si tu es une personne ouverte, curieuse, qui assume ses désirs et cherche des expériences enrichissantes dans un cadre de respect mutuel, alors nous avons probablement des affinités à explorer."
        }
    }
    
    # Reformulations intelligentes
    def reformuler_physique(physique: str) -> str:
        """Transforme une description technique en description attractive"""
        physique_lower = physique.lower()

        # Extraire les informations clés
        taille = ""
        if "180cm" in physique or "1m80" in physique:
            taille = "grand"
        elif "170cm" in physique or "1m70" in physique:
            taille = "de taille moyenne"
        elif "taille" in physique_lower:
            taille = "bien proportionné"

        yeux = ""
        if "noisette" in physique_lower:
            yeux = "au regard noisette"
        elif "bleu" in physique_lower:
            yeux = "aux yeux bleus"
        elif "vert" in physique_lower:
            yeux = "aux yeux verts"
        elif "marron" in physique_lower:
            yeux = "au regard brun"

        cheveux = ""
        if "rasé" in physique_lower or "chauve" in physique_lower:
            cheveux = "au style assumé"
        elif "noir" in physique_lower:
            cheveux = "aux cheveux noirs"
        elif "brun" in physique_lower:
            cheveux = "aux cheveux bruns"
        elif "blond" in physique_lower:
            cheveux = "aux cheveux blonds"

        style = ""
        if "sportif" in physique_lower or "sport" in physique_lower:
            style = "sportif"
        elif "élégant" in physique_lower:
            style = "élégant"
        else:
            style = "au charme naturel"

        # Construire une description fluide
        elements = [e for e in [taille, style, cheveux, yeux] if e]
        if elements:
            return ", ".join(elements[:3])  # Max 3 éléments pour éviter la surcharge
        else:
            return "au charme naturel"
    
    def reformuler_gouts(gouts: str) -> str:
        """Transforme une liste de goûts en description narrative attractive"""
        gouts_lower = gouts.lower()

        # Extraire les activités par catégorie
        sports = []
        if "sport en salle" in gouts_lower or "musculation" in gouts_lower:
            sports.append("la musculation")
        if "course" in gouts_lower or "running" in gouts_lower:
            sports.append("la course à pied")
        if "aviron" in gouts_lower:
            sports.append("l'aviron")
        if "échecs" in gouts_lower:
            sports.append("les échecs")

        loisirs = []
        if "cinéma" in gouts_lower or "films" in gouts_lower:
            loisirs.append("le cinéma")
        if "restaurant" in gouts_lower:
            loisirs.append("la gastronomie")
        if "musique" in gouts_lower:
            loisirs.append("la musique")
        if "voyage" in gouts_lower:
            loisirs.append("les voyages")
        if "pilotage" in gouts_lower:
            loisirs.append("l'aviation")

        # Construire une phrase naturelle
        passions = []

        if sports:
            if len(sports) == 1:
                passions.append(f"je pratique {sports[0]}")
            else:
                passions.append(f"je suis passionné de sport ({', '.join(sports[:2])})")

        if loisirs:
            if len(loisirs) == 1:
                passions.append(f"j'adore {loisirs[0]}")
            elif len(loisirs) == 2:
                passions.append(f"j'apprécie {loisirs[0]} et {loisirs[1]}")
            else:
                passions.append(f"j'aime {', '.join(loisirs[:2])} entre autres")

        # Ajouter des traits de caractère s'ils sont mentionnés
        if "intelligent" in gouts_lower:
            passions.append("j'aime les défis intellectuels")
        if "charismatique" in gouts_lower:
            passions.append("j'aime rencontrer de nouvelles personnes")

        if passions:
            return ". ".join(passions[:3])  # Max 3 phrases
        else:
            return "j'ai de nombreux centres d'intérêt variés"
    
    # Variables pour le template
    template = templates[personne.recherche]
    variables = {
        "prenom": personne.prenom,
        "physique_reformule": reformuler_physique(personne.physique),
        "gouts_reformules": reformuler_gouts(personne.gouts),
        "trait": "dynamique" if personne.recherche == "amical" else "authentique",
        "trait_sensuel": "une personne assumée",
        "activite": "découvrir de nouvelles choses"
    }
    
    # TOUJOURS générer la version PREMIUM LONGUE (service payant)
    # Description complète avec tous les éléments pour maximiser la valeur
    description = f"{template['intro'].format(**variables)}\n\n{template['corps'].format(**variables)}\n\n{template['motivation']}\n\n{template['extension']}\n\n{template['conclusion'].format(**variables)}"
    
    # Calculer le score d'attractivité PREMIUM
    score = 70  # Base plus élevée pour service premium
    if len(personne.physique) > 30: score += 15
    if len(personne.gouts) > 40: score += 15
    # Bonus pour version premium complète
    score += 10  # Bonus motivation
    score += 10  # Bonus extension
    score += 5   # Bonus paragraphes structurés
    
    # Conseils
    conseils = []
    if len(personne.physique) < 20:
        conseils.append("Ajoutez plus de détails sur votre apparence")
    if len(personne.gouts) < 30:
        conseils.append("Développez davantage vos centres d'intérêt")
    if not conseils:
        conseils.append("Votre profil est bien équilibré !")
    
    # Mots-clés attractifs
    mots_cles = []
    description_lower = description.lower()
    for mot in ["authentique", "passionné", "dynamique", "charme", "découvrir"]:
        if mot in description_lower:
            mots_cles.append(mot)
    
    return {
        "description": description,
        "conseils_amelioration": conseils,
        "mots_cles_attractifs": mots_cles[:5],
        "score_attractivite": min(score, 100),
        "style_utilise": personne.style_description
    }

# ================================
# ENDPOINTS
# ================================

@app.get("/")
async def root():
    return {
        "app": "MeetVoice App Complète",
        "version": "3.0",
        "description": "TTS + IA + Description Attractive + WebSocket",
        "endpoints": {
            "tts": "POST /tts",
            "ia": "POST /ia",
            "description": "POST /description",
            "questions": "GET /inscription/question/{numero}",
            "websocket": "WS /ws/chat/{user_id}",
            "feedback": "POST /feedback",
            "stats": "GET /stats"
        },
        "features": [
            "🎵 Text-to-Speech (Edge TTS)",
            "🤖 IA Hybride (Gemini + DeepInfra)",
            "🎯 Description Attractive",
            "📝 Questions d'inscription",
            "⚡ WebSocket temps réel",
            "💾 Base de données PostgreSQL"
        ]
    }

@app.post("/tts")
async def generate_tts(request: TTSRequest):
    """🎵 Génère l'audio TTS"""
    try:
        start_time = time.time()

        logger.info(f"🎵 Génération TTS: {request.text[:50]}...")

        # Générer l'audio
        audio_data = await generer_audio_tts(request.text, request.voice, request.rate, request.pitch)

        if not audio_data:
            raise HTTPException(status_code=500, detail="Erreur génération audio")

        processing_time = time.time() - start_time

        # Enregistrer en base
        try:
            conversation_id = db_service.log_conversation(
                prompt=f"TTS: {request.text}",
                response="Audio généré",
                provider="edge_tts",
                processing_time=processing_time,
                user_id="tts_user",
                system_prompt="Génération TTS",
                fallback_used=False,
                cost=0.0,  # TTS gratuit (Edge)
                voice_settings={"voice": request.voice, "rate": request.rate, "pitch": request.pitch},
                audio_generated=True
            )
        except Exception as db_error:
            logger.warning(f"Erreur BDD TTS: {db_error}")

        # Retourner l'audio en base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return {
            "audio": f"data:audio/mp3;base64,{audio_base64}",
            "text": request.text,
            "voice": request.voice,
            "processing_time": processing_time,
            "size": len(audio_data)
        }

    except Exception as e:
        logger.error(f"Erreur TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vocal")
async def conversation_vocale_streaming(
    audio_file: UploadFile = File(...),
    prenom: str = None,
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)",
    rate: str = "+0%",
    pitch: str = "+0Hz"
):
    """🎤 Conversation vocale pure avec streaming audio

    Upload un fichier audio → Transcription → IA → Streaming audio de la réponse
    Plus rapide et plus naturel que l'endpoint texte classique !
    """
    try:
        start_time = time.time()

        logger.info(f"🎤 Conversation vocale: {audio_file.filename} (prenom: {prenom})")

        # 1. Transcription audio → texte
        transcription_start = time.time()
        prompt = await transcrire_audio(audio_file)
        transcription_time = time.time() - transcription_start

        if not prompt or prompt in ["Je n'ai pas pu comprendre l'audio", "Erreur de transcription"]:
            # Réponse d'erreur en audio
            error_text = "Désolée, je n'ai pas bien compris. Peux-tu répéter ?"
            return StreamingResponse(
                generer_audio_tts_streaming(error_text, voice, rate, pitch),
                media_type="audio/mp3",
                headers={"X-Error": "transcription_failed"}
            )

        logger.info(f"🎤 Transcrit en {transcription_time:.3f}s: {prompt[:50]}...")

        # 2. Traitement IA
        ia_start = time.time()
        system_prompt = "Tu es Sophie, coach de séduction experte et bienveillante."
        ai_result = await call_ai_hybrid(prompt, system_prompt, prenom)
        ia_time = time.time() - ia_start

        logger.info(f"🤖 IA répondu en {ia_time:.3f}s: {ai_result['response'][:50]}...")

        # 3. Enregistrer en base (en arrière-plan)
        total_time = time.time() - start_time
        try:
            db_service = get_database_service()
            db_service.log_conversation(
                prompt=prompt,
                response=ai_result["response"],
                provider=f"vocal_{ai_result['provider']}",
                processing_time=total_time,
                user_id=prenom or "vocal_user",
                system_prompt=system_prompt,
                fallback_used=ai_result["fallback_used"],
                cost=ai_result["cost"],
                voice_settings={"voice": voice, "rate": rate, "pitch": pitch, "transcription_time": transcription_time},
                audio_generated=True
            )
        except Exception as db_error:
            logger.warning(f"⚠️ Erreur BDD vocal: {db_error}")

        # 4. Streaming de la réponse audio
        logger.info(f"🎵 Streaming audio de la réponse...")

        return StreamingResponse(
            generer_audio_tts_streaming(ai_result["response"], voice, rate, pitch),
            media_type="audio/mp3",
            headers={
                "X-Transcription-Time": str(transcription_time),
                "X-IA-Time": str(ia_time),
                "X-Total-Time": str(total_time),
                "X-Provider": ai_result["provider"],
                "X-Transcription": prompt[:100]  # Pour debug
            }
        )

    except Exception as e:
        logger.error(f"❌ Erreur conversation vocale: {e}")
        # Réponse d'erreur en audio
        error_text = "Désolée, il y a eu un problème technique. Peux-tu réessayer ?"
        return StreamingResponse(
            generer_audio_tts_streaming(error_text, voice, rate, pitch),
            media_type="audio/mp3",
            headers={"X-Error": str(e)}
        )

@app.post("/ia")
async def chat_ia(request: IARequest):
    """🤖 Chat avec l'IA (Gemini + DeepInfra)"""
    try:
        start_time = time.time()

        logger.info(f"🤖 Chat IA: {request.prompt[:50]}...")

        # Appeler l'IA hybride avec personnalisation
        ai_result = await call_ai_hybrid(request.prompt, request.system_prompt, request.prenom)

        # Générer l'audio si demandé
        audio_data = None
        if request.include_audio:
            audio_data = await generer_audio_tts(ai_result["response"], request.voice, request.rate, request.pitch)

        total_time = time.time() - start_time

        # Enregistrer en base
        try:
            conversation_id = db_service.log_conversation(
                prompt=request.prompt,
                response=ai_result["response"],
                provider=ai_result["provider"],
                processing_time=total_time,
                user_id=request.user_id,
                system_prompt=request.system_prompt,
                fallback_used=ai_result["fallback_used"],
                cost=ai_result["cost"],
                voice_settings={"voice": request.voice, "rate": request.rate, "pitch": request.pitch},
                audio_generated=request.include_audio
            )
        except Exception as db_error:
            logger.warning(f"Erreur BDD IA: {db_error}")

        # Réponse simplifiée pour le frontend
        response_data = {
            "response": ai_result["response"]
        }

        if audio_data:
            response_data["audio"] = f"data:audio/mp3;base64,{base64.b64encode(audio_data).decode()}"

        return response_data

    except Exception as e:
        logger.error(f"Erreur IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/description")
async def generer_description(personne: DescriptionRequest):
    """🎯 Génère une description attractive PREMIUM pour profil de rencontre

    Service payant - Toujours la version longue et complète avec :
    - Introduction personnalisée
    - Description des passions reformulées
    - Motivation claire (pourquoi sur le site)
    - Extension détaillée selon le type de relation
    - Conclusion engageante
    - Paragraphes structurés pour une lecture optimale
    """
    try:
        start_time = time.time()

        logger.info(f"🎯 Génération description pour {personne.prenom} (recherche: {personne.recherche})")

        # Générer la description
        result = generer_description_attractive(personne)

        processing_time = time.time() - start_time
        # Garder seulement la description pour le frontend
        simplified_result = {"description": result["description"]}

        # Enregistrer en base de données
        try:
            conversation_id = db_service.log_conversation(
                prompt=f"Description de {personne.prenom}: {personne.physique} | {personne.gouts}",
                response=simplified_result["description"],
                provider="description_generator",
                processing_time=processing_time,
                user_id=personne.user_id,
                system_prompt=f"Génération description {personne.recherche}",
                fallback_used=False,
                cost=0.0,  # Description gratuite
                voice_settings={"type": "description", "recherche": personne.recherche},
                audio_generated=False
            )
            # Conversation enregistrée mais pas retournée au frontend
            logger.info(f"✅ Description enregistrée: conversation_id={conversation_id}")
        except Exception as db_error:
            logger.warning(f"⚠️ Erreur enregistrement BDD: {db_error}")

        return simplified_result

    except Exception as e:
        logger.error(f"❌ Erreur génération description: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inscription/question/{numero}")
async def get_question_audio(numero: int):
    """📝 Récupère l'audio d'une question d'inscription"""
    try:
        if not (1 <= numero <= 30):
            raise HTTPException(status_code=400, detail="Numéro de question invalide (1-30)")

        # Questions d'inscription prédéfinies
        questions = {
            1: "Bonjour ! Bienvenue dans votre parcours de développement personnel. Pouvez-vous me dire votre prénom ?",
            2: "Parfait ! Maintenant, parlez-moi un peu de vous. Que faites-vous dans la vie ?",
            3: "Très intéressant ! Quels sont vos principaux centres d'intérêt et passions ?",
            4: "Excellent ! Dans quels domaines aimeriez-vous progresser en matière de séduction ?",
            5: "Merci pour ces informations. Avez-vous déjà eu des expériences en coaching personnel ?"
        }

        if numero not in questions:
            # Question générique pour les numéros non définis
            question_text = f"Question {numero} : Pouvez-vous développer votre réponse précédente ?"
        else:
            question_text = questions[numero]

        # Générer l'audio de la question
        audio_data = await generer_audio_tts(
            question_text,
            "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail="Erreur génération audio question")

        # Enregistrer en base
        try:
            db_service.log_conversation(
                prompt=f"Question inscription {numero}",
                response=question_text,
                provider="inscription_questions",
                processing_time=0.5,
                user_id="inscription_system",
                system_prompt="Questions d'inscription",
                fallback_used=False,
                cost=0.0,  # Questions gratuites
                voice_settings={"type": "question", "numero": numero},
                audio_generated=True
            )
        except Exception as db_error:
            logger.warning(f"Erreur BDD question: {db_error}")

        # Retourner l'audio directement
        from fastapi.responses import Response
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=question_{numero}.mp3",
                "Cache-Control": "public, max-age=3600"
            }
        )

    except Exception as e:
        logger.error(f"Erreur question {numero}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inscription/info")
async def get_inscription_info():
    """📋 Informations sur les questions d'inscription"""
    return {
        "total_questions": 30,
        "questions_disponibles": list(range(1, 31)),
        "format_audio": "MP3",
        "voix": "Denise (Français)",
        "duree_moyenne": "5-10 secondes par question",
        "endpoint": "/inscription/question/{numero}"
    }

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """💬 Soumettre un feedback sur une conversation"""
    try:
        # Enregistrer le feedback en base
        feedback_id = db_service.log_feedback(
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            comment=feedback.comment,
            category=feedback.category,
            improvement_suggestion=feedback.improvement_suggestion,
            user_id=feedback.user_id
        )

        logger.info(f"📝 Feedback enregistré: {feedback_id}")

        return {
            "feedback_id": feedback_id,
            "message": "Feedback enregistré avec succès",
            "rating": feedback.rating,
            "category": feedback.category
        }

    except Exception as e:
        logger.error(f"Erreur feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """📊 Statistiques générales de l'application"""
    try:
        stats = db_service.get_system_stats()

        return {
            "app": "MeetVoice App Complète",
            "version": "3.0",
            "stats": stats,
            "websocket_connections": len(manager.active_connections),
            "features_actives": [
                "TTS Edge",
                "IA Hybride (Gemini + DeepInfra)",
                "Description Attractive",
                "Questions d'inscription",
                "WebSocket temps réel",
                "Base de données PostgreSQL"
            ],
            "endpoints_disponibles": {
                "tts": "POST /tts",
                "ia": "POST /ia",
                "description": "POST /description",
                "questions": "GET /inscription/question/{numero}",
                "websocket": "WS /ws/chat/{user_id}",
                "feedback": "POST /feedback"
            }
        }

    except Exception as e:
        logger.error(f"Erreur stats: {e}")
        return {
            "app": "MeetVoice App Complète",
            "version": "3.0",
            "error": "Erreur récupération statistiques",
            "websocket_connections": len(manager.active_connections)
        }

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """⚡ WebSocket pour chat temps réel avec l'IA"""
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Recevoir le message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            prompt = message_data.get("prompt", "")
            system_prompt = message_data.get("system_prompt", "Tu es Sophie, coach de séduction experte.")
            include_audio = message_data.get("include_audio", True)
            voice = message_data.get("voice", "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)")

            if not prompt:
                continue

            # Indiquer le début du traitement
            await manager.send_message(user_id, {
                "type": "processing_start",
                "message": "Sophie réfléchit..."
            })

            try:
                # Appeler l'IA
                ai_result = await call_ai_hybrid(prompt, system_prompt)

                # Envoyer la réponse texte
                await manager.send_message(user_id, {
                    "type": "text_response",
                    "content": ai_result["response"],
                    "provider": ai_result["provider"],
                    "fallback_used": ai_result["fallback_used"]
                })

                # Générer et envoyer l'audio si demandé
                if include_audio:
                    await manager.send_message(user_id, {
                        "type": "audio_generation_start",
                        "message": "Génération de l'audio..."
                    })

                    audio_data = await generer_audio_tts(ai_result["response"], voice)

                    if audio_data:
                        await manager.send_message(user_id, {
                            "type": "audio_complete",
                            "audio": f"data:audio/mp3;base64,{base64.b64encode(audio_data).decode()}"
                        })

                # Enregistrer en base
                try:
                    conversation_id = db_service.log_conversation(
                        prompt=prompt,
                        response=ai_result["response"],
                        provider=f"websocket_{ai_result['provider']}",
                        processing_time=ai_result["processing_time"],
                        user_id=user_id,
                        system_prompt=system_prompt,
                        fallback_used=ai_result["fallback_used"],
                        cost=ai_result["cost"],
                        voice_settings={"voice": voice, "websocket": True},
                        audio_generated=include_audio
                    )

                    await manager.send_message(user_id, {
                        "type": "conversation_complete",
                        "conversation_id": conversation_id,
                        "total_time": ai_result["processing_time"]
                    })

                except Exception as db_error:
                    logger.warning(f"Erreur BDD WebSocket: {db_error}")

            except Exception as ai_error:
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": f"Erreur IA: {str(ai_error)}"
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        manager.disconnect(user_id)

# ================================
# POINT D'ENTRÉE
# ================================

if __name__ == "__main__":
    import uvicorn

    print("🚀 Démarrage MeetVoice App Complète")
    print("=" * 50)
    print("📋 Fonctionnalités disponibles :")
    print("   🎵 TTS (Text-to-Speech)")
    print("   🤖 IA Hybride (Gemini + DeepInfra)")
    print("   🎯 Description Attractive")
    print("   📝 Questions d'inscription")
    print("   ⚡ WebSocket temps réel")
    print("   💾 Base de données PostgreSQL")
    print("=" * 50)
    print("🌐 Endpoints principaux :")
    print("   POST /tts")
    print("   POST /ia")
    print("   POST /description")
    print("   GET  /inscription/question/{numero}")
    print("   WS   /ws/chat/{user_id}")
    print("   POST /feedback")
    print("   GET  /stats")
    print("=" * 50)
    print("🔗 URL : https://aaaazealmmmma.duckdns.org")
    print("📚 Documentation : https://aaaazealmmmma.duckdns.org/docs")

    uvicorn.run(app, host="0.0.0.0", port=8012)
