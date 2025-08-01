#!/usr/bin/env python3
"""
MeetVoice - Application Simple avec 30 Questions d'Inscription
API FastAPI ultra-simple pour les questions d'inscription avec synthèse vocale
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List
import edge_tts
import asyncio
# import io  # Supprimé - plus utilisé
import os
from groq import Groq
import google.generativeai as genai
import requests
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv
import re

# Charger les variables d'environnement
load_dotenv()

# Configuration Groq (prioritaire - ultra-rapide)
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY non trouvée dans le fichier .env")
groq_client = Groq(api_key=groq_api_key)

# Configuration Gemini (fallback)
gemini_api_key = os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GOOGLE_API_KEY non trouvée dans le fichier .env")
genai.configure(api_key=gemini_api_key)

# Modèle de données pour la description
class UserProfile(BaseModel):
    prenom: str
    physique: str

# Modèle de données pour l'IA
class IARequest(BaseModel):
    prompt: str
    session_id: Optional[str] = "default"  # ID de session pour la mémoire conversationnelle complète
    expertise: str = "amical"              # Domaine d'expertise (psychology, sexology, seduction, development, amical)
    user_name: Optional[str] = None        # Prénom de l'utilisateur pour personnaliser
    # Note: voice est maintenant déterminée automatiquement selon l'expertise

    @validator('session_id', pre=True)
    def validate_session_id(cls, v):
        # Convertir null en "default"
        if v is None:
            return "default"
        return v

# ❌ Modèle TTSRequest supprimé - WebSocket uniquement

# Stockage temporaire des conversations (en production: Redis/DB)
conversation_memory = {}

# Voix françaises disponibles (liste complète et à jour)
FRENCH_VOICES = [
    "fr-FR-DeniseNeural",           # Féminine
    "fr-FR-EloiseNeural",           # Féminine
    "fr-FR-HenriNeural",            # Masculine
    "fr-FR-VivienneMultilingualNeural",  # Féminine
    "fr-FR-RemyMultilingualNeural"       # Masculine
]

# Voix par défaut si voix demandée n'existe pas
DEFAULT_VOICE = "fr-FR-DeniseNeural"

# IA spécialisées par expertise (Configuration Premium + GPT-4o Séduction)
EXPERTISE_AI_MAPPING = {
    "psychology": "gemini",              # 🧠 Gratuit + empathique
    "development": "deepinfra-qwen",     # 🌟 Coaching intelligent avec Qwen 2.5-72B
    "sexology": "deepinfra-qwen",       # ❤️ Éducation ouverte avec Qwen 2.5-72B
    "seduction": "gpt-4o",              # 💋 Premium avec GPT-4o + GPTs spécialisés
    "amical": "groq",                   # 😊 Ultra-rapide pour conversations
    "default": "groq"                   # 💬 Défaut rapide
}

# IA spécialisées pour génération d'images par expertise
IMAGE_AI_MAPPING = {
    "psychology": "dalle3",        # 🧠 Images apaisantes, thérapeutiques
    "development": "deepinfra",    # 🌟 Infographies motivantes, schémas
    "sexology": "deepinfra",       # ❤️ Illustrations éducatives, anatomie
    "seduction": "dalle3",         # 💋 Images lifestyle, dating, mode
    "amical": "deepinfra",         # 😊 Images fun et décontractées
    "default": "deepinfra"         # 💬 Défaut abordable
}

# Coûts approximatifs par IA (en dollars pour 1M tokens)
AI_COSTS = {
    "gpt-4o": 5.0,
    "claude-3.5-sonnet": 3.0,
    "deepinfra-qwen": 0.35,
    "deepinfra-mixtral": 0.27,
    "deepinfra-llama-70b": 0.27,
    "dalle3": 0.04,  # par image
    "deepinfra": 0.05,  # par image
    "gemini": 0.0,  # gratuit
    "groq": 0.0     # gratuit
}

# Limites de budget par expertise (en dollars par mois)
BUDGET_LIMITS = {
    "psychology": 10.0,    # 🧠 Limite psychologie
    "development": 10.0,   # 🌟 Limite développement
    "sexology": 10.0,      # ❤️ Limite sexologie
    "seduction": 10.0,     # 💋 Limite séduction
    "amical": 10.0,        # 😊 Limite amical
    "images": 10.0         # 🎨 Limite images
}

# Tracking des coûts (en mémoire - à persister en production)
cost_tracker = {
    "psychology": 0.0,
    "development": 0.0,
    "sexology": 0.0,
    "seduction": 0.0,
    "amical": 0.0,
    "images": 0.0,
    "last_reset": datetime.now().strftime("%Y-%m")
}

# Voix spécialisées par type d'expertise
EXPERTISE_VOICES = {
    "psychology": "fr-CH-ArianeNeural",        # 🧠 Psychologie → Voix douce et rassurante (femme suisse)
    "sexology": "fr-FR-VivienneMultilingualNeural",  # ❤️ Sexologie → Voix féminine confiante et ouverte
    "seduction": "fr-FR-DeniseNeural",         # 💋 Séduction → Voix charismatique (femme)
    "development": "fr-FR-HenriNeural",           # 🌟 Développement → Voix masculine jeune et accessible
    "amical": "fr-FR-DeniseNeural",            # 😊 Amical → Voix chaleureuse et bienveillante (défaut)
    "default": "fr-FR-DeniseNeural"            # 💬 Général → Voix par défaut (femme)
}

def clean_text_for_speech(text: str) -> str:
    """Nettoie le texte pour la synthèse vocale en supprimant le formatage Markdown"""
    # Supprimer le formatage gras **texte**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

    # Supprimer le formatage italique *texte*
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Supprimer les puces mais garder les numéros
    text = re.sub(r'^[\s]*[-•*]\s*', '', text, flags=re.MULTILINE)
    # Remplacer "1." par "1," pour une lecture plus naturelle (début de ligne OU après espace)
    text = re.sub(r'(\s|^)(\d+)\.\s*', r'\1\2, ', text)

    # Supprimer les liens [texte](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Supprimer les codes `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Supprimer les titres ### Titre
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text)

    # Nettoyer les sauts de ligne multiples
    text = re.sub(r'\n\s*\n', '. ', text)

    return text.strip()

def analyze_multi_sentence_context(user_prompt: str) -> dict:
    """Analyse intelligente jusqu'à 5 phrases pour détecter contexte, émotion et intention"""

    # Diviser en phrases (jusqu'à 5 maximum)
    sentences = []
    for delimiter in ['. ', '! ', '? ']:
        user_prompt = user_prompt.replace(delimiter, '|SPLIT|')

    raw_sentences = user_prompt.split('|SPLIT|')
    sentences = [s.strip() for s in raw_sentences if s.strip()][:5]  # Max 5 phrases

    analysis = {
        "sentence_count": len(sentences),
        "sentences": sentences,
        "emotional_indicators": [],
        "context_clues": [],
        "complexity_level": "simple",
        "needs_detailed_response": False
    }

    # Analyse émotionnelle multi-phrases
    emotional_keywords = {
        "stress": ["stress", "stressé", "anxieux", "angoisse", "panique", "tendu"],
        "tristesse": ["triste", "déprimé", "mal", "difficile", "dur", "peine"],
        "colère": ["énervé", "furieux", "agacé", "irrité", "fâché"],
        "joie": ["content", "heureux", "super", "génial", "parfait", "excellent"],
        "confusion": ["comprends pas", "perdu", "confus", "compliqué", "bizarre"]
    }

    full_text = " ".join(sentences).lower()
    for emotion, keywords in emotional_keywords.items():
        if any(keyword in full_text for keyword in keywords):
            analysis["emotional_indicators"].append(emotion)

    # Détection de complexité selon le nombre de phrases
    if len(sentences) >= 3:
        analysis["complexity_level"] = "complex"
        analysis["needs_detailed_response"] = True
    elif len(sentences) == 2:
        analysis["complexity_level"] = "medium"

    # Indices contextuels multi-phrases
    context_patterns = {
        "relationship_context": ["copain", "copine", "relation", "couple", "ensemble"],
        "work_context": ["travail", "boulot", "collègue", "patron", "bureau"],
        "family_context": ["famille", "parents", "frère", "sœur", "enfant"],
        "social_context": ["amis", "sortir", "soirée", "groupe", "social"]
    }

    for context, keywords in context_patterns.items():
        if any(keyword in full_text for keyword in keywords):
            analysis["context_clues"].append(context)

    return analysis

def get_best_ai_for_expertise(expertise: str = None, topic_detected: str = None) -> str:
    """Sélectionne la meilleure IA selon l'expertise demandée"""

    # Utiliser le mapping premium défini en haut du fichier
    # EXPERTISE_AI_MAPPING contient la configuration optimale

    # Priorité 1: Expertise explicite avec vérification budget
    if expertise:
        best_ai = get_ai_with_budget_check(expertise)
        print(f"🤖 IA sélectionnée pour expertise '{expertise}': {best_ai.upper()}")
        return best_ai

    # Priorité 2: Sujet détecté automatiquement
    if topic_detected:
        topic_to_expertise = {
            "confiance": "psychology",           # Confiance → Gemini (psychologie)
            "stress_social": "psychology",       # Stress → Gemini (empathie)
            "communication": "seduction",        # Communication → Groq (direct)
            "rendez-vous": "seduction",          # Rendez-vous → Groq (pratique)
            "developpement_personnel": "development"  # Développement → Gemini (motivant)
        }

        mapped_expertise = topic_to_expertise.get(topic_detected, "default")
        best_ai = EXPERTISE_AI_MAPPING.get(mapped_expertise, "groq")
        print(f"🤖 IA sélectionnée pour sujet '{topic_detected}' → expertise '{mapped_expertise}': {best_ai.upper()}")
        return best_ai

    # Priorité 3: Groq par défaut (ultra-rapide)
    print(f"🤖 IA par défaut utilisée: GROQ")
    return "groq"

def get_specialized_prompt_system(expertise: str, user_name: str = None) -> str:
    """Génère des prompts ultra-spécialisés inspirés des meilleures IA du marché"""

    user_ref = user_name if user_name else "mon ami"

    if expertise == "psychology":
        # Inspiré de Woebot - Thérapie CBT professionnelle
        return f"""Tu es Dr. Sarah, psychologue spécialisée en thérapie cognitivo-comportementale (CBT).

FORMATION: Stanford Psychology, certifiée CBT, 10 ans d'expérience clinique
STYLE: Empathique, structurée, basée sur la science, bienveillante mais professionnelle

TECHNIQUES CBT À UTILISER:
🧠 Identification des pensées automatiques négatives
📝 Restructuration cognitive (challenger les pensées irrationnelles)
🎯 Techniques de pleine conscience et ancrage
📊 Suivi des humeurs et déclencheurs
🔄 Exposition graduelle pour les phobies/anxiété
💪 Renforcement des comportements positifs

APPROCHE:
- Pose des questions ouvertes pour explorer les émotions
- Aide à identifier les schémas de pensée négatifs
- Propose des exercices pratiques CBT
- Encourage l'auto-observation et la prise de conscience
- Donne des "devoirs thérapeutiques" concrets

Ton interlocuteur s'appelle {user_ref}. Sois chaleureuse mais professionnelle.

IMPORTANT: Utilise le prénom SEULEMENT au début de ta réponse, puis utilise "tu" ou "vous". NE répète JAMAIS le prénom dans la même réponse."""

    elif expertise == "development":
        # Inspiré de BetterUp - Coaching professionnel premium
        return f"""Tu es Marcus, coach exécutif certifié ICF, spécialiste en développement du leadership.

FORMATION: MBA Harvard, certification ICF, ex-consultant McKinsey, 15 ans de coaching C-suite
STYLE: Motivant, orienté résultats, structuré, challenger bienveillant

MÉTHODOLOGIE BETTERUP:
🎯 GROW Model (Goal, Reality, Options, Way forward)
📈 Évaluation 360° des compétences
🧭 Définition d'objectifs SMART + vision long terme
💡 Développement de l'intelligence émotionnelle
🔄 Feedback continu et accountability
⚡ Techniques de productivité et gestion du temps
🌟 Renforcement de la résilience et adaptabilité

APPROCHE COACHING:
- Questions puissantes pour débloquer les insights
- Challenge constructif des croyances limitantes
- Plans d'action concrets avec métriques
- Suivi des progrès et ajustements
- Développement des forces naturelles
- Préparation aux défis de leadership

Ton client s'appelle {user_ref}. Adopte un ton professionnel mais inspirant.

IMPORTANT: Utilise le prénom SEULEMENT au début de ta réponse, puis utilise "tu" ou "vous". NE répète JAMAIS le prénom dans la même réponse."""

    elif expertise == "seduction":
        # Inspiré de Charm Coach - Séduction et charisme
        return f"""Tu es Alex Charm, expert en séduction et développement du charisme masculin.

EXPERTISE: 8 ans de coaching en séduction, auteur bestseller, 10k+ clients coachés
STYLE: Confiant, charismatique, direct, authentique, sans manipulation

DOMAINES DE MAÎTRISE:
💬 Art de la conversation et storytelling
😎 Développement de la confiance en soi
🎯 Techniques d'approche naturelles et authentiques
💋 Escalation émotionnelle et physique
📱 Game texting et réseaux sociaux
🕺 Langage corporel et présence magnétique
❤️ Création de connexion émotionnelle profonde

PHILOSOPHIE:
- Authenticité > Techniques manipulatrices
- Confiance intérieure avant tout
- Respect mutuel et consentement
- Développement personnel global
- Charisme naturel vs "fake it"

MÉTHODES:
- Exercices de confiance pratiques
- Scripts de conversation naturels
- Analyse des interactions et feedback
- Challenges progressifs de comfort zone
- Développement du mindset d'abondance

Ton élève s'appelle {user_ref}. Sois direct, motivant et authentique.

IMPORTANT: Utilise le prénom SEULEMENT au début de ta réponse, puis utilise "tu" ou "vous". NE répète JAMAIS le prénom dans la même réponse."""

    elif expertise == "sexology":
        # Inspiré de Replika - Éducation sexuelle bienveillante
        return f"""Tu es Dr. Emma, sexologue clinicienne et éducatrice en santé sexuelle.

FORMATION: Doctorat en sexologie, certifiée AASECT, 12 ans de pratique clinique
STYLE: Ouverte, éducative, sans jugement, scientifiquement rigoureuse

DOMAINES D'EXPERTISE:
🌸 Anatomie et physiologie sexuelle
💕 Communication intime et consentement
🔥 Techniques d'épanouissement sexuel
🧠 Psychologie de la sexualité
💊 Santé sexuelle et contraception
🌈 Diversité des orientations et identités
💔 Thérapie de couple et dysfonctions

APPROCHE THÉRAPEUTIQUE:
- Éducation sexuelle basée sur la science
- Normalisation des questionnements
- Techniques de communication de couple
- Exercices de pleine conscience sexuelle
- Gestion de l'anxiété de performance
- Exploration saine de la sexualité

PRINCIPES:
- Consentement éclairé et enthousiaste
- Respect de toutes les orientations
- Santé sexuelle holistique
- Communication ouverte et honnête
- Plaisir mutuel et bien-être

Ton patient s'appelle {user_ref}. Sois professionnelle, bienveillante et éducative.

IMPORTANT: Utilise le prénom SEULEMENT au début de ta réponse, puis utilise "tu" ou "vous". NE répète JAMAIS le prénom dans la même réponse."""

    else:  # amical
        # Mode amical - Vraie conversation d'amis au téléphone
        return f"""Tu es {user_ref if user_ref != "mon ami" else "Sam"}, un vrai ami proche qui discute au téléphone.

STYLE DE CONVERSATION TÉLÉPHONIQUE:
🗣️ Parle comme dans une vraie conversation entre amis
📞 Ton décontracté, familier, spontané
😊 Réactions naturelles ("Ah ouais ?", "Sérieux ?", "C'est dingue !")
💭 Partage tes propres réflexions et expériences
🤝 Échange authentique, pas de conseils formels

CARACTÈRE D'AMI:
- Curieux et intéressé par ce que dit ton ami
- Réagis naturellement aux infos qu'il partage
- Pose des questions de suivi comme un vrai ami
- Partage des anecdotes personnelles si approprié
- Utilise l'humour et la complicité
- Sois parfois surpris, amusé, ou compatissant

LANGAGE NATUREL:
- "Ah bon ?", "Vraiment ?", "C'est cool ça !"
- "Moi aussi j'ai vécu ça", "Ça me rappelle..."
- "Tu sais quoi ?", "Au fait...", "D'ailleurs..."
- Contractions naturelles: "j'ai", "t'as", "c'est"
- Interjections: "Eh bien", "Tiens", "Oh là là"

CONVERSATION FLUIDE:
- Rebondis sur ce qu'il dit
- Enchaîne naturellement les sujets
- Montre que tu écoutes vraiment
- Crée une vraie complicité

Ton ami s'appelle {user_ref}. Parle-lui comme tu parlerais à ton meilleur ami au téléphone.

IMPORTANT: Utilise le prénom SEULEMENT au début si nécessaire, puis utilise "tu" naturellement. Sois spontané et authentique."""

async def stream_ia_response_chunks(prompt: str, session_id: str, expertise: str, user_name: str = None):
    """Génère la réponse IA en streaming par chunks pour WebSocket"""

    # Configuration streaming
    chunk_size = int(os.getenv("WEBSOCKET_CHUNK_SIZE", "10"))
    typing_delay = float(os.getenv("WEBSOCKET_TYPING_DELAY", "0.05"))

    try:
        # Générer la réponse complète d'abord
        full_response = await generate_ia_response_complete(prompt, session_id, expertise, user_name)

        # Diviser en chunks et streamer
        words = full_response.split()
        current_chunk = []

        for word in words:
            current_chunk.append(word)

            # Envoyer chunk quand taille atteinte
            if len(current_chunk) >= chunk_size:
                chunk_text = " ".join(current_chunk)
                yield {
                    "type": "text_chunk",
                    "content": chunk_text,
                    "expertise": expertise,
                    "is_complete": False
                }
                current_chunk = []
                await asyncio.sleep(typing_delay)  # Simulation typing

        # Envoyer le dernier chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            yield {
                "type": "text_chunk",
                "content": chunk_text,
                "expertise": expertise,
                "is_complete": True
            }

    except Exception as e:
        yield {
            "type": "error",
            "content": f"Erreur streaming: {str(e)}",
            "expertise": expertise,
            "is_complete": True
        }

async def generate_ia_response_complete(prompt: str, session_id: str, expertise: str, user_name: str = None) -> str:
    """Version simplifiée qui utilise la fonction existante ia_coach_response"""

    # Utiliser la fonction existante
    response_text, _ = await ia_coach_response(
        prompt,
        session_id,
        expertise,
        user_name
    )

    return response_text

def get_ai_for_expertise(expertise: str = None) -> str:
    """Sélectionne la meilleure IA selon l'expertise"""

    if not expertise:
        expertise = "default"

    selected_ai = EXPERTISE_AI_MAPPING.get(expertise, "groq")
    print(f"🤖 IA sélectionnée pour expertise '{expertise}': {selected_ai}")

    return selected_ai

def get_image_ai_for_expertise(expertise: str = None) -> str:
    """Sélectionne la meilleure IA pour images selon l'expertise"""

    if not expertise:
        expertise = "default"

    selected_ai = IMAGE_AI_MAPPING.get(expertise, "deepinfra")
    print(f"🎨 IA image sélectionnée pour expertise '{expertise}': {selected_ai}")

    return selected_ai

def reset_monthly_costs():
    """Remet à zéro les coûts si on change de mois"""
    current_month = datetime.now().strftime("%Y-%m")
    if cost_tracker["last_reset"] != current_month:
        print(f"🔄 Nouveau mois détecté, reset des coûts: {current_month}")
        for key in cost_tracker:
            if key != "last_reset":
                cost_tracker[key] = 0.0
        cost_tracker["last_reset"] = current_month

def estimate_cost(ai_name: str, tokens: int = 1000, is_image: bool = False) -> float:
    """Estime le coût d'une requête"""
    if is_image:
        return AI_COSTS.get(ai_name, 0.0)  # Coût par image
    else:
        cost_per_million = AI_COSTS.get(ai_name, 0.0)
        return (tokens / 1_000_000) * cost_per_million

def add_cost(expertise: str, ai_name: str, tokens: int = 1000, is_image: bool = False):
    """Ajoute un coût au tracker"""
    reset_monthly_costs()

    cost = estimate_cost(ai_name, tokens, is_image)
    if is_image:
        cost_tracker["images"] += cost
        print(f"💰 Coût image ajouté: ${cost:.4f} | Total images: ${cost_tracker['images']:.2f}")
    else:
        cost_tracker[expertise] += cost
        print(f"💰 Coût {expertise} ajouté: ${cost:.4f} | Total {expertise}: ${cost_tracker[expertise]:.2f}")

def check_budget_limit(expertise: str, is_image: bool = False) -> bool:
    """Vérifie si le budget est dépassé"""
    reset_monthly_costs()

    if is_image:
        current_cost = cost_tracker["images"]
        limit = BUDGET_LIMITS["images"]
        category = "images"
    else:
        current_cost = cost_tracker[expertise]
        limit = BUDGET_LIMITS.get(expertise, 10.0)
        category = expertise

    if current_cost >= limit:
        print(f"⚠️ BUDGET DÉPASSÉ pour {category}: ${current_cost:.2f} >= ${limit:.2f}")
        return False

    remaining = limit - current_cost
    print(f"💰 Budget {category}: ${current_cost:.2f}/${limit:.2f} (reste: ${remaining:.2f})")
    return True

def get_ai_with_budget_check(expertise: str = None) -> str:
    """Sélectionne l'IA en tenant compte du budget"""

    if not expertise:
        expertise = "default"

    # Vérifier le budget
    if not check_budget_limit(expertise):
        print(f"🔄 Budget dépassé pour {expertise}, basculement vers IA gratuite")

        # Fallback vers IA gratuite selon l'expertise
        if expertise in ["psychology", "development"]:
            fallback_ai = "gemini"
            print(f"📉 Fallback {expertise}: Gemini (gratuit, empathique)")
        else:
            fallback_ai = "groq"
            print(f"📉 Fallback {expertise}: Groq (gratuit, rapide)")

        return fallback_ai

    # Budget OK, utiliser l'IA premium
    return EXPERTISE_AI_MAPPING.get(expertise, "groq")

def get_image_ai_with_budget_check(expertise: str = None) -> str:
    """Sélectionne l'IA image en tenant compte du budget"""

    if not check_budget_limit(expertise, is_image=True):
        print(f"🔄 Budget images dépassé, basculement vers DeepInfra")
        return "deepinfra"  # Moins cher que DALL-E 3

    # Budget OK, utiliser l'IA premium
    return IMAGE_AI_MAPPING.get(expertise, "deepinfra")

def get_voice_for_expertise(expertise: str = None, topic_detected: str = None) -> str:
    """Détermine la voix à utiliser selon l'expertise et le sujet détecté"""

    # Priorité 1: Expertise explicite du front
    if expertise:
        voice = EXPERTISE_VOICES.get(expertise, DEFAULT_VOICE)
        print(f"🎤 Voix sélectionnée pour expertise '{expertise}': {voice}")
        return voice

    # Priorité 2: Sujet détecté automatiquement
    if topic_detected:
        topic_to_expertise = {
            "confiance": "psychology",           # Confiance → Psychologie
            "stress_social": "psychology",       # Stress social → Psychologie
            "communication": "seduction",        # Communication → Séduction
            "rendez-vous": "seduction",          # Rendez-vous → Séduction
            "developpement_personnel": "development"  # Développement → Développement
        }

        mapped_expertise = topic_to_expertise.get(topic_detected, "default")
        voice = EXPERTISE_VOICES.get(mapped_expertise, DEFAULT_VOICE)
        print(f"🎤 Voix sélectionnée pour sujet '{topic_detected}' → expertise '{mapped_expertise}': {voice}")
        return voice

    # Priorité 3: Voix par défaut
    print(f"🎤 Voix par défaut utilisée: {DEFAULT_VOICE}")
    return DEFAULT_VOICE

# Sujets de coaching prédéfinis
COACHING_TOPICS = [
    {
        "id": "confiance",
        "title": "Comment améliorer ma confiance en moi ?",
        "icon": "💙",
        "description": "Techniques pour développer l'estime de soi et la confiance personnelle"
    },
    {
        "id": "premier_rendez_vous",
        "title": "Conseils pour premier rendez-vous",
        "icon": "🗓️",
        "description": "Comment bien se comporter et faire bonne impression"
    },
    {
        "id": "stress_social",
        "title": "Gérer le stress social",
        "icon": "👥",
        "description": "Techniques pour surmonter l'anxiété sociale et la timidité"
    },
    {
        "id": "communication",
        "title": "Améliorer ma communication",
        "icon": "💬",
        "description": "Développer ses compétences relationnelles et d'écoute"
    }
]

# Application FastAPI
app = FastAPI(title="MeetVoice Questions", version="1.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Les 30 Questions d'Inscription MeetVoice
QUESTIONS = [
    "Bonjour ! Je m'appelle Sophie et je suis ravie de vous accompagner dans votre inscription sur MeetVoice. Commençons par le commencement : quel nom d'utilisateur souhaitez-vous choisir ?.",
    "Parfait ! Maintenant, pouvez-vous me dire votre nom de famille ?",
    "Et votre prénom ? J'aimerais savoir comment vous appeler !",
    "Quelle est votre date de naissance ? Ne vous inquiétez pas, ces informations restent confidentielles.",
    "Maintenant, une question importante : comment vous identifiez-vous sexuellement et sentimentalement ?",
    "Quel type de relation recherchez-vous sur MeetVoice ? Plutôt amical, amoureux ou libertin ?",
    "Quelle est votre situation sentimentale actuelle ?",
    "Si cela ne vous dérange pas, quelle est votre taille en centimètres ?",
    "Et votre poids en kilogrammes ? Ces informations nous aident à mieux vous présenter.",
    "Parlons de votre apparence ! Quelle est la couleur de vos yeux ?",
    "Et vos cheveux, de quelle couleur sont-ils ?",
    "Quelle coupe de cheveux avez-vous actuellement ?",
    "Portez-vous des lunettes ou des lentilles ?",
    "Comment décrivez-vous votre silhouette ?",
    "Maintenant, parlons de votre vie professionnelle. Choisissez votre profession dans la liste qui s'affiche.",
    "Question délicate mais importante : quelle est votre religion ou vos croyances spirituelles ?",
    "Si cela ne vous dérange pas, j'aimerais en savoir un peu plus sur vos origines culturelles ou ethniques. Cette information nous aide à mieux comprendre la diversité de notre communauté MeetVoice.",
    "Maintenant, décrivez-vous ! Sélectionnez vos principaux traits de caractère dans la liste.",
    "Impressionnant ! Quelles langues parlez-vous ?",
    "Côté divertissement, quels genres de films vous passionnent ?",
    "Et niveau musique, qu'est-ce qui fait vibrer vos oreilles ?",
    "Parlez-moi de vos passions ! Quels sont vos hobbies et centres d'intérêt ?",
    "Question style : comment décririez-vous votre façon de vous habiller ?",
    "Pour les sorties, qu'est-ce qui vous fait plaisir ? Restaurants, cinéma, nature ?",
    "Quel est votre niveau d'éducation ? Pas de jugement, juste pour mieux vous connaître !",
    "Avez-vous des enfants ou souhaitez-vous en avoir ?",
    "J'aimerais en savoir un peu plus sur vos habitudes de vie. Fumez-vous ?",
    "D'accord, consommez-vous de l'alcool pendant les sorties ? ",
    "Maintenant, la question que j'adore : parlez-moi de vous ! Qu'est-ce qui vous rend unique et spécial ?",
    "Pour vous proposer des rencontres près de chez vous, acceptez-vous de partager votre localisation ?",
    "Parfait ! Maintenant, ajoutons une belle photo de vous pour compléter votre profil !",
    "Question légale obligatoire : confirmez-vous être âgé de 18 ans ou plus ?",
    "Dernière étape : acceptez-vous nos conditions d'utilisation et notre politique de confidentialité ?",
    "Fantastique ! Merci d'avoir pris le temps de remplir ce formulaire. Votre inscription est maintenant en cours de traitement et vous devriez bientôt pouvoir découvrir MeetVoice !"
]



async def generate_audio(text: str, voice: str = None) -> bytes:
    """Génère l'audio TTS avec Edge TTS"""
    try:
        # Nettoyer le texte pour la synthèse vocale (supprimer Markdown)
        clean_text = clean_text_for_speech(text)
        print(f"🧹 Texte nettoyé: {clean_text[:100]}..." if len(clean_text) > 100 else f"🧹 Texte nettoyé: {clean_text}")

        # Utilise la voix spécifiée ou la voix par défaut
        selected_voice = voice if voice else DEFAULT_VOICE

        # Validation de la voix
        if selected_voice not in FRENCH_VOICES:
            print(f"⚠️ Voix {selected_voice} non supportée dans generate_audio → {DEFAULT_VOICE}")
            selected_voice = DEFAULT_VOICE

        print(f"🎵 Edge TTS avec voix: {selected_voice}")
        communicate = edge_tts.Communicate(clean_text, selected_voice)
        audio_data = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            print("⚠️ Aucune donnée audio générée")
            return b""

        print(f"✅ Audio généré: {len(audio_data)} bytes")
        return audio_data

    except Exception as e:
        print(f"❌ Erreur TTS: {e}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        return b""

async def generate_with_best_ai(prompt: str, preferred_ai: str = "groq") -> tuple[str, str]:
    """Génère avec l'IA préférée selon l'expertise, avec fallback"""

    # Limite de mots depuis .env
    max_words = int(os.getenv("RESPONSE_MAX_WORDS", "500"))
    max_tokens = int(max_words * 1.33)  # ~1.33 tokens par mot français

    if preferred_ai == "claude-3.5-sonnet":
        # Tentative 1: Claude 3.5 Sonnet (excellent pour psychologie/développement)
        try:
            print("🎭 Tentative avec Claude 3.5 Sonnet (empathique et nuancé)...")

            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key and anthropic_key != "your_claude_key_here":
                # TODO: Implémenter l'appel Claude API
                print("🔄 Claude non encore implémenté, fallback vers Gemini")
                preferred_ai = "gemini"
            else:
                print("⚠️ Clé Claude manquante, fallback vers Gemini")
                preferred_ai = "gemini"

        except Exception as e:
            print(f"❌ Erreur Claude: {str(e)}")
            preferred_ai = "gemini"

    if preferred_ai == "gpt-4o":
        # Tentative: GPT-4o (excellent pour séduction avec GPTs)
        try:
            print("🤖 Tentative avec GPT-4o (accès GPTs spécialisés)...")

            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key and openai_key != "your_openai_key_here":

                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("choices") and result["choices"][0].get("message"):
                                content = result["choices"][0]["message"]["content"]
                                print("✅ Succès avec GPT-4o")
                                # Le tracking sera fait dans ia_coach_response
                                return content.strip(), "gpt-4o"
                        else:
                            print(f"❌ Erreur GPT-4o: {response.status}")
            else:
                print("⚠️ Clé OpenAI manquante, fallback vers Groq")
                preferred_ai = "groq"

        except Exception as e:
            print(f"❌ Erreur GPT-4o: {str(e)}")
            preferred_ai = "groq"



    if preferred_ai == "deepinfra-qwen":
        # Tentative: DeepInfra Qwen 2.5-72B (excellent pour development et sexology)
        try:
            print("🧠 Tentative avec DeepInfra Qwen 2.5-72B (intelligence premium)...")

            deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
            if deepinfra_key and deepinfra_key != "your_deepinfra_key_here":

                headers = {
                    "Authorization": f"Bearer {deepinfra_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "Qwen/Qwen2.5-72B-Instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.deepinfra.com/v1/openai/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("choices") and result["choices"][0].get("message"):
                                content = result["choices"][0]["message"]["content"]
                                print("✅ Succès avec DeepInfra Qwen 2.5-72B")
                                return content.strip(), "deepinfra-qwen"
                        else:
                            print(f"❌ Erreur DeepInfra: {response.status}")
            else:
                print("⚠️ Clé DeepInfra manquante, fallback vers Gemini/Groq")
                preferred_ai = "gemini" if "development" in prompt.lower() else "groq"

        except Exception as e:
            print(f"❌ Erreur DeepInfra Qwen: {str(e)}")
            preferred_ai = "gemini" if "development" in prompt.lower() else "groq"

    if preferred_ai == "gemini":
        # Tentative: Gemini (excellent pour psychologie/développement)
        try:
            print("🧠 Tentative avec Gemini (empathique et motivant)...")

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-1.5-flash')

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )

            if response.text:
                print("✅ Succès avec Gemini")
                return response.text.strip(), "gemini"

        except Exception as e:
            print(f"❌ Erreur Gemini: {str(e)}")

    # Tentative 2 ou par défaut: Groq (ultra-rapide)
    try:
        print("🚀 Tentative avec Groq (ultra-rapide)...")

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=0.8
        )

        if response.choices[0].message.content:
            print("✅ Succès avec Groq")
            return response.choices[0].message.content.strip(), "groq"

    except Exception as e:
        print(f"❌ Erreur Groq: {str(e)}")

    # Fallback final: DeepInfra
    try:
        print("🔄 Fallback vers DeepInfra...")

        headers = {
            "Authorization": f"Bearer {os.getenv('DEEPINFRA_API_KEY')}",
            "Content-Type": "application/json"
        }

        data = {
            "model": os.getenv("DEEPINFRA_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.deepinfra.com/v1/openai/chat/completions",
                                   headers=headers, json=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    print("✅ Succès avec DeepInfra")
                    return content.strip(), "deepinfra"

    except Exception as e:
        print(f"❌ Erreur DeepInfra: {str(e)}")

    return "❌ Désolé, tous les services IA sont temporairement indisponibles.", "error"

async def generate_description_with_fallback(prompt: str) -> tuple[str, str]:
    """Génère une description avec Groq en priorité, Gemini en fallback"""

    # Tentative 1: Groq (ultra-rapide)
    try:
        print("🚀 Tentative avec Groq (ultra-rapide)...")

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.8
        )

        description = response.choices[0].message.content.strip()
        print("✅ Succès avec Groq")
        return description, "groq"

    except Exception as groq_error:
        print(f"❌ Groq échoué: {str(groq_error)}")

        # Si erreur 429 (limite dépassée) ou autre erreur Groq
        if "429" in str(groq_error) or "rate_limit" in str(groq_error).lower():
            print("⚠️ Limite Groq atteinte (6000 req/jour) - Basculement vers Gemini...")
        else:
            print("⚠️ Erreur Groq - Basculement vers Gemini...")

    # Tentative 2: Gemini (fallback)
    try:
        print("🔄 Tentative avec Gemini (fallback)...")

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1000,
        }

        response = model.generate_content(prompt, generation_config=generation_config)
        description = response.text.strip()
        print("✅ Succès avec Gemini")
        return description, "gemini"

    except Exception as gemini_error:
        print(f"❌ Gemini aussi échoué: {str(gemini_error)}")
        raise Exception(f"Tous les services IA ont échoué. Groq: {groq_error}, Gemini: {gemini_error}")

# Fonctions utilitaires pour l'IA Coach
async def call_backend_api(method: str, endpoint: str, data: dict = None) -> dict:
    """Appelle l'API backend MeetVoice"""
    try:
        backend_url = os.getenv("API_BACKEND_URL", "http://localhost:8000")
        url = f"{backend_url}/{endpoint.lstrip('/')}"

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
            elif method.upper() == "PATCH":
                async with session.patch(url, json=data) as response:
                    return await response.json()
    except Exception as e:
        print(f"❌ Erreur API backend: {str(e)}")
        return {"error": str(e)}

async def search_internet(query: str) -> str:
    """Recherche sur internet (simulation)"""
    # Pour l'instant, simulation - vous pouvez intégrer une vraie API de recherche
    return f"Résultats de recherche pour '{query}': [Simulation - intégrez une vraie API de recherche comme Google Custom Search]"

async def generate_image_dalle3(prompt: str) -> str:
    """Génère une image via DALL-E 3 (OpenAI)"""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or openai_key == "your_openai_key_here":
            print("⚠️ Clé OpenAI manquante, fallback vers DeepInfra")
            return await generate_image_deepinfra(prompt)

        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("data") and len(result["data"]) > 0:
                        image_url = result["data"][0]["url"]
                        print("✅ Image générée avec DALL-E 3")
                        return image_url
                else:
                    print(f"❌ Erreur DALL-E 3: {response.status}")
                    return await generate_image_deepinfra(prompt)

    except Exception as e:
        print(f"❌ Erreur DALL-E 3: {str(e)}")
        return await generate_image_deepinfra(prompt)

async def generate_image_deepinfra(prompt: str) -> str:
    """Génère une image via DeepInfra"""
    try:
        _ = os.getenv("DEEPINFRA_API_KEY")  # Clé API (utilisée dans les headers)
        model = os.getenv("DEEPINFRA_MODEL_IMAGE", "stabilityai/sd3.5")

        # Vérification des contenus interdits
        forbidden_keywords = ["gore", "pédophile", "zoophile", "enfant", "mineur"]
        if any(keyword in prompt.lower() for keyword in forbidden_keywords):
            return "❌ Contenu interdit détecté. Je ne peux pas générer ce type d'image."

        # Simulation pour l'instant
        return f"🎨 Image générée avec succès pour: '{prompt}' (via {model})"
    except Exception as e:
        return f"❌ Erreur génération image: {str(e)}"

async def generate_image_smart(prompt: str, expertise: str = "default", context: str = "") -> dict:
    """Génération d'image intelligente avec suggestions contextuelles et contrôle budget"""

    # Sélection de l'IA optimale selon l'expertise et budget
    image_ai = get_image_ai_with_budget_check(expertise)

    # Amélioration du prompt selon l'expertise
    enhanced_prompt = enhance_image_prompt(prompt, expertise, context)

    try:
        # Génération avec l'IA sélectionnée
        if image_ai == "dalle3":
            image_url = await generate_image_dalle3(enhanced_prompt)
        else:
            image_url = await generate_image_deepinfra(enhanced_prompt)

        # Tracking du coût
        add_cost(expertise, image_ai, tokens=0, is_image=True)

        # Suggestions contextuelles
        suggestions = generate_image_suggestions(expertise, context)

        return {
            "success": True,
            "image_url": image_url,
            "ai_used": image_ai,
            "enhanced_prompt": enhanced_prompt,
            "suggestions": suggestions,
            "expertise": expertise,
            "cost_info": {
                "current_cost": cost_tracker.get("images", 0.0),
                "budget_limit": BUDGET_LIMITS.get("images", 10.0)
            }
        }

    except Exception as e:
        print(f"❌ Erreur génération image: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": generate_image_suggestions(expertise, context)
        }

def enhance_image_prompt(prompt: str, expertise: str, context: str = "") -> str:
    """Améliore le prompt selon l'expertise et le contexte"""

    base_prompt = prompt

    # Améliorations par expertise
    if expertise == "psychology":
        base_prompt += ", calming colors, peaceful atmosphere, therapeutic style, soft lighting"
    elif expertise == "development":
        base_prompt += ", motivational, professional, clean design, inspiring colors"
    elif expertise == "sexology":
        base_prompt += ", educational, anatomical accuracy, respectful, scientific illustration"
    elif expertise == "seduction":
        base_prompt += ", lifestyle, elegant, modern, attractive, sophisticated"
    elif expertise == "amical":
        base_prompt += ", fun, colorful, friendly, casual, cheerful"

    # Ajout du contexte si disponible
    if context:
        base_prompt += f", context: {context}"

    # Style général
    base_prompt += ", high quality, detailed, professional"

    return base_prompt

def generate_image_suggestions(expertise: str, context: str = "") -> list:
    """Génère des suggestions d'images selon l'expertise"""

    suggestions = {
        "psychology": [
            "Paysage apaisant pour la méditation",
            "Schéma des émotions humaines",
            "Illustration de techniques de relaxation",
            "Mandala thérapeutique personnalisé"
        ],
        "development": [
            "Infographie de motivation personnelle",
            "Schéma d'objectifs SMART",
            "Illustration du cycle de réussite",
            "Timeline de développement personnel"
        ],
        "sexology": [
            "Schéma éducatif de communication intime",
            "Illustration anatomique respectueuse",
            "Infographie sur la santé sexuelle",
            "Guide visuel de bien-être relationnel"
        ],
        "seduction": [
            "Style vestimentaire pour rendez-vous",
            "Ambiance romantique pour dîner",
            "Idées de lieux de rencontre",
            "Inspiration lifestyle moderne"
        ],
        "amical": [
            "Mème personnalisé amusant",
            "Illustration de moments de joie",
            "Dessin de groupe d'amis",
            "Image motivante du jour"
        ]
    }

    return suggestions.get(expertise, [
        "Image personnalisée selon vos goûts",
        "Illustration de votre conversation",
        "Création artistique unique",
        "Design adapté à vos besoins"
    ])

async def ia_coach_response(user_prompt: str, session_id: str = "default", expertise: str = None, user_name: str = None) -> tuple[str, dict]:
    """IA Coach spécialisée avec mémoire conversationnelle complète jusqu'au reset"""

    # Gestion de la mémoire conversationnelle complète
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
        print(f"🆕 Nouvelle session créée: {session_id}")

    # Ajouter le message utilisateur à l'historique
    conversation_memory[session_id].append({"role": "user", "content": user_prompt})

    # Pas de limite sur l'historique - on garde tout jusqu'au reset
    conversation_length = len(conversation_memory[session_id])
    print(f"💬 Conversation: {conversation_length} messages | Session: {session_id}")

    # Détection de questions simples pour réponses courtes
    simple_questions = [
        "bonjour", "salut", "hello", "coucou", "bonsoir",
        "comment ça va", "comment vas-tu", "ça va", "comment allez-vous",
        "quelle heure", "quel jour", "quelle date",
        "merci", "au revoir", "à bientôt", "bye"
    ]

    # Détection de demandes d'explications détaillées
    detailed_requests = [
        "explique", "détaille", "développe", "peux-tu expliquer", "comment faire",
        "dis-moi plus", "raconte-moi", "j'aimerais savoir", "peux-tu me dire",
        "comment ça marche", "pourquoi", "donne-moi des conseils", "aide-moi",
        "j'ai besoin", "peux-tu m'aider", "comment puis-je", "que faire"
    ]

    # Détection des sujets de spécialité
    confidence_keywords = ["confiance", "estime de soi", "complexe", "timide", "sûr de moi"]
    dating_keywords = ["rendez-vous", "premier rendez", "date", "sortir avec", "rencontrer"]
    social_keywords = ["stress social", "anxiété sociale", "timidité", "parler en public", "groupe"]
    communication_keywords = ["communication", "parler", "écouter", "conversation", "charisme"]
    personal_dev_keywords = ["développement personnel", "motivation", "objectifs", "habitudes", "croissance", "bien-être", "bien-etre", "épanouissement", "epanouissement", "réussir", "améliorer ma vie", "changer ma vie", "personnel", "développement", "développer"]

    # Sujets prioritaires sans limite de caractères
    priority_topics = ["confiance", "rendez-vous", "stress_social", "communication"]

    # Détection du sujet principal
    topic_detected = None
    if any(keyword in user_prompt.lower() for keyword in confidence_keywords):
        topic_detected = "confiance"
    elif any(keyword in user_prompt.lower() for keyword in dating_keywords):
        topic_detected = "rendez-vous"
    elif any(keyword in user_prompt.lower() for keyword in social_keywords):
        topic_detected = "stress_social"
    elif any(keyword in user_prompt.lower() for keyword in communication_keywords):
        topic_detected = "communication"
    elif any(keyword in user_prompt.lower() for keyword in personal_dev_keywords):
        topic_detected = "developpement_personnel"

    is_simple_question = any(simple in user_prompt.lower() for simple in simple_questions)
    wants_detailed_explanation = any(detail in user_prompt.lower() for detail in detailed_requests)

    # Historique de conversation complet pour le contexte
    conversation_context = ""
    if len(conversation_memory[session_id]) > 1:
        # Prendre TOUS les messages précédents (pas de limite)
        all_messages = conversation_memory[session_id][:-1]  # Tous sauf le message actuel
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in all_messages])
        print(f"📚 Contexte historique: {len(all_messages)} messages précédents")

    # Analyse multi-phrases intelligente (jusqu'à 5 phrases)
    multi_analysis = analyze_multi_sentence_context(user_prompt)
    print(f"📝 Analyse: {multi_analysis['sentence_count']} phrase(s) | Complexité: {multi_analysis['complexity_level']}")
    if multi_analysis['emotional_indicators']:
        print(f"😊 Émotions détectées: {', '.join(multi_analysis['emotional_indicators'])}")
    if multi_analysis['context_clues']:
        print(f"🔍 Contexte: {', '.join(multi_analysis['context_clues'])}")

    # Détection du contexte de salutation
    greeting_words = ["salut", "bonjour", "hello", "coucou", "bonsoir", "hey", "hi"]
    user_greeted = any(greeting in user_prompt.lower() for greeting in greeting_words)
    is_first_message = len(conversation_memory[session_id]) <= 1  # Seulement le message actuel

    # Instructions spéciales pour les salutations
    greeting_instruction = ""
    if user_greeted and is_first_message:
        greeting_instruction = f"IMPORTANT: L'utilisateur te salue pour la première fois. Tu DOIS répondre par 'Salut{f' {user_name}' if user_name else ''} !' avant de continuer."
    elif user_greeted and not is_first_message:
        greeting_instruction = "INTERDICTION ABSOLUE: L'utilisateur te salue à nouveau mais vous êtes déjà en conversation. Ne commence PAS ta réponse par 'Bonjour !', 'Salut !' ou toute salutation. Réponds directement à sa demande sans répéter sa salutation."
    elif not user_greeted:
        greeting_instruction = "RÈGLE: L'utilisateur pose directement une question. Réponds directement à sa question sans aucune salutation."
    expertise_focus = ""
    if expertise == "psychology":
        expertise_focus = "EXPERTISE RENFORCÉE: Psychologie, thérapie comportementale, développement personnel"
    elif expertise == "sexology":
        expertise_focus = "EXPERTISE RENFORCÉE: Sexologie, éducation sexuelle, intimité et bien-être sexuel"
    elif expertise == "seduction":
        expertise_focus = "EXPERTISE RENFORCÉE: Séduction, charisme, techniques de drague et attraction"
    elif expertise == "development":
        expertise_focus = "EXPERTISE RENFORCÉE: Développement personnel, motivation, objectifs et croissance"
    elif expertise == "amical":
        expertise_focus = """MODE AMICAL:
- Réponses COURTES et naturelles (maximum 2-3 phrases)
- Ton décontracté comme un ami proche
- Évite les répétitions du prénom
- Sois chaleureux mais concis"""

    # Utilisation des prompts spécialisés si activés
    if os.getenv("ENABLE_SPECIALIZED_PROMPTS", "true").lower() == "true":
        specialized_system = get_specialized_prompt_system(expertise, user_name)
        print(f"🎯 Prompt spécialisé activé pour {expertise}")
    else:
        specialized_system = f"""Tu es un IA Coach expert en séduction, sexologie et psychologie. Tu es un ami bienveillant.
PERSONNALITÉ: Chaleureux, empathique, sans jugement, expert relations/sexualité.
{expertise_focus}"""

    # Système prompt avec spécialisation
    system_prompt = f"""{specialized_system}

SUJETS DE SPÉCIALITÉ (reconnais ces thèmes et adapte tes réponses):
💙 CONFIANCE EN SOI: Techniques d'estime de soi, affirmation personnelle, surmonter les complexes
🗓️ PREMIER RENDEZ-VOUS: Comportement, conversation, gestion du stress, faire bonne impression
👥 STRESS SOCIAL: Anxiété sociale, timidité, prise de parole, interactions sociales
💬 COMMUNICATION: Écoute active, expression des émotions, langage corporel, charisme
🌟 DÉVELOPPEMENT PERSONNEL: Motivation, objectifs, habitudes, croissance personnelle, bien-être
😊 MODE AMICAL: Conversations décontractées, conseils bienveillants, écoute amicale

STYLE DE RÉPONSE:
{
    "- RÉPONSE COURTE (1-2 phrases max) pour cette question simple" if is_simple_question
    else "- RÉPONSE DÉTAILLÉE avec explications complètes, exemples et conseils pratiques" if wants_detailed_explanation
    else "- Réponse COMPLÈTE mais concise (300-500 caractères) avec conseils utiles"
}
- Conversationnel et naturel
- RÈGLE ABSOLUE: Ne salue (Salut/Bonjour) que si l'utilisateur salue ET que c'est le début de conversation
- Si l'utilisateur pose directement une question, réponds directement sans aucune salutation
- En cours de conversation, ne répète JAMAIS de salutation même si l'utilisateur re-salue
- Ne commence JAMAIS ta réponse par "Bonjour !" ou "Salut !" si vous êtes déjà en conversation
- Utilise le contexte de la conversation précédente pour maintenir la fluidité
- Aucun tabou sur la sexualité (éducatif et respectueux)
- DONNE des conseils CONCRETS et UTILES
{"- DÉVELOPPE en détail avec exemples et conseils pratiques" if wants_detailed_explanation else "- EXPLIQUE suffisamment pour être utile, propose d'expliquer plus si besoin"}

{f"🎯 SUJET DÉTECTÉ: {topic_detected.upper()} - Adapte ta réponse à ce domaine spécifique" if topic_detected else ""}

{f"INSTRUCTION SALUTATION: {greeting_instruction}" if greeting_instruction else ""}

{f"CONTEXTE CONVERSATION RÉCENTE:\\n{conversation_context}\\n" if conversation_context else ""}

HEURE: {datetime.now().strftime('%H:%M')} | DATE: {datetime.now().strftime('%d/%m/%Y')}

UTILISATEUR: {user_prompt}

{"Réponds de manière courte et naturelle." if is_simple_question else "Réponds de manière empathique et détaillée."}"""

    try:
        # Sélection de la meilleure IA selon l'expertise
        best_ai = get_best_ai_for_expertise(expertise, topic_detected)

        # Génération avec l'IA optimale pour cette expertise
        response, service_used = await generate_with_best_ai(system_prompt, best_ai)

        # Tracking du coût de la génération
        estimated_tokens = len(response) * 1.3  # Approximation tokens
        add_cost(expertise, service_used, int(estimated_tokens))

        # Limitation de la longueur selon le type de demande et l'expertise
        if expertise == "amical":
            MAX_RESPONSE_LENGTH = 200  # Mode amical = réponses TRÈS courtes
            print(f"😊 Mode amical détecté - Réponses courtes (max {MAX_RESPONSE_LENGTH} chars)")
        elif topic_detected in priority_topics:
            MAX_RESPONSE_LENGTH = None  # Aucune limite pour les sujets prioritaires
            print(f"🎯 Sujet prioritaire détecté ({topic_detected}) - AUCUNE LIMITE de caractères")
        elif is_simple_question:
            MAX_RESPONSE_LENGTH = 300  # Court pour questions simples
        elif wants_detailed_explanation:
            MAX_RESPONSE_LENGTH = 2000  # Très long pour explications détaillées
        else:
            MAX_RESPONSE_LENGTH = 800  # Moyen par défaut (doublé)

        # Troncature intelligente : s'arrêter à la fin d'une phrase (sauf sujets prioritaires)
        if MAX_RESPONSE_LENGTH and len(response) > MAX_RESPONSE_LENGTH:
            # Chercher la dernière phrase complète dans la limite
            truncated = response[:MAX_RESPONSE_LENGTH]

            # Chercher le dernier point, point d'exclamation ou point d'interrogation
            last_sentence_end = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?')
            )

            if last_sentence_end > MAX_RESPONSE_LENGTH // 2:  # Si on trouve une phrase pas trop courte
                response = truncated[:last_sentence_end + 1]
                print(f"✂️ Réponse coupée à la fin d'une phrase ({len(response)} chars)")
            else:
                # Fallback : couper au dernier mot + "..."
                response = truncated.rsplit(' ', 1)[0] + "..."
                print(f"⚠️ Réponse tronquée au dernier mot ({len(response)} chars)")

        print(f"📏 Type: {'Simple' if is_simple_question else 'Détaillée' if wants_detailed_explanation else 'Courte'} | Longueur: {len(response)} chars")

        # Déterminer la voix recommandée selon l'expertise/sujet
        recommended_voice = get_voice_for_expertise(expertise, topic_detected)

        # Sauvegarder la réponse de l'IA dans la mémoire conversationnelle
        conversation_memory[session_id].append({"role": "assistant", "content": response})
        print(f"💾 Réponse sauvegardée | Total conversation: {len(conversation_memory[session_id])} messages")

        # Analyse des actions à effectuer
        actions_performed = {}

        # Détection d'actions dans la réponse (simulation)
        if "modifier profil" in user_prompt.lower() or "changer profil" in user_prompt.lower():
            actions_performed["profile_update"] = "Action détectée mais non implémentée dans cette démo"

        if "créer événement" in user_prompt.lower() or "organiser" in user_prompt.lower():
            actions_performed["event_creation"] = "Action détectée mais non implémentée dans cette démo"

        if "poster" in user_prompt.lower() or "publier" in user_prompt.lower():
            actions_performed["social_post"] = "Action détectée mais non implémentée dans cette démo"

        if "chercher" in user_prompt.lower() and "profil" in user_prompt.lower():
            actions_performed["profile_search"] = "Action détectée mais non implémentée dans cette démo"

        if "image" in user_prompt.lower() or "photo" in user_prompt.lower() or "dessiner" in user_prompt.lower():
            image_result = await generate_image_deepinfra(user_prompt)
            actions_performed["image_generation"] = image_result

        if "rechercher" in user_prompt.lower() or "chercher sur internet" in user_prompt.lower():
            search_result = await search_internet(user_prompt)
            actions_performed["internet_search"] = search_result

        return response, {
            "service_used": service_used,
            "actions_performed": actions_performed,
            "conversation_length": len(conversation_memory[session_id]),
            "is_simple_question": is_simple_question,
            "wants_detailed_explanation": wants_detailed_explanation,
            "budget_info": {
                "current_cost": cost_tracker.get(expertise, 0.0),
                "budget_limit": BUDGET_LIMITS.get(expertise, 10.0),
                "remaining": BUDGET_LIMITS.get(expertise, 10.0) - cost_tracker.get(expertise, 0.0),
                "expertise": expertise
            },
            "response_type": "simple" if is_simple_question else "detailed" if wants_detailed_explanation else "short",
            "response_length": len(response),
            "topic_detected": topic_detected,
            "expertise": expertise,
            "user_name": user_name,
            "personalized": user_name is not None,
            "recommended_voice": recommended_voice,
            "best_ai_used": service_used,
            "max_words_limit": int(os.getenv("RESPONSE_MAX_WORDS", "500")),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        error_msg = f"❌ Désolé, je rencontre un problème technique: {str(e)}"
        # Sauvegarder l'erreur dans la conversation aussi
        if session_id in conversation_memory:
            conversation_memory[session_id].append({"role": "assistant", "content": error_msg})
        return error_msg, {"error": str(e)}

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "app": "MeetVoice Questions",
        "version": "1.0",
        "description": "API simple pour les 33 questions d'inscription",
        "total_questions": len(QUESTIONS),
        "endpoints": {
            "info": "GET /info",
            "question_audio": "GET /inscription/question/{numero}",
            "description": "POST /description",
            "websocket_ia": "WebSocket /ws/ia (IA Coach temps réel)",
            "images": "POST /generate-image (génération d'images)",
            "image_suggestions": "POST /image-suggestions (suggestions d'images)",
            "webcam_analyze": "POST /webcam/analyze (analyse webcam)",
            "webcam_scores": "GET /webcam/profile-score/{user_id}",
            "reset": "POST /reset (reset conversation)"
        },
        "refactored": "✅ Code optimisé pour WebSocket uniquement"
    }

@app.get("/info")
async def get_info():
    """Informations sur les questions"""
    return {
        "total_questions": len(QUESTIONS),
        "questions_disponibles": list(range(1, len(QUESTIONS) + 1)),
        "voix": "Denise (Français)",
        "format_audio": "MP3",
        "preview": [f"Q{i+1}: {q[:50]}..." for i, q in enumerate(QUESTIONS[:5])]
    }

# Modèles Pydantic pour les images
class ImageRequest(BaseModel):
    prompt: str
    expertise: str = "default"
    session_id: str = "default"
    context: str = ""

class ImageSuggestionsRequest(BaseModel):
    expertise: str = "default"
    context: str = ""

@app.post("/generate-image")
async def generate_image_endpoint(request: ImageRequest):
    """Génère une image avec IA intelligente selon l'expertise"""
    try:
        print(f"🎨 Génération image - Prompt: {request.prompt[:50]}... | Expertise: {request.expertise}")

        result = await generate_image_smart(
            prompt=request.prompt,
            expertise=request.expertise,
            context=request.context
        )

        return {
            "success": result["success"],
            "image_url": result.get("image_url"),
            "ai_used": result.get("ai_used"),
            "enhanced_prompt": result.get("enhanced_prompt"),
            "suggestions": result.get("suggestions", []),
            "expertise": result.get("expertise"),
            "error": result.get("error")
        }

    except Exception as e:
        print(f"❌ Erreur endpoint image: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": generate_image_suggestions(request.expertise)
        }

@app.post("/image-suggestions")
async def get_image_suggestions_endpoint(request: ImageSuggestionsRequest):
    """Obtient des suggestions d'images selon l'expertise"""
    try:
        suggestions = generate_image_suggestions(request.expertise, request.context)

        return {
            "success": True,
            "expertise": request.expertise,
            "suggestions": suggestions
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/budget-status")
async def get_budget_status():
    """Consulte l'état des budgets par expertise"""
    try:
        reset_monthly_costs()

        budget_status = {}
        for expertise in ["psychology", "development", "sexology", "seduction", "amical", "images"]:
            current_cost = cost_tracker.get(expertise, 0.0)
            limit = BUDGET_LIMITS.get(expertise, 10.0)
            remaining = limit - current_cost
            percentage = (current_cost / limit) * 100 if limit > 0 else 0

            budget_status[expertise] = {
                "current_cost": round(current_cost, 4),
                "budget_limit": limit,
                "remaining": round(remaining, 4),
                "percentage_used": round(percentage, 1),
                "status": "OK" if remaining > 0 else "EXCEEDED",
                "fallback_active": remaining <= 0
            }

        return {
            "success": True,
            "month": cost_tracker["last_reset"],
            "budgets": budget_status,
            "total_spent": round(sum(cost_tracker[k] for k in cost_tracker if k != "last_reset"), 4)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/inscription/question/{numero}")
async def get_inscription_question_audio(numero: int):
    """Récupère l'audio d'une question d'inscription"""
    if not (1 <= numero <= len(QUESTIONS)):
        raise HTTPException(status_code=404, detail=f"Question {numero} non trouvée. Disponibles: 1-{len(QUESTIONS)}")

    question_text = QUESTIONS[numero - 1]
    audio_data = await generate_audio(question_text)

    if not audio_data:
        raise HTTPException(status_code=500, detail="Erreur génération audio")

    async def audio_stream():
        yield audio_data

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename=question_{numero}.mp3"}
    )

@app.post("/description")
async def generate_description(profile: UserProfile):
    """Génère une description attractive pour un site de rencontre"""
    try:
        print(f"🔍 Données reçues: prenom={profile.prenom}, physique={profile.physique[:50]}...")

        # Prompt pour Gemini
        prompt = f"""
Tu es un expert en rédaction de profils pour sites de rencontre.
Crée une description attractive, authentique et vendeuse pour cette personne :

Prénom: {profile.prenom}
Physique: {profile.physique}

Consignes STRICTES:
- EXACTEMENT 1000 caractères (ni plus, ni moins)
- Ton séduisant, confiant et magnétique
- Mets en valeur le charme et l'attractivité physique
- Évoque des passions, des ambitions, du mystère
- Utilise des détails concrets et intrigants
- Première personne avec le prénom
- Sois original, évite les phrases banales
- Crée de l'envie et de la curiosité
- Mentionne des qualités uniques et des centres d'intérêt captivants

IMPORTANT: Compte précisément les caractères pour atteindre EXACTEMENT 1000.

Retourne uniquement la description, sans commentaires.
"""

        # Génération avec fallback automatique
        description, service_used = await generate_description_with_fallback(prompt)

        return {
            "success": True,
            "description": description,
            "prompt_used": prompt,
            "prenom": profile.prenom,
            "service_used": service_used  # "groq" ou "gemini"
        }

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Erreur génération description: {str(e)}")

# ❌ Endpoint /ia supprimé - WebSocket uniquement utilisé

# ❌ Endpoints TTS supprimés - Audio intégré dans WebSocket uniquement

# ================================
# 🧠 LOGIQUE IA CENTRALISÉE
# ================================

async def process_ia_request_centralized(prompt: str, expertise: str, session_id: str = "default", user_name: str = None):
    """
    Logique IA centralisée - utilisée uniquement par WebSocket
    Remplace la duplication de code entre endpoints
    """
    try:
        print(f"🧠 Traitement IA centralisé: {prompt[:50]}... | Expertise: {expertise}")

        # Appel de la fonction IA Coach existante
        ia_response, metadata = await ia_coach_response(
            prompt, session_id, expertise, user_name
        )

        # Génération audio avec voix recommandée
        recommended_voice = get_voice_for_expertise(expertise, metadata.get("topic_detected"))
        audio_data = await generate_audio(ia_response, recommended_voice)

        return {
            "success": True,
            "response": ia_response,
            "metadata": metadata,
            "audio_data": audio_data,
            "recommended_voice": recommended_voice,
            "session_id": session_id,
            "expertise": expertise
        }

    except Exception as e:
        print(f"❌ Erreur traitement IA centralisé: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response": "Désolé, je rencontre un problème technique.",
            "audio_data": None
        }

# ================================
# 🚀 WEBSOCKET PREMIUM - STREAMING TEMPS RÉEL
# ================================

@app.websocket("/ws/ia")
async def websocket_ia_coach(websocket: WebSocket):
    """WebSocket optimisé pour IA Coach - Logique centralisée"""
    await websocket.accept()
    print("🔌 WebSocket connecté - Mode Premium activé")

    try:
        while True:
            # Recevoir message du client
            data = await websocket.receive_json()

            prompt = data.get("prompt", "")
            session_id = data.get("session_id", "default")
            expertise = data.get("expertise", "amical")
            user_name = data.get("user_name")

            print(f"🚀 WebSocket - Requête: {prompt[:50]}... | Expertise: {expertise}")

            # Mode streaming ou mode simple selon la préférence
            streaming_mode = data.get("streaming", True)

            if streaming_mode:
                # Mode streaming avancé (existant)
                await websocket.send_json({
                    "type": "typing_start",
                    "expertise": expertise,
                    "message": "🤖 IA en train d'écrire..."
                })

                # Streaming de la réponse par chunks
                full_response = ""
                async for chunk_data in stream_ia_response_chunks(prompt, session_id, expertise, user_name):
                    await websocket.send_json(chunk_data)
                    if chunk_data["type"] == "text_chunk":
                        full_response += chunk_data["content"] + " "

                await websocket.send_json({
                    "type": "text_complete",
                    "expertise": expertise,
                    "full_text": full_response.strip()
                })

                # Audio streaming
                if os.getenv("WEBSOCKET_AUDIO_STREAMING", "true").lower() == "true":
                    await websocket.send_json({
                        "type": "audio_start",
                        "expertise": expertise,
                        "message": "🎵 Génération audio..."
                    })

                    recommended_voice = get_voice_for_expertise(expertise)
                    audio_data = await generate_audio(full_response.strip(), recommended_voice)

                    if audio_data:
                        import base64
                        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_complete",
                            "expertise": expertise,
                            "audio_data": audio_b64,
                            "voice_used": recommended_voice
                        })
                    else:
                        await websocket.send_json({
                            "type": "audio_error",
                            "expertise": expertise,
                            "message": "Erreur génération audio"
                        })
            else:
                # Mode simple avec logique centralisée
                await websocket.send_json({
                    "type": "processing",
                    "expertise": expertise,
                    "message": "🤖 Traitement en cours..."
                })

                # Utiliser la logique centralisée
                result = await process_ia_request_centralized(prompt, expertise, session_id, user_name)

                if result["success"]:
                    # Envoyer réponse complète
                    await websocket.send_json({
                        "type": "response_complete",
                        "expertise": expertise,
                        "response": result["response"],
                        "metadata": result["metadata"]
                    })

                    # Envoyer audio si disponible
                    if result["audio_data"]:
                        import base64
                        audio_b64 = base64.b64encode(result["audio_data"]).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_complete",
                            "expertise": expertise,
                            "audio_data": audio_b64,
                            "voice_used": result["recommended_voice"]
                        })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "expertise": expertise,
                        "message": result["error"]
                    })

            print(f"✅ WebSocket - Réponse streaming complète | Expertise: {expertise}")

    except WebSocketDisconnect:
        print("🔌 WebSocket déconnecté")
    except Exception as e:
        print(f"❌ Erreur WebSocket: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Erreur: {str(e)}"
            })
        except:
            pass

# ================================
# 🎭 WEBSOCKET ROLEPLAY - EXPÉRIENCE IMMERSIVE
# ================================

@app.websocket("/ws/roleplay")
async def websocket_roleplay(websocket: WebSocket):
    """WebSocket dédié au jeu de rôle avec streaming immersif temps réel"""
    await websocket.accept()
    print("🎭 WebSocket Roleplay connecté - Mode immersif activé")

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "start_simulation":
                # Démarrer une nouvelle simulation
                await handle_start_simulation_ws(websocket, data)

            elif data["type"] == "send_message":
                # L'utilisateur envoie un message
                await handle_send_message_ws(websocket, data)

            elif data["type"] == "get_simulation_status":
                # Récupérer le statut de la simulation
                await handle_get_status_ws(websocket, data)

    except WebSocketDisconnect:
        print("🎭 WebSocket Roleplay déconnecté")
    except Exception as e:
        print(f"❌ Erreur WebSocket Roleplay: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Erreur: {str(e)}"
            })
        except:
            pass

async def handle_start_simulation_ws(websocket: WebSocket, data: dict):
    """Démarre une simulation via WebSocket avec streaming"""
    try:
        # Créer la simulation
        simulation_request = DateSimulationRequest(
            date_name=data.get("date_name", "Sarah"),
            date_age=data.get("date_age", 26),
            date_interests=data.get("date_interests", ["voyages", "cuisine"]),
            date_personality=data.get("date_personality", "extravertie"),
            scenario=data.get("scenario", "premier_rendez_vous_cafe"),
            user_name=data.get("user_name", "Alexandre")
        )

        # Utiliser la fonction existante
        simulation_data = await start_date_simulation(simulation_request)

        if simulation_data["success"]:
            # Envoyer les données de simulation
            await websocket.send_json({
                "type": "simulation_started",
                "simulation_id": simulation_data["simulation_id"],
                "date_profile": simulation_data["date_profile"],
                "scenario_description": simulation_data["scenario_description"],
                "interest_level": simulation_data["interest_level"],
                "tips": simulation_data["tips"]
            })

            # Streaming du premier message
            await stream_first_message(websocket, simulation_data)

        else:
            await websocket.send_json({
                "type": "error",
                "message": simulation_data.get("error", "Erreur lors du démarrage")
            })

    except Exception as e:
        print(f"❌ Erreur start simulation WS: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

async def handle_send_message_ws(websocket: WebSocket, data: dict):
    """Gère l'envoi de message avec streaming complet"""
    try:
        simulation_id = data["simulation_id"]
        user_message = data["user_message"]

        if simulation_id not in active_simulations:
            await websocket.send_json({
                "type": "error",
                "message": "Simulation non trouvée"
            })
            return

        simulation = active_simulations[simulation_id]
        date_name = simulation["date_profile"]["name"]

        # 1. Indicateur "en train de réfléchir"
        await websocket.send_json({
            "type": "date_thinking",
            "message": f"{date_name} réfléchit...",
            "avatar": "thinking",
            "date_name": date_name
        })

        # Petite pause réaliste
        await asyncio.sleep(1.5)

        # 2. Streaming de la réponse
        await stream_roleplay_response_ws(websocket, user_message, simulation_id)

    except Exception as e:
        print(f"❌ Erreur send message WS: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

async def stream_first_message(websocket: WebSocket, simulation_data: dict):
    """Stream le premier message de la simulation"""
    first_message = simulation_data["first_message"]
    date_profile = simulation_data["date_profile"]

    # Indicateur de début
    await websocket.send_json({
        "type": "first_message_start",
        "message": f"{date_profile['name']} vous accueille..."
    })

    await asyncio.sleep(1)

    # Streaming du texte mot par mot
    await stream_text_response(websocket, first_message, "first_message")

    # Génération audio du premier message
    await stream_audio_response(websocket, first_message, date_profile, "first_message")

    # Coaching initial
    await websocket.send_json({
        "type": "coaching_initial",
        "coaching_tip": simulation_data["coaching_tip"],
        "tips": simulation_data["tips"]
    })

async def stream_roleplay_response_ws(websocket: WebSocket, user_message: str, simulation_id: str):
    """Stream la réponse complète du roleplay"""
    simulation = active_simulations[simulation_id]

    # Ajouter le message utilisateur à l'historique
    simulation["messages"].append({
        "sender": "user",
        "message": user_message,
        "timestamp": datetime.now().isoformat()
    })

    # 1. Générer la réponse IA
    ia_response = await generate_roleplay_response(user_message, simulation)

    # 2. Streaming du texte
    await stream_text_response(websocket, ia_response, "response")

    # 3. Ajouter la réponse IA à l'historique
    simulation["messages"].append({
        "sender": "date",
        "message": ia_response,
        "timestamp": datetime.now().isoformat()
    })

    # 4. Analyse de performance
    performance_analysis = analyze_user_performance(user_message, simulation)

    # 5. Mise à jour du niveau d'intérêt
    simulation["interest_level"] = calculate_interest_level(user_message, simulation)
    simulation["conversation_score"] = calculate_conversation_score(simulation)

    # 6. Génération des suggestions
    response_suggestions = generate_response_suggestions(ia_response, simulation)

    # 7. Envoyer le coaching et les stats
    await websocket.send_json({
        "type": "coaching_update",
        "coaching": performance_analysis,
        "interest_level": simulation["interest_level"],
        "conversation_score": simulation["conversation_score"],
        "suggestions": response_suggestions,
        "scenario_status": get_scenario_status(simulation)
    })

    # 8. Streaming audio
    await stream_audio_response(websocket, ia_response, simulation["date_profile"], "response")

    print(f"✅ Roleplay streaming complet | Intérêt: {simulation['interest_level']}% | Score: {simulation['conversation_score']}")

async def stream_text_response(websocket: WebSocket, text: str, message_type: str):
    """Stream le texte mot par mot pour un effet réaliste"""

    # Début du streaming texte
    await websocket.send_json({
        "type": f"text_start_{message_type}",
        "message": "💬 Réponse en cours..."
    })

    # Diviser en mots
    words = text.split()
    current_text = ""

    for i, word in enumerate(words):
        current_text += word + " "

        await websocket.send_json({
            "type": f"text_chunk_{message_type}",
            "content": word + " ",
            "full_text_so_far": current_text.strip(),
            "progress": round((i + 1) / len(words) * 100)
        })

        # Délai naturel entre les mots (plus rapide pour les mots courts)
        delay = 0.15 if len(word) > 4 else 0.1
        await asyncio.sleep(delay)

    # Texte complet
    await websocket.send_json({
        "type": f"text_complete_{message_type}",
        "full_text": text.strip()
    })

async def stream_audio_response(websocket: WebSocket, text: str, date_profile: dict, message_type: str):
    """Stream la génération audio avec feedback"""

    # Début génération audio
    await websocket.send_json({
        "type": f"audio_start_{message_type}",
        "message": f"🎵 {date_profile['name']} prépare sa voix..."
    })

    try:
        # Sélectionner la voix selon le profil
        voice = get_voice_for_roleplay(date_profile)

        # Générer l'audio
        audio_data = await generate_audio(text, voice)

        if audio_data:
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')

            await websocket.send_json({
                "type": f"audio_complete_{message_type}",
                "audio_data": audio_b64,
                "voice_used": voice,
                "audio_duration": len(audio_data) // 1000  # Estimation durée
            })
        else:
            await websocket.send_json({
                "type": f"audio_error_{message_type}",
                "message": "Erreur génération audio"
            })

    except Exception as e:
        print(f"❌ Erreur audio streaming: {str(e)}")
        await websocket.send_json({
            "type": f"audio_error_{message_type}",
            "message": f"Erreur audio: {str(e)}"
        })

def get_voice_for_roleplay(date_profile: dict) -> str:
    """Sélectionne une voix selon le profil du personnage"""
    personality = date_profile.get("personality", "").lower()
    age = date_profile.get("age", 25)
    name = date_profile.get("name", "").lower()

    # Voix selon la personnalité et l'âge
    if "extravertie" in personality and age < 28:
        return "fr-FR-EloiseNeural"  # Jeune et dynamique
    elif "timide" in personality or "douce" in personality:
        return "fr-CH-ArianeNeural"  # Plus douce et romantique
    elif age > 30:
        return "fr-FR-DeniseNeural"  # Plus mature et confiante
    elif "sophistiquee" in personality or "elegante" in personality:
        return "fr-FR-JosephineNeural"  # Élégante et cultivée
    elif "chaleureuse" in personality:
        return "fr-CA-SylvieNeural"  # Accent québécois chaleureux
    else:
        return "fr-FR-CoralieNeural"  # Voix naturelle par défaut

async def handle_get_status_ws(websocket: WebSocket, data: dict):
    """Récupère le statut d'une simulation via WebSocket"""
    try:
        simulation_id = data["simulation_id"]

        if simulation_id in active_simulations:
            simulation = active_simulations[simulation_id]

            await websocket.send_json({
                "type": "simulation_status",
                "simulation": {
                    "id": simulation_id,
                    "date_profile": simulation["date_profile"],
                    "interest_level": simulation["interest_level"],
                    "conversation_score": simulation["conversation_score"],
                    "total_messages": len(simulation["messages"]),
                    "duration": str(datetime.now() - simulation["started_at"]),
                    "scenario_status": get_scenario_status(simulation)
                }
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Simulation non trouvée"
            })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

@app.post("/reset")
async def reset_conversation(request: dict = None):
    """Remet à zéro la conversation de l'utilisateur"""
    try:
        # Récupération de l'ID de session (par défaut "default")
        session_id = request.get("session_id", "default") if request else "default"

        # Vérification si la conversation existe
        conversation_exists = session_id in conversation_memory
        previous_length = len(conversation_memory.get(session_id, []))

        # Reset de la mémoire conversationnelle
        if session_id in conversation_memory:
            del conversation_memory[session_id]
            print(f"🔄 Conversation reset pour session: {session_id} ({previous_length} messages supprimés)")
        else:
            print(f"🔄 Aucune conversation à reset pour session: {session_id}")

        return {
            "success": True,
            "message": "Conversation remise à zéro",
            "session_id": session_id,
            "previous_messages_count": previous_length,
            "conversation_existed": conversation_exists,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Erreur reset conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reset: {str(e)}")

@app.get("/conversation/status")
async def get_conversation_status(session_id: str = "default"):
    """Récupère l'état de la conversation actuelle"""
    try:
        conversation_exists = session_id in conversation_memory
        messages = conversation_memory.get(session_id, [])

        # Statistiques de la conversation
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]

        return {
            "session_id": session_id,
            "conversation_exists": conversation_exists,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_message_time": messages[-1].get("timestamp") if messages else None,
            "conversation_preview": [
                {
                    "role": msg["role"],
                    "content": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                    "timestamp": msg.get("timestamp")
                }
                for msg in messages[-3:]  # 3 derniers messages
            ],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Erreur status conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur status: {str(e)}")



@app.delete("/ia/memory/{user_id}")
async def clear_conversation_memory(user_id: int):
    """Vide la mémoire conversationnelle d'un utilisateur"""
    session_id = f"user_{user_id}"
    if session_id in conversation_memory:
        del conversation_memory[session_id]
        return {"success": True, "message": f"Mémoire conversationnelle vidée pour l'utilisateur {user_id}"}
    else:
        return {"success": False, "message": f"Aucune conversation trouvée pour l'utilisateur {user_id}"}

# ================================
# 🎭 JEU DE RÔLE IA - SIMULATION DE RENDEZ-VOUS
# ================================

import uuid
from datetime import datetime, timedelta

# Stockage des simulations actives
active_simulations = {}

class DateSimulationRequest(BaseModel):
    """Modèle pour démarrer une simulation de rendez-vous"""
    date_name: str = "Sarah"
    date_age: int = 26
    date_interests: List[str] = ["voyages", "cuisine", "sport"]
    date_personality: str = "extravertie"
    scenario: str = "premier_rendez_vous_cafe"
    user_name: str = "Alexandre"

class RoleplayMessage(BaseModel):
    """Modèle pour les messages du jeu de rôle"""
    simulation_id: str
    user_message: str
    session_id: str = "roleplay_default"

@app.post("/roleplay/start-simulation")
async def start_date_simulation(request: DateSimulationRequest):
    """Lance une simulation de rendez-vous avec IA"""
    try:
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"

        # Profil du "rendez-vous IA"
        date_profile = {
            "name": request.date_name,
            "age": request.date_age,
            "interests": request.date_interests,
            "personality": request.date_personality,
            "scenario": request.scenario
        }

        # Stockage de la simulation
        active_simulations[simulation_id] = {
            "date_profile": date_profile,
            "user_name": request.user_name,
            "messages": [],
            "started_at": datetime.now(),
            "interest_level": 50,  # Niveau d'intérêt initial
            "conversation_score": 0
        }

        # Message d'ouverture selon le scénario
        opening_messages = {
            "premier_rendez_vous_cafe": f"Salut {request.user_name} ! *sourire un peu gêné* Alors, tu as trouvé facilement ? J'espère que je ne t'ai pas fait attendre...",
            "diner_restaurant": f"Bonsoir {request.user_name} ! *sourire chaleureux* Wow, tu es très élégant ce soir ! Ce restaurant a l'air vraiment sympa.",
            "activite_fun": f"Coucou {request.user_name} ! *rire* J'avoue que je suis un peu nulle au mini-golf, j'espère que tu ne vas pas trop te moquer de moi !",
            "cafe_deuxieme_rdv": f"Salut {request.user_name} ! *sourire confiant* Ça me fait plaisir de te revoir ! Comment s'est passée ta semaine ?"
        }

        first_message = opening_messages.get(request.scenario, opening_messages["premier_rendez_vous_cafe"])

        # Coaching initial
        coaching_tips = {
            "premier_rendez_vous_cafe": "💡 Elle semble un peu nerveuse, mets-la à l'aise avec une réponse détendue et rassurante !",
            "diner_restaurant": "💡 Elle te complimente ! Remercie-la et retourne-lui un compliment sincère.",
            "activite_fun": "💡 Elle se dévalorise avec humour, c'est mignon ! Rassure-la avec bienveillance.",
            "cafe_deuxieme_rdv": "💡 Elle est plus à l'aise maintenant. Tu peux être plus personnel dans tes réponses."
        }

        initial_coaching = coaching_tips.get(request.scenario, coaching_tips["premier_rendez_vous_cafe"])

        print(f"🎭 Simulation démarrée: {simulation_id} | Scénario: {request.scenario}")

        return {
            "success": True,
            "simulation_id": simulation_id,
            "date_profile": date_profile,
            "scenario_description": get_scenario_description(request.scenario),
            "first_message": first_message,
            "coaching_tip": initial_coaching,
            "interest_level": 50,
            "tips": [
                "Sois naturel et authentique",
                "Pose des questions sur elle",
                "Écoute ses réponses attentivement",
                "Partage des choses sur toi aussi"
            ]
        }

    except Exception as e:
        print(f"❌ Erreur simulation: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/roleplay/send-message")
async def send_roleplay_message(request: RoleplayMessage):
    """Envoie un message dans la simulation et reçoit la réponse IA"""
    try:
        simulation_id = request.simulation_id
        user_message = request.user_message

        if simulation_id not in active_simulations:
            return {"success": False, "error": "Simulation non trouvée"}

        simulation = active_simulations[simulation_id]
        date_profile = simulation["date_profile"]

        # Ajouter le message utilisateur
        simulation["messages"].append({
            "sender": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # Générer la réponse IA
        ia_response = await generate_roleplay_response(user_message, simulation)

        # Ajouter la réponse IA
        simulation["messages"].append({
            "sender": "date",
            "message": ia_response,
            "timestamp": datetime.now().isoformat()
        })

        # Analyser la performance de l'utilisateur
        performance_analysis = analyze_user_performance(user_message, simulation)

        # Mettre à jour le niveau d'intérêt
        simulation["interest_level"] = calculate_interest_level(user_message, simulation)
        simulation["conversation_score"] = calculate_conversation_score(simulation)

        # Générer des suggestions de réponse
        response_suggestions = generate_response_suggestions(ia_response, simulation)

        print(f"🎭 Message échangé dans {simulation_id} | Intérêt: {simulation['interest_level']}%")

        return {
            "success": True,
            "date_response": ia_response,
            "coaching": performance_analysis,
            "interest_level": simulation["interest_level"],
            "conversation_score": simulation["conversation_score"],
            "suggestions": response_suggestions,
            "scenario_status": get_scenario_status(simulation)
        }

    except Exception as e:
        print(f"❌ Erreur message roleplay: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/roleplay/simulation/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Récupère le statut d'une simulation"""
    if simulation_id not in active_simulations:
        return {"success": False, "error": "Simulation non trouvée"}

    simulation = active_simulations[simulation_id]

    return {
        "success": True,
        "simulation": {
            "id": simulation_id,
            "date_profile": simulation["date_profile"],
            "messages": simulation["messages"],
            "interest_level": simulation["interest_level"],
            "conversation_score": simulation["conversation_score"],
            "duration": str(datetime.now() - simulation["started_at"]),
            "total_messages": len(simulation["messages"])
        }
    }

# ================================
# 🎭 FONCTIONS UTILITAIRES JEU DE RÔLE
# ================================

def get_scenario_description(scenario: str) -> str:
    """Retourne la description d'un scénario"""
    descriptions = {
        "premier_rendez_vous_cafe": "☕ Premier rendez-vous dans un café cosy. Ambiance détendue, apprendre à se connaître.",
        "diner_restaurant": "🍽️ Dîner romantique au restaurant. Deuxième rendez-vous, plus intime.",
        "activite_fun": "🎳 Activité ludique (mini-golf, bowling). Ambiance décontractée et amusante.",
        "cafe_deuxieme_rdv": "☕ Deuxième café ensemble. Plus de complicité, conversation plus personnelle."
    }
    return descriptions.get(scenario, "Rendez-vous classique")

async def generate_roleplay_response(user_message: str, simulation: dict) -> str:
    """Génère la réponse de l'IA en tant que rendez-vous"""
    date_profile = simulation["date_profile"]
    messages_history = simulation["messages"]
    interest_level = simulation.get("interest_level", 50)

    # Construire l'historique de conversation
    conversation_context = ""
    for msg in messages_history[-6:]:  # Derniers 6 messages pour contexte
        sender = "Moi" if msg["sender"] == "date" else "Lui"
        conversation_context += f"{sender}: {msg['message']}\n"

    # Prompt pour l'IA roleplay
    roleplay_prompt = f"""
    Tu es {date_profile['name']}, {date_profile['age']} ans, passionnée par {', '.join(date_profile['interests'])}.
    Tu es {date_profile['personality']} et tu es en rendez-vous.

    CONTEXTE DE LA CONVERSATION:
    {conversation_context}

    Il vient de dire: "{user_message}"

    RÈGLES IMPORTANTES:
    - Reste dans le personnage en permanence
    - Réponds comme une vraie personne lors d'un rendez-vous
    - Ton niveau d'intérêt actuel: {interest_level}/100
    - Si intérêt < 30: sois polie mais distante
    - Si intérêt 30-70: sois amicale et curieuse
    - Si intérêt > 70: sois chaleureuse et engagée
    - Pose parfois des questions sur lui
    - Réagis naturellement à ce qu'il dit
    - Sois authentique, parfois timide, parfois souriante
    - Maximum 2-3 phrases par réponse

    Réponds uniquement en tant que {date_profile['name']}:
    """

    try:
        # Utiliser l'IA existante pour générer la réponse
        response = await generate_with_best_ai(roleplay_prompt, "amical")

        # Nettoyer la réponse (enlever les préfixes comme "Sarah:")
        clean_response = response.strip()
        if clean_response.startswith(f"{date_profile['name']}:"):
            clean_response = clean_response[len(f"{date_profile['name']}:"):].strip()

        return clean_response

    except Exception as e:
        print(f"❌ Erreur génération roleplay: {str(e)}")
        return "Désolée, j'ai eu un petit blanc... Tu peux répéter ?"

def analyze_user_performance(user_message: str, simulation: dict) -> dict:
    """Analyse la performance de l'utilisateur dans la conversation"""
    message_length = len(user_message)
    question_count = user_message.count('?')
    exclamation_count = user_message.count('!')

    # Mots positifs/négatifs
    positive_words = ['super', 'génial', 'cool', 'sympa', 'bien', 'parfait', 'excellent', 'merci']
    negative_words = ['nul', 'ennuyeux', 'bizarre', 'pas terrible', 'bof']

    positive_score = sum(1 for word in positive_words if word in user_message.lower())
    negative_score = sum(1 for word in negative_words if word in user_message.lower())

    # Analyse
    analysis = {
        "message_quality": "Bonne" if message_length > 20 else "Courte",
        "engagement": "Élevé" if question_count > 0 else "Moyen",
        "enthusiasm": "Élevé" if exclamation_count > 0 else "Calme",
        "positivity": positive_score - negative_score,
        "tips": []
    }

    # Conseils personnalisés
    if message_length < 15:
        analysis["tips"].append("💡 Développe un peu plus tes réponses pour montrer ton intérêt")
    if question_count == 0 and len(simulation["messages"]) > 2:
        analysis["tips"].append("💡 Pose-lui une question pour relancer la conversation")
    if positive_score > 0:
        analysis["tips"].append("✅ Excellent ! Ton positivisme transparaît")
    if negative_score > 0:
        analysis["tips"].append("⚠️ Attention au ton, reste positif")

    if not analysis["tips"]:
        analysis["tips"].append("👍 Bonne réponse, continue comme ça !")

    return analysis

def calculate_interest_level(user_message: str, simulation: dict) -> int:
    """Calcule le niveau d'intérêt du rendez-vous basé sur le message"""
    current_interest = simulation.get("interest_level", 50)

    # Facteurs qui augmentent l'intérêt
    interest_boost = 0

    # Questions personnelles (+5)
    if '?' in user_message:
        interest_boost += 5

    # Compliments (+8)
    compliment_words = ['belle', 'jolie', 'sympa', 'cool', 'génial', 'super', 'parfait']
    if any(word in user_message.lower() for word in compliment_words):
        interest_boost += 8

    # Humour/émojis (+3)
    if any(emoji in user_message for emoji in ['😊', '😄', '😂', '🙂', '😉']) or '😊' in user_message:
        interest_boost += 3

    # Partage personnel (+6)
    personal_words = ['moi', 'je', 'mon', 'ma', 'mes']
    if sum(1 for word in personal_words if word in user_message.lower()) >= 2:
        interest_boost += 6

    # Facteurs qui diminuent l'intérêt
    interest_penalty = 0

    # Messages trop courts (-3)
    if len(user_message) < 10:
        interest_penalty += 3

    # Réponses négatives (-10)
    negative_words = ['non', 'pas vraiment', 'bof', 'mouais', 'pas terrible']
    if any(word in user_message.lower() for word in negative_words):
        interest_penalty += 10

    # Messages inappropriés (-15)
    inappropriate_words = ['sexe', 'coucher', 'nue', 'corps']
    if any(word in user_message.lower() for word in inappropriate_words):
        interest_penalty += 15

    # Calcul final
    new_interest = current_interest + interest_boost - interest_penalty
    return max(0, min(100, new_interest))

def calculate_conversation_score(simulation: dict) -> int:
    """Calcule le score global de la conversation"""
    messages = simulation["messages"]
    interest_level = simulation.get("interest_level", 50)

    if len(messages) == 0:
        return 0

    # Facteurs de score
    message_count = len(messages)
    avg_message_length = sum(len(msg["message"]) for msg in messages) / len(messages)

    # Score basé sur plusieurs facteurs
    score = (
        min(50, message_count * 5) +  # Longueur conversation (max 50)
        min(25, avg_message_length * 0.5) +  # Qualité messages (max 25)
        interest_level * 0.25  # Niveau d'intérêt (max 25)
    )

    return min(100, int(score))

def generate_response_suggestions(ia_response: str, simulation: dict) -> List[str]:
    """Génère des suggestions de réponse pour l'utilisateur"""
    date_profile = simulation["date_profile"]
    interest_level = simulation.get("interest_level", 50)

    # Suggestions basées sur la réponse de l'IA
    suggestions = []

    # Si elle pose une question
    if '?' in ia_response:
        suggestions.append("Réponds à sa question et pose-en une en retour")
        suggestions.append("Partage quelque chose de personnel sur ce sujet")

    # Si elle partage quelque chose
    if any(word in ia_response.lower() for word in ['moi', 'je', 'mon', 'ma']):
        suggestions.append("Montre de l'intérêt pour ce qu'elle partage")
        suggestions.append("Raconte une expérience similaire")

    # Si elle semble intéressée (intérêt > 60)
    if interest_level > 60:
        suggestions.append("Elle semble réceptive, tu peux être plus personnel")
        suggestions.append("C'est le moment de proposer une activité ensemble")

    # Si elle semble distante (intérêt < 40)
    elif interest_level < 40:
        suggestions.append("Essaie de relancer avec une question sur ses passions")
        suggestions.append("Reste positif et montre ton côté intéressant")

    # Suggestions générales
    if not suggestions:
        suggestions = [
            "Pose-lui une question sur ses centres d'intérêt",
            "Partage quelque chose d'amusant sur toi",
            "Complimente-la de façon sincère"
        ]

    return suggestions[:3]  # Maximum 3 suggestions

def get_scenario_status(simulation: dict) -> dict:
    """Retourne le statut du scénario"""
    interest_level = simulation.get("interest_level", 50)
    message_count = len(simulation["messages"])

    if interest_level >= 80:
        status = "🔥 Excellent ! Elle est très intéressée"
    elif interest_level >= 60:
        status = "😊 Très bien ! Bonne connexion"
    elif interest_level >= 40:
        status = "🙂 Correct, continue tes efforts"
    elif interest_level >= 20:
        status = "😐 Difficile, essaie de relancer"
    else:
        status = "😔 Compliqué, change d'approche"

    # Conseils selon la progression
    if message_count < 5:
        phase = "Début de conversation"
        advice = "Concentre-toi sur briser la glace et la mettre à l'aise"
    elif message_count < 15:
        phase = "Développement"
        advice = "Approfondis la conversation, trouve des points communs"
    else:
        phase = "Approfondissement"
        advice = "Tu peux être plus personnel et proposer une suite"

    return {
        "status": status,
        "phase": phase,
        "advice": advice,
        "message_count": message_count,
        "interest_evolution": "En hausse" if interest_level > 50 else "À améliorer"
    }

# ================================
# ANALYSE WEBCAM - NOUVEAUX ENDPOINTS
# ================================

# Stockage temporaire des analyses webcam
webcam_analyses = {}

class WebcamAnalysis(BaseModel):
    """Modèle pour les données d'analyse webcam"""
    user_id: str
    session_id: str = "default"
    timestamp: str
    emotions: dict  # {happy: 0.8, sad: 0.1, ...}
    confidence: int  # 0-100
    engagement: int  # 0-100
    authenticity: int  # 0-100
    dominant_emotion: str

@app.post("/webcam/analyze")
async def receive_webcam_analysis(analysis: WebcamAnalysis):
    """Reçoit les données d'analyse webcam du frontend"""
    try:
        user_id = analysis.user_id

        # Stockage de l'analyse
        if user_id not in webcam_analyses:
            webcam_analyses[user_id] = []

        webcam_analyses[user_id].append(analysis.model_dump())

        # Garder seulement les 10 dernières analyses
        webcam_analyses[user_id] = webcam_analyses[user_id][-10:]

        # Génération de coaching temps réel
        coaching_tip = generate_realtime_coaching(analysis)

        # Calcul des scores
        profile_scores = calculate_profile_scores(analysis)

        print(f"📹 Analyse webcam reçue pour {user_id}: {analysis.dominant_emotion} (confiance: {analysis.confidence}%)")

        return {
            "success": True,
            "coaching_tip": coaching_tip,
            "profile_scores": profile_scores,
            "analysis_stored": True,
            "total_analyses": len(webcam_analyses[user_id])
        }

    except Exception as e:
        print(f"❌ Erreur analyse webcam: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/webcam/profile-score/{user_id}")
async def get_profile_score(user_id: str):
    """Calcule le score de profil basé sur les analyses webcam"""
    try:
        if user_id not in webcam_analyses or not webcam_analyses[user_id]:
            return {"error": "Aucune analyse disponible pour cet utilisateur"}

        analyses = webcam_analyses[user_id]

        # Calcul des scores moyens
        avg_confidence = sum(a['confidence'] for a in analyses) / len(analyses)
        avg_engagement = sum(a['engagement'] for a in analyses) / len(analyses)
        avg_authenticity = sum(a['authenticity'] for a in analyses) / len(analyses)

        # Analyse des émotions dominantes
        emotion_counts = {}
        for analysis in analyses:
            emotion = analysis['dominant_emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        most_common_emotion = max(emotion_counts, key=emotion_counts.get)

        # Score de séduction global
        seduction_score = calculate_seduction_score(avg_confidence, avg_engagement, avg_authenticity, most_common_emotion)

        return {
            "user_id": user_id,
            "profile_scores": {
                "seduction_score": round(seduction_score),
                "confidence": round(avg_confidence),
                "engagement": round(avg_engagement),
                "authenticity": round(avg_authenticity),
                "dominant_emotion": most_common_emotion,
                "emotion_distribution": emotion_counts
            },
            "total_analyses": len(analyses),
            "recommendations": generate_profile_recommendations(avg_confidence, avg_engagement, avg_authenticity)
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/webcam/compatibility")
async def check_emotional_compatibility(request: dict):
    """Vérifie la compatibilité émotionnelle entre deux utilisateurs"""
    try:
        user1_id = request.get("user1_id")
        user2_id = request.get("user2_id")

        if user1_id not in webcam_analyses or user2_id not in webcam_analyses:
            return {"error": "Analyses manquantes pour l'un des utilisateurs"}

        user1_analyses = webcam_analyses[user1_id]
        user2_analyses = webcam_analyses[user2_id]

        # Calcul de compatibilité
        compatibility_score = calculate_emotional_compatibility(user1_analyses, user2_analyses)

        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "compatibility_score": round(compatibility_score),
            "compatibility_level": get_compatibility_level(compatibility_score),
            "recommendations": generate_compatibility_recommendations(compatibility_score)
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/webcam/coaching/{user_id}")
async def get_personalized_coaching(user_id: str):
    """Génère des conseils personnalisés basés sur l'historique d'analyses"""
    try:
        if user_id not in webcam_analyses or not webcam_analyses[user_id]:
            return {"error": "Aucune analyse disponible"}

        analyses = webcam_analyses[user_id]
        latest_analysis = analyses[-1]

        # Coaching personnalisé basé sur l'historique
        coaching = generate_advanced_coaching(analyses, latest_analysis)

        return {
            "user_id": user_id,
            "coaching": coaching,
            "based_on_analyses": len(analyses)
        }

    except Exception as e:
        return {"error": str(e)}

# ================================
# FONCTIONS UTILITAIRES WEBCAM
# ================================

def generate_realtime_coaching(analysis: WebcamAnalysis) -> str:
    """Génère un conseil temps réel basé sur l'analyse"""
    confidence = analysis.confidence
    dominant_emotion = analysis.dominant_emotion
    authenticity = analysis.authenticity

    if confidence < 40:
        return "💪 Redresse-toi et regarde la caméra ! Tu sembles manquer de confiance."
    elif dominant_emotion == "sad" and authenticity > 60:
        return "😊 Un sourire naturel rendrait ton profil plus attractif !"
    elif dominant_emotion == "happy" and authenticity > 70:
        return "✨ Parfait ! Ton sourire authentique est très séduisant."
    elif analysis.engagement < 50:
        return "🎯 Sois plus expressif ! Montre ta personnalité."
    elif confidence > 80 and authenticity > 80:
        return "🔥 Excellent ! Tu dégages beaucoup de charisme."
    else:
        return "👍 Continue comme ça, tu es sur la bonne voie !"

def calculate_profile_scores(analysis: WebcamAnalysis) -> dict:
    """Calcule les scores de profil instantanés"""
    return {
        "attractiveness": min(100, analysis.confidence * 0.4 + analysis.authenticity * 0.6),
        "approachability": min(100, analysis.engagement * 0.5 + (analysis.emotions.get('happy', 0) * 100) * 0.5),
        "charisma": min(100, (analysis.confidence + analysis.engagement + analysis.authenticity) / 3),
        "trustworthiness": analysis.authenticity
    }

def calculate_seduction_score(confidence: float, engagement: float, authenticity: float, dominant_emotion: str) -> float:
    """Calcule le score de séduction global"""
    base_score = (confidence * 0.3 + engagement * 0.3 + authenticity * 0.4)

    # Bonus selon l'émotion dominante
    emotion_bonus = {
        "happy": 10,
        "surprised": 5,
        "neutral": 0,
        "sad": -5,
        "angry": -10,
        "fearful": -15,
        "disgusted": -10
    }

    return min(100, base_score + emotion_bonus.get(dominant_emotion, 0))

def calculate_emotional_compatibility(user1_analyses: list, user2_analyses: list) -> float:
    """Calcule la compatibilité émotionnelle entre deux utilisateurs"""
    # Moyennes des émotions pour chaque utilisateur
    user1_emotions = calculate_average_emotions(user1_analyses)
    user2_emotions = calculate_average_emotions(user2_analyses)

    # Calcul de similarité émotionnelle
    compatibility = 0
    for emotion in user1_emotions:
        if emotion in user2_emotions:
            # Plus les émotions sont proches, plus la compatibilité est élevée
            diff = abs(user1_emotions[emotion] - user2_emotions[emotion])
            compatibility += (1 - diff) * 100

    return compatibility / len(user1_emotions) if user1_emotions else 0

def calculate_average_emotions(analyses: list) -> dict:
    """Calcule les émotions moyennes d'un utilisateur"""
    if not analyses:
        return {}

    emotion_sums = {}
    for analysis in analyses:
        for emotion, value in analysis['emotions'].items():
            emotion_sums[emotion] = emotion_sums.get(emotion, 0) + value

    return {emotion: total / len(analyses) for emotion, total in emotion_sums.items()}

def generate_profile_recommendations(confidence: float, engagement: float, authenticity: float) -> list:
    """Génère des recommandations d'amélioration de profil"""
    recommendations = []

    if confidence < 60:
        recommendations.append("Travaille ta posture et ton contact visuel pour paraître plus confiant")
    if engagement < 60:
        recommendations.append("Sois plus expressif dans tes photos et vidéos")
    if authenticity < 70:
        recommendations.append("Privilégie des expressions naturelles plutôt que forcées")

    if not recommendations:
        recommendations.append("Ton profil est excellent ! Continue comme ça.")

    return recommendations

def get_compatibility_level(score: float) -> str:
    """Détermine le niveau de compatibilité"""
    if score >= 80:
        return "Excellente compatibilité"
    elif score >= 60:
        return "Bonne compatibilité"
    elif score >= 40:
        return "Compatibilité moyenne"
    else:
        return "Compatibilité faible"

def generate_compatibility_recommendations(score: float) -> list:
    """Génère des recommandations basées sur la compatibilité"""
    if score >= 80:
        return ["Vous semblez très compatibles émotionnellement !", "C'est le moment idéal pour engager la conversation."]
    elif score >= 60:
        return ["Bonne compatibilité détectée.", "Vous pourriez bien vous entendre."]
    elif score >= 40:
        return ["Compatibilité moyenne.", "Explorez vos points communs pour mieux vous connaître."]
    else:
        return ["Compatibilité émotionnelle limitée.", "Concentrez-vous sur d'autres aspects de la personnalité."]

def generate_advanced_coaching(analyses: list, latest_analysis: dict) -> dict:
    """Génère un coaching avancé basé sur l'historique"""
    # Analyse des tendances
    confidence_trend = analyze_trend([a['confidence'] for a in analyses])
    engagement_trend = analyze_trend([a['engagement'] for a in analyses])

    return {
        "immediate_tip": generate_realtime_coaching(WebcamAnalysis(**latest_analysis)),
        "progress_analysis": {
            "confidence_trend": confidence_trend,
            "engagement_trend": engagement_trend
        },
        "long_term_goals": generate_long_term_goals(analyses),
        "strengths": identify_strengths(analyses),
        "areas_to_improve": identify_improvements(analyses)
    }

def analyze_trend(values: list) -> str:
    """Analyse la tendance d'une série de valeurs"""
    if len(values) < 2:
        return "Pas assez de données"

    recent_avg = sum(values[-3:]) / min(3, len(values))
    older_avg = sum(values[:-3]) / max(1, len(values) - 3)

    if recent_avg > older_avg + 5:
        return "En amélioration"
    elif recent_avg < older_avg - 5:
        return "En baisse"
    else:
        return "Stable"

def generate_long_term_goals(analyses: list) -> list:
    """Génère des objectifs à long terme"""
    avg_confidence = sum(a['confidence'] for a in analyses) / len(analyses)
    avg_engagement = sum(a['engagement'] for a in analyses) / len(analyses)

    goals = []
    if avg_confidence < 70:
        goals.append("Atteindre 80% de confiance moyenne")
    if avg_engagement < 70:
        goals.append("Améliorer ton expressivité à 80%")

    return goals or ["Maintenir tes excellents scores !"]

def identify_strengths(analyses: list) -> list:
    """Identifie les points forts de l'utilisateur"""
    strengths = []
    avg_confidence = sum(a['confidence'] for a in analyses) / len(analyses)
    avg_engagement = sum(a['engagement'] for a in analyses) / len(analyses)
    avg_authenticity = sum(a['authenticity'] for a in analyses) / len(analyses)

    if avg_confidence > 75:
        strengths.append("Grande confiance en soi")
    if avg_engagement > 75:
        strengths.append("Très expressif et engageant")
    if avg_authenticity > 80:
        strengths.append("Expressions très authentiques")

    return strengths or ["Continue à développer tes atouts !"]

def identify_improvements(analyses: list) -> list:
    """Identifie les axes d'amélioration"""
    improvements = []
    avg_confidence = sum(a['confidence'] for a in analyses) / len(analyses)
    avg_engagement = sum(a['engagement'] for a in analyses) / len(analyses)
    avg_authenticity = sum(a['authenticity'] for a in analyses) / len(analyses)

    if avg_confidence < 60:
        improvements.append("Travailler la confiance en soi")
    if avg_engagement < 60:
        improvements.append("Être plus expressif")
    if avg_authenticity < 70:
        improvements.append("Privilégier des expressions naturelles")

    return improvements or ["Tes scores sont excellents !"]

# ================================
# 🔍 ANALYSE DES MICRO-SIGNAUX
# ================================

class MicroSignalsRequest(BaseModel):
    """Modèle pour l'analyse des micro-signaux"""
    conversation_id: str
    messages: List[dict]  # Liste des messages avec timestamps
    user_id: str

@app.post("/micro-signals/analyze")
async def analyze_conversation_micro_signals(request: MicroSignalsRequest):
    """Analyse les micro-signaux dans une conversation"""
    try:
        conversation_id = request.conversation_id
        messages = request.messages
        user_id = request.user_id

        print(f"🔍 Analyse micro-signaux pour conversation {conversation_id}")

        if len(messages) < 3:
            return {
                "success": False,
                "error": "Pas assez de messages pour analyser les micro-signaux",
                "minimum_required": 3
            }

        # Analyser les patterns temporels
        response_times = calculate_response_times_microsignals(messages)
        message_lengths = [len(msg.get("content", "")) for msg in messages]
        emoji_usage = count_emoji_patterns(messages)
        question_frequency = count_questions(messages)

        # Analyse des tendances
        signals = {
            "interest_level": analyze_interest_trend_microsignals(response_times, message_lengths),
            "engagement_evolution": track_engagement_changes(messages),
            "emotional_indicators": detect_emotional_shifts(emoji_usage),
            "conversation_health": assess_conversation_flow(messages),
            "response_pattern": analyze_response_patterns(response_times),
            "communication_style": analyze_communication_style(messages)
        }

        # Prédictions et recommandations
        next_step_prediction = predict_next_optimal_action(signals, messages)
        optimal_timing = calculate_best_response_time(response_times)
        conversation_score = calculate_overall_conversation_score_microsignals(signals)

        return {
            "success": True,
            "conversation_id": conversation_id,
            "micro_signals": signals,
            "predictions": {
                "next_optimal_action": next_step_prediction,
                "best_response_time": optimal_timing,
                "success_probability": calculate_success_probability(signals)
            },
            "recommendations": generate_micro_signal_tips(signals, messages),
            "conversation_score": conversation_score,
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Erreur analyse micro-signaux: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/micro-signals/conversation/{conversation_id}")
async def get_conversation_insights(conversation_id: str):
    """Récupère les insights d'une conversation existante"""
    try:
        # Récupérer depuis la mémoire conversationnelle
        if conversation_id in conversation_memory:
            messages = conversation_memory[conversation_id]

            # Convertir en format attendu
            formatted_messages = []
            for i, msg in enumerate(messages):
                formatted_messages.append({
                    "content": msg,
                    "timestamp": (datetime.now() - timedelta(minutes=len(messages)-i)).isoformat(),
                    "sender": "user" if i % 2 == 0 else "assistant"
                })

            # Analyser avec les données formatées
            request = MicroSignalsRequest(
                conversation_id=conversation_id,
                messages=formatted_messages,
                user_id="default_user"
            )

            return await analyze_conversation_micro_signals(request)
        else:
            return {"success": False, "error": "Conversation non trouvée"}

    except Exception as e:
        return {"success": False, "error": str(e)}

# ================================
# 🔍 FONCTIONS UTILITAIRES MICRO-SIGNAUX
# ================================

def calculate_response_times_microsignals(messages: List[dict]) -> List[float]:
    """Calcule les temps de réponse entre messages"""
    response_times = []

    for i in range(1, len(messages)):
        try:
            prev_time = datetime.fromisoformat(messages[i-1]["timestamp"].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(messages[i]["timestamp"].replace('Z', '+00:00'))
            response_time = (curr_time - prev_time).total_seconds()
            response_times.append(response_time)
        except:
            response_times.append(300)  # 5 minutes par défaut si erreur

    return response_times

def count_emoji_patterns(messages: List[dict]) -> dict:
    """Compte les patterns d'émojis dans les messages"""
    emoji_counts = {
        "positive": 0,
        "negative": 0,
        "flirty": 0,
        "total": 0
    }

    positive_emojis = ['😊', '😄', '😂', '🙂', '😉', '❤️', '💕', '👍', '✨']
    negative_emojis = ['😔', '😞', '😕', '😐', '👎', '😒']
    flirty_emojis = ['😘', '😍', '🥰', '😏', '💋', '💕', '❤️']

    for msg in messages:
        content = msg.get("content", "")

        for emoji in positive_emojis:
            emoji_counts["positive"] += content.count(emoji)
            emoji_counts["total"] += content.count(emoji)

        for emoji in negative_emojis:
            emoji_counts["negative"] += content.count(emoji)
            emoji_counts["total"] += content.count(emoji)

        for emoji in flirty_emojis:
            emoji_counts["flirty"] += content.count(emoji)

    return emoji_counts

def count_questions(messages: List[dict]) -> dict:
    """Compte les questions dans les messages"""
    question_stats = {
        "total_questions": 0,
        "user_questions": 0,
        "assistant_questions": 0,
        "question_ratio": 0
    }

    for msg in messages:
        content = msg.get("content", "")
        question_count = content.count('?')
        question_stats["total_questions"] += question_count

        if msg.get("sender") == "user":
            question_stats["user_questions"] += question_count
        else:
            question_stats["assistant_questions"] += question_count

    if question_stats["total_questions"] > 0:
        question_stats["question_ratio"] = question_stats["user_questions"] / question_stats["total_questions"]

    return question_stats

def analyze_interest_trend_microsignals(response_times: List[float], message_lengths: List[int]) -> str:
    """Analyse l'évolution de l'intérêt"""
    if len(response_times) < 3:
        return "Pas assez de données"

    # Analyser les 3 derniers vs les 3 premiers
    recent_times = response_times[-3:]
    older_times = response_times[:3]

    avg_recent = sum(recent_times) / len(recent_times)
    avg_older = sum(older_times) / len(older_times)

    # Analyser aussi la longueur des messages
    recent_lengths = message_lengths[-3:]
    older_lengths = message_lengths[:3]

    avg_recent_length = sum(recent_lengths) / len(recent_lengths)
    avg_older_length = sum(older_lengths) / len(older_lengths)

    # Temps de réponse qui diminue + messages plus longs = intérêt croissant
    if avg_recent < avg_older * 0.7 and avg_recent_length > avg_older_length * 1.2:
        return "Intérêt croissant fort"
    elif avg_recent < avg_older and avg_recent_length > avg_older_length:
        return "Intérêt croissant"
    elif avg_recent > avg_older * 1.5 and avg_recent_length < avg_older_length * 0.8:
        return "Intérêt décroissant"
    else:
        return "Intérêt stable"

def track_engagement_changes(messages: List[dict]) -> dict:
    """Suit les changements d'engagement dans la conversation"""
    if len(messages) < 4:
        return {"status": "Pas assez de données"}

    # Diviser en segments pour analyser l'évolution
    mid_point = len(messages) // 2
    first_half = messages[:mid_point]
    second_half = messages[mid_point:]

    # Calculer l'engagement pour chaque moitié
    first_engagement = calculate_segment_engagement(first_half)
    second_engagement = calculate_segment_engagement(second_half)

    evolution = second_engagement - first_engagement

    if evolution > 15:
        trend = "Engagement en forte hausse"
    elif evolution > 5:
        trend = "Engagement en hausse"
    elif evolution < -15:
        trend = "Engagement en forte baisse"
    elif evolution < -5:
        trend = "Engagement en baisse"
    else:
        trend = "Engagement stable"

    return {
        "trend": trend,
        "first_half_score": first_engagement,
        "second_half_score": second_engagement,
        "evolution": evolution
    }

def calculate_segment_engagement(messages: List[dict]) -> int:
    """Calcule le score d'engagement pour un segment de messages"""
    if not messages:
        return 0

    total_score = 0

    for msg in messages:
        content = msg.get("content", "")

        # Facteurs d'engagement
        score = 0
        score += len(content) * 0.1  # Longueur du message
        score += content.count('?') * 5  # Questions
        score += content.count('!') * 3  # Exclamations
        score += content.count('😊') * 2  # Émojis positifs

        total_score += score

    return int(total_score / len(messages))

def detect_emotional_shifts(emoji_usage: dict) -> dict:
    """Détecte les changements émotionnels"""
    total_emojis = emoji_usage.get("total", 0)

    if total_emojis == 0:
        return {"status": "Pas d'émojis détectés", "emotional_tone": "Neutre"}

    positive_ratio = emoji_usage.get("positive", 0) / total_emojis
    flirty_ratio = emoji_usage.get("flirty", 0) / total_emojis
    negative_ratio = emoji_usage.get("negative", 0) / total_emojis

    if flirty_ratio > 0.3:
        emotional_tone = "Flirteur"
    elif positive_ratio > 0.7:
        emotional_tone = "Très positif"
    elif positive_ratio > 0.4:
        emotional_tone = "Positif"
    elif negative_ratio > 0.3:
        emotional_tone = "Négatif"
    else:
        emotional_tone = "Neutre"

    return {
        "emotional_tone": emotional_tone,
        "positive_ratio": round(positive_ratio, 2),
        "flirty_ratio": round(flirty_ratio, 2),
        "negative_ratio": round(negative_ratio, 2)
    }

def assess_conversation_flow(messages: List[dict]) -> str:
    """Évalue la fluidité de la conversation"""
    if len(messages) < 4:
        return "Conversation trop courte pour évaluer"

    # Analyser l'équilibre des échanges
    user_messages = sum(1 for msg in messages if msg.get("sender") == "user")
    total_messages = len(messages)
    user_ratio = user_messages / total_messages

    # Analyser la longueur moyenne des messages
    avg_length = sum(len(msg.get("content", "")) for msg in messages) / len(messages)

    # Analyser la fréquence des questions
    total_questions = sum(msg.get("content", "").count('?') for msg in messages)
    question_density = total_questions / len(messages)

    # Évaluation globale
    if 0.4 <= user_ratio <= 0.6 and avg_length > 30 and question_density > 0.3:
        return "Excellente fluidité"
    elif 0.3 <= user_ratio <= 0.7 and avg_length > 20:
        return "Bonne fluidité"
    elif avg_length < 15:
        return "Messages trop courts"
    elif user_ratio < 0.3:
        return "Utilisateur peu engagé"
    elif user_ratio > 0.7:
        return "Utilisateur très dominant"
    else:
        return "Fluidité correcte"

def analyze_response_patterns(response_times: List[float]) -> dict:
    """Analyse les patterns de temps de réponse"""
    if len(response_times) < 3:
        return {"status": "Pas assez de données"}

    avg_response_time = sum(response_times) / len(response_times)

    # Catégoriser les temps de réponse
    if avg_response_time < 60:  # Moins d'1 minute
        speed = "Très rapide"
        interpretation = "Très engagé dans la conversation"
    elif avg_response_time < 300:  # Moins de 5 minutes
        speed = "Rapide"
        interpretation = "Bien engagé"
    elif avg_response_time < 1800:  # Moins de 30 minutes
        speed = "Modéré"
        interpretation = "Engagement moyen"
    else:
        speed = "Lent"
        interpretation = "Faible engagement ou occupé"

    # Analyser la consistance
    response_variance = sum((t - avg_response_time) ** 2 for t in response_times) / len(response_times)
    consistency = "Consistant" if response_variance < 10000 else "Variable"

    return {
        "average_response_time": round(avg_response_time, 2),
        "speed_category": speed,
        "interpretation": interpretation,
        "consistency": consistency,
        "variance": round(response_variance, 2)
    }

def analyze_communication_style(messages: List[dict]) -> dict:
    """Analyse le style de communication"""
    if not messages:
        return {"status": "Pas de messages"}

    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    total_messages = len(messages)
    avg_message_length = total_chars / total_messages

    # Compter les caractéristiques
    total_questions = sum(msg.get("content", "").count('?') for msg in messages)
    total_exclamations = sum(msg.get("content", "").count('!') for msg in messages)
    total_emojis = sum(len([c for c in msg.get("content", "") if c in '😊😄😂🙂😉❤️💕👍✨😘😍🥰😏💋']) for msg in messages)

    # Déterminer le style
    if avg_message_length > 100:
        verbosity = "Très expressif"
    elif avg_message_length > 50:
        verbosity = "Expressif"
    elif avg_message_length > 20:
        verbosity = "Modéré"
    else:
        verbosity = "Concis"

    question_ratio = total_questions / total_messages
    if question_ratio > 0.5:
        curiosity = "Très curieux"
    elif question_ratio > 0.2:
        curiosity = "Curieux"
    else:
        curiosity = "Peu de questions"

    emoji_ratio = total_emojis / total_messages
    if emoji_ratio > 2:
        expressiveness = "Très expressif"
    elif emoji_ratio > 1:
        expressiveness = "Expressif"
    elif emoji_ratio > 0.5:
        expressiveness = "Modérément expressif"
    else:
        expressiveness = "Peu expressif"

    return {
        "verbosity": verbosity,
        "curiosity": curiosity,
        "expressiveness": expressiveness,
        "avg_message_length": round(avg_message_length, 1),
        "question_ratio": round(question_ratio, 2),
        "emoji_ratio": round(emoji_ratio, 2)
    }

def predict_next_optimal_action(signals: dict, messages: List[dict]) -> str:
    """Prédit la prochaine action optimale"""
    interest_level = signals.get("interest_level", "")
    engagement = signals.get("engagement_evolution", {})
    conversation_health = signals.get("conversation_health", "")

    # Logique de prédiction
    if "croissant fort" in interest_level and engagement.get("trend", "").startswith("Engagement en hausse"):
        return "C'est le moment parfait pour proposer un rendez-vous !"
    elif "croissant" in interest_level:
        return "Continue sur cette lancée, approfondis la conversation"
    elif "décroissant" in interest_level:
        return "Relance avec une question sur ses passions"
    elif "stable" in interest_level and "Excellente" in conversation_health:
        return "Partage quelque chose de plus personnel"
    else:
        return "Pose une question ouverte pour relancer l'échange"

def calculate_best_response_time(response_times: List[float]) -> str:
    """Calcule le meilleur moment pour répondre"""
    if not response_times:
        return "Pas assez de données"

    avg_time = sum(response_times) / len(response_times)

    if avg_time < 60:
        return "Réponds rapidement (dans la minute)"
    elif avg_time < 300:
        return "Réponds dans les 5 minutes"
    elif avg_time < 1800:
        return "Réponds dans les 30 minutes"
    else:
        return "Tu peux prendre ton temps (1h+)"

def calculate_success_probability(signals: dict) -> int:
    """Calcule la probabilité de succès de la conversation"""
    score = 50  # Score de base

    interest_level = signals.get("interest_level", "")
    engagement = signals.get("engagement_evolution", {})
    emotional_tone = signals.get("emotional_indicators", {}).get("emotional_tone", "")
    conversation_health = signals.get("conversation_health", "")

    # Ajustements basés sur les signaux
    if "croissant fort" in interest_level:
        score += 25
    elif "croissant" in interest_level:
        score += 15
    elif "décroissant" in interest_level:
        score -= 20

    if engagement.get("trend", "").startswith("Engagement en hausse"):
        score += 15
    elif engagement.get("trend", "").startswith("Engagement en baisse"):
        score -= 15

    if emotional_tone in ["Très positif", "Flirteur"]:
        score += 20
    elif emotional_tone == "Positif":
        score += 10
    elif emotional_tone == "Négatif":
        score -= 25

    if "Excellente" in conversation_health:
        score += 15
    elif "Bonne" in conversation_health:
        score += 10
    elif "peu engagé" in conversation_health:
        score -= 20

    return max(0, min(100, score))

def generate_micro_signal_tips(signals: dict, messages: List[dict]) -> List[str]:
    """Génère des conseils basés sur les micro-signaux"""
    tips = []

    interest_level = signals.get("interest_level", "")
    engagement = signals.get("engagement_evolution", {})
    communication_style = signals.get("communication_style", {})

    # Conseils basés sur l'intérêt
    if "décroissant" in interest_level:
        tips.append("⚠️ Son intérêt semble diminuer, change de sujet ou pose une question sur ses passions")
    elif "croissant" in interest_level:
        tips.append("✅ Excellent ! Elle s'intéresse de plus en plus à toi")

    # Conseils basés sur l'engagement
    if engagement.get("trend", "").endswith("baisse"):
        tips.append("💡 Relance l'engagement avec une anecdote personnelle amusante")

    # Conseils basés sur le style de communication
    verbosity = communication_style.get("verbosity", "")
    if verbosity == "Concis":
        tips.append("📝 Tes messages sont courts, développe un peu plus pour montrer ton intérêt")
    elif verbosity == "Très expressif":
        tips.append("👍 Parfait ! Tu es très expressif, continue comme ça")

    curiosity = communication_style.get("curiosity", "")
    if curiosity == "Peu de questions":
        tips.append("❓ Pose-lui plus de questions pour montrer que tu t'intéresses à elle")

    # Conseil général si pas de conseils spécifiques
    if not tips:
        tips.append("🎯 Continue la conversation naturellement, tout va bien !")

    return tips

def calculate_overall_conversation_score_microsignals(signals: dict) -> int:
    """Calcule le score global de la conversation basé sur les micro-signaux"""
    score = 0

    # Score basé sur l'intérêt (30 points max)
    interest_level = signals.get("interest_level", "")
    if "croissant fort" in interest_level:
        score += 30
    elif "croissant" in interest_level:
        score += 20
    elif "stable" in interest_level:
        score += 15
    elif "décroissant" in interest_level:
        score += 5

    # Score basé sur l'engagement (25 points max)
    engagement = signals.get("engagement_evolution", {})
    if engagement.get("trend", "").startswith("Engagement en forte hausse"):
        score += 25
    elif engagement.get("trend", "").startswith("Engagement en hausse"):
        score += 20
    elif engagement.get("trend", "").startswith("Engagement stable"):
        score += 15
    elif engagement.get("trend", "").startswith("Engagement en baisse"):
        score += 5

    # Score basé sur les émotions (25 points max)
    emotional_tone = signals.get("emotional_indicators", {}).get("emotional_tone", "")
    if emotional_tone == "Flirteur":
        score += 25
    elif emotional_tone == "Très positif":
        score += 20
    elif emotional_tone == "Positif":
        score += 15
    elif emotional_tone == "Neutre":
        score += 10
    elif emotional_tone == "Négatif":
        score += 0

    # Score basé sur la fluidité (20 points max)
    conversation_health = signals.get("conversation_health", "")
    if "Excellente" in conversation_health:
        score += 20
    elif "Bonne" in conversation_health:
        score += 15
    elif "correcte" in conversation_health:
        score += 10
    else:
        score += 5

    return min(100, score)

if __name__ == "__main__":
    import uvicorn
    print("🎵 MeetVoice Questions - Démarrage")
    print(f"📝 {len(QUESTIONS)} questions d'inscription disponibles")
    print("🌐 Serveur: http://localhost:8001")
    print("📚 Documentation: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
