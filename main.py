from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import edge_tts
import os
import hashlib
import requests
import asyncio
import base64
from dotenv import load_dotenv
import io
from PIL import Image
import tempfile
import uuid
import webbrowser
import subprocess
from playwright.async_api import async_playwright
import feedparser
from bs4 import BeautifulSoup
import json
import urllib.parse

# Charger les variables d'environnement
load_dotenv()

# API ultra-légère
app = FastAPI(title="MeetVoice TTS", version="2.0")
# Configuration CORS spécifique (évite les conflits avec Nginx)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",      # Vue.js dev
        "http://localhost:8083",      # Vue.js dev (votre port)
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8083",
        "https://aaaazealmmmma.duckdns.org",  # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"],
    expose_headers=["Content-Length", "Content-Type"],
)

# Questions d'inscription humanisées
QUESTIONS = [
    "Bonjour ! Je m'appelle Sophie et je suis ravie de vous accompagner dans votre inscription sur MeetVoice. Commençons par le commencement : quel nom d'utilisateur souhaitez-vous choisir ?",
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
    "Maintenant, la question que j'adore : parlez-moi de vous ! Qu'est-ce qui vous rend unique et spécial ?",
    "Pour vous proposer des rencontres près de chez vous, acceptez-vous de partager votre localisation ?",
    "Parfait ! Maintenant, ajoutons une belle photo de vous pour compléter votre profil !",
    "Question légale obligatoire : confirmez-vous être âgé de 18 ans ou plus ?",
    "Dernière étape : acceptez-vous nos conditions d'utilisation et notre politique de confidentialité ?",
    "Fantastique ! Merci d'avoir pris le temps de remplir ce formulaire. Votre inscription est maintenant en cours de traitement et vous devriez bientôt pouvoir découvrir MeetVoice !"
]

# Voix unique - Denise
VOICE = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"

# Mapping des noms de voix simplifiés
VOICE_MAPPING = {
    "denise": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)",
    "henri": "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)",
    "alain": "Microsoft Server Speech Text to Speech Voice (fr-FR, AlainNeural)",
    "brigitte": "Microsoft Server Speech Text to Speech Voice (fr-FR, BrigitteNeural)",
    "celeste": "Microsoft Server Speech Text to Speech Voice (fr-FR, CelesteNeural)",
    "claude": "Microsoft Server Speech Text to Speech Voice (fr-FR, ClaudeNeural)",
    "coralie": "Microsoft Server Speech Text to Speech Voice (fr-FR, CoralieNeural)",
    "jacqueline": "Microsoft Server Speech Text to Speech Voice (fr-FR, JacquelineNeural)",
    "jerome": "Microsoft Server Speech Text to Speech Voice (fr-FR, JeromeNeural)",
    "josephine": "Microsoft Server Speech Text to Speech Voice (fr-FR, JosephineNeural)",
    "maurice": "Microsoft Server Speech Text to Speech Voice (fr-FR, MauriceNeural)",
    "yves": "Microsoft Server Speech Text to Speech Voice (fr-FR, YvesNeural)",
    "yvette": "Microsoft Server Speech Text to Speech Voice (fr-FR, YvetteNeural)"
}

def normalize_voice_name(voice_name: str) -> str:
    """Normalise le nom de voix (accepte les noms courts et complets)"""
    if not voice_name:
        return VOICE

    # Si c'est déjà un nom complet, le retourner
    if "Microsoft Server Speech Text to Speech Voice" in voice_name:
        return voice_name

    # Sinon, chercher dans le mapping
    voice_lower = voice_name.lower()
    return VOICE_MAPPING.get(voice_lower, VOICE)

def extract_selling_points(physique: str, gouts: str) -> dict:
    """Extrait les éléments vendeurs (non-visibles) du profil"""
    selling_points = {
        "languages": [],
        "music": [],
        "personality": [],
        "origin": "",
        "unique_traits": []
    }

    if physique:
        # Extraire l'origine (vendeur car culturel)
        if "origine:" in physique.lower():
            origin_part = physique.lower().split("origine:")[1].strip()
            if origin_part and origin_part != "non spécifié":
                selling_points["origin"] = origin_part.capitalize()

    if gouts:
        gouts_lower = gouts.lower()

        # Extraire les langues (très vendeur car rare)
        if "langues:" in gouts_lower:
            lang_part = gouts_lower.split("langues:")[1].strip()
            if lang_part:
                # Nettoyer et séparer les langues
                languages = [lang.strip().capitalize() for lang in lang_part.replace(",", " ").split() if lang.strip()]
                selling_points["languages"] = languages

        # Extraire la musique (vendeur car révèle la personnalité)
        if "musique:" in gouts_lower:
            music_part = gouts_lower.split("musique:")[1].split(".")[0].strip()
            if music_part:
                music_styles = [style.strip() for style in music_part.replace(",", " ").split() if style.strip()]
                selling_points["music"] = music_styles

        # Extraire le caractère (très vendeur)
        if "caractère:" in gouts_lower:
            char_part = gouts_lower.split("caractère:")[1].split(".")[0].strip()
            if char_part:
                traits = [trait.strip().capitalize() for trait in char_part.replace(",", " ").split() if trait.strip()]
                selling_points["personality"] = traits

    return selling_points


# Modèles
class TTSRequest(BaseModel):
    text: str
    voice: str = VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"

class IARequest(BaseModel):
    prompt: str
    include_prompt_audio: bool = False  # Par défaut False pour économiser la bande passante
    voice: str = VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"

class IASimpleRequest(BaseModel):
    prompt: str

class ImageRequest(BaseModel):
    prompt: str
    style: str = "realistic"  # realistic, artistic, cartoon, portrait
    size: str = "1024x1024"  # 512x512, 1024x1024, 1024x1536
    quality: str = "standard"  # standard, hd

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5
    open_browser: bool = True  # Ouvrir automatiquement dans le navigateur

class NewsRequest(BaseModel):
    topic: str = "actualités"
    category: str = "general"  # general, technology, health, sports, entertainment
    max_results: int = 5
    open_browser: bool = True

class BrowseRequest(BaseModel):
    url: str
    action: str = "open"  # open, screenshot, extract_text
    open_browser: bool = True

class DescriptionRequest(BaseModel):
    user_info: dict = {}  # Informations utilisateur (âge, intérêts, etc.)
    style: str = "attractif"  # attractif, drôle, mystérieux, sincère
    length: str = "moyen"  # court, moyen, long

class MessageRequest(BaseModel):
    sender_id: str
    recipient_id: str
    message_type: str = "first_message"  # first_message, response, continuation
    context: dict = {}  # Profil du destinataire, historique conversation
    style: str = "attractif"  # attractif, drôle, sincère, mystérieux
    max_length: int = 500

class ResponseRequest(BaseModel):
    sender_id: str
    recipient_id: str
    received_message: str
    conversation_history: list = []
    sender_profile: dict = {}
    recipient_profile: dict = {}
    style: str = "attractif"
    max_length: int = 500

class InstantMessageRequest(BaseModel):
    room_id: str
    user_id: str
    partial_message: str  # Message en cours de frappe
    request_suggestion: bool = True

# Cache simple
def get_cache_path(text: str) -> str:
    cache_key = hashlib.md5(text.encode()).hexdigest()
    os.makedirs("cache", exist_ok=True)
    return f"cache/{cache_key}.mp3"

async def generate_tts(text: str, voice: str = VOICE, rate: str = "+0%", pitch: str = "+0Hz") -> str:
    # Normaliser le nom de voix
    normalized_voice = normalize_voice_name(voice)

    cache_path = get_cache_path(f"{text}_{normalized_voice}_{rate}_{pitch}")
    if os.path.exists(cache_path):
        return cache_path

    communicate = edge_tts.Communicate(text=text, voice=normalized_voice, rate=rate, pitch=pitch)
    await communicate.save(cache_path)
    return cache_path

async def generate_tts_bytes(text: str, voice: str = VOICE, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Génère TTS et retourne les bytes directement"""
    cache_path = await generate_tts(text, voice, rate, pitch)
    with open(cache_path, 'rb') as f:
        return f.read()

async def call_deepinfra_model(prompt: str, system_prompt: str = "", model: str = None) -> str:
    """Appel à l'API DeepInfra avec modèle spécifique"""
    try:
        deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        if not model:
            model = os.getenv('DEEPINFRA_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')

        if not deepinfra_key:
            raise Exception("DEEPINFRA_API_KEY non configurée")

        url = f"https://api.deepinfra.com/v1/openai/chat/completions"

        headers = {
            "Authorization": f"Bearer {deepinfra_key}",
            "Content-Type": "application/json"
        }

        # Format OpenAI compatible pour DeepInfra
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Paramètres adaptés selon le modèle
        if "Qwen" in model:
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 600,
                "temperature": 0.6,
                "top_p": 0.8
            }
        elif "Kokoro" in model:
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.8,
                "top_p": 0.9
            }
        else:  # Llama et autres
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.9
            }

        # Appel synchrone dans un thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, headers=headers, json=data, timeout=30)
        )

        response.raise_for_status()
        result = response.json()

        # Traitement de la réponse format OpenAI
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']['content']
            return message.strip()
        else:
            return "Désolée, je n'ai pas pu générer de réponse."

    except Exception as e:
        print(f"Erreur DeepInfra {model}: {str(e)}")
        raise Exception(f"DeepInfra {model} indisponible: {str(e)}")

async def call_deepinfra(prompt: str, system_prompt: str = "") -> str:
    """Fonction de compatibilité - utilise le modèle par défaut"""
    return await call_deepinfra_model(prompt, system_prompt)

async def call_google_gemini(prompt: str, system_prompt: str = "") -> str:
    """Appel à l'API Google Gemini (prioritaire)"""
    try:
        import google.generativeai as genai

        google_key = os.getenv('GOOGLE_API_KEY')
        if not google_key:
            raise Exception("GOOGLE_API_KEY non configurée")

        genai.configure(api_key=google_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Construction du prompt complet
        full_prompt = f"{system_prompt}\n\nQuestion: {prompt}\n\nRéponds de manière empathique et professionnelle:"

        response = model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        print(f"Erreur Google Gemini: {str(e)}")
        raise Exception(f"Google Gemini indisponible: {str(e)}")

def choose_best_ai_model(prompt: str, category: str) -> dict:
    """Choisit le meilleur modèle IA selon la complexité et le type de question"""
    prompt_lower = prompt.lower()

    # Analyse de la complexité
    complexity_indicators = [
        "pourquoi", "comment expliquer", "analyse", "comprendre", "complexe",
        "psychologie", "philosophie", "sociologie", "neurologie"
    ]

    # Analyse de la longueur et complexité
    word_count = len(prompt.split())
    complexity_score = sum(1 for indicator in complexity_indicators if indicator in prompt_lower)
    is_complex = complexity_score > 1 or word_count > 20

    # Indicateurs pour chaque type de modèle
    gemini_indicators = [
        "qu'est-ce que", "définition", "expliquer", "différence", "scientifique",
        "médical", "psychologique", "émotions", "sentiments"
    ]

    llama_indicators = [
        "que faire", "comment faire", "étapes", "technique", "conseil",
        "draguer", "aborder", "séduire", "flirter", "pratique"
    ]

    qwen_indicators = [
        "analyse", "compare", "évalue", "complexe", "nuancé", "subtil"
    ]

    # Calcul des scores
    gemini_score = sum(1 for indicator in gemini_indicators if indicator in prompt_lower)
    llama_score = sum(1 for indicator in llama_indicators if indicator in prompt_lower)
    qwen_score = sum(1 for indicator in qwen_indicators if indicator in prompt_lower)

    # Logique de sélection
    if category == "psychology" and is_complex:
        return {"provider": "google_gemini", "model": "gemini-pro", "reason": "Psychologie complexe"}
    elif category == "sexology":
        return {"provider": "google_gemini", "model": "gemini-pro", "reason": "Questions médicales"}
    elif category == "seduction" and llama_score > 0:
        return {"provider": "deepinfra", "model": "Qwen/Qwen2.5-72B-Instruct", "reason": "Conseils pratiques optimisés"}
    elif qwen_score > gemini_score and qwen_score > llama_score:
        return {"provider": "deepinfra", "model": "Qwen/Qwen2.5-72B-Instruct", "reason": "Analyse nuancée avancée"}
    elif is_complex or gemini_score > llama_score:
        return {"provider": "google_gemini", "model": "gemini-1.5-flash", "reason": "Question complexe"}
    else:
        return {"provider": "deepinfra", "model": "Qwen/Qwen2.5-72B-Instruct", "reason": "Réponse directe optimisée"}

def should_use_gemini(prompt: str, category: str) -> bool:
    """Fonction de compatibilité - utilise le nouveau système"""
    choice = choose_best_ai_model(prompt, category)
    return choice["provider"] == "google_gemini"

async def call_ai_with_smart_routing(prompt: str, system_prompt: str = "", category: str = "general") -> tuple[str, str]:
    """Appel IA avec routage intelligent selon le type de question"""

    # Choisir le meilleur modèle
    ai_choice = choose_best_ai_model(prompt, category)
    provider = ai_choice["provider"]
    model = ai_choice["model"]
    reason = ai_choice["reason"]

    print(f"🤖 Routage: {provider} ({model}) - Raison: {reason}")

    # Essayer le modèle principal choisi
    if provider == "google_gemini":
        try:
            response = await call_google_gemini(prompt, system_prompt)
            return response, f"google_gemini ({reason})"
        except Exception as e:
            print(f"Google Gemini échoué: {str(e)}")
            # Fallback vers DeepInfra avec modèle adapté
            try:
                fallback_model = "Qwen/Qwen2.5-72B-Instruct"
                response = await call_deepinfra_model(prompt, system_prompt, fallback_model)
                return response, f"deepinfra_fallback ({fallback_model})"
            except Exception as e:
                print(f"DeepInfra fallback échoué: {str(e)}")
    else:
        # DeepInfra avec modèle spécifique
        try:
            response = await call_deepinfra_model(prompt, system_prompt, model)
            return response, f"deepinfra ({model}) - {reason}"
        except Exception as e:
            print(f"DeepInfra {model} échoué: {str(e)}")
            # Fallback vers Gemini
            try:
                response = await call_google_gemini(prompt, system_prompt)
                return response, f"google_gemini_fallback"
            except Exception as e:
                print(f"Google Gemini fallback échoué: {str(e)}")
                # Dernier fallback vers Qwen
                try:
                    fallback_model = "Qwen/Qwen2.5-72B-Instruct"
                    response = await call_deepinfra_model(prompt, system_prompt, fallback_model)
                    return response, f"deepinfra_last_fallback ({fallback_model})"
                except Exception as e:
                    print(f"Dernier fallback échoué: {str(e)}")

    # Si tout échoue, utiliser le mode démo
    demo_response = generate_demo_response(prompt, category)
    return demo_response, "demo_mode"

def generate_demo_response(prompt: str, category: str) -> str:
    """Génère une réponse démo intelligente selon la catégorie"""
    prompt_lower = prompt.lower()

    # Réponses par catégorie
    if category == "seduction":
        if "aborder" in prompt_lower or "draguer" in prompt_lower:
            return "Pour aborder quelqu'un naturellement : 1) Souris et établis un contact visuel, 2) Commence par un compliment sincère ou une observation sur l'environnement, 3) Pose une question ouverte pour engager la conversation. L'authenticité est ta meilleure arme !"
        elif "confiance" in prompt_lower:
            return "Pour gagner en confiance : Travaille ta posture (dos droit, épaules détendues), pratique des affirmations positives, et rappelle-toi tes succès passés. La confiance se construit petit à petit !"
        else:
            return "En séduction, l'authenticité prime sur les techniques. Sois toi-même, écoute activement, et montre un intérêt sincère. Le charme naturel vaut mieux que les artifices !"

    elif category == "psychology":
        if "anxiété" in prompt_lower or "stress" in prompt_lower:
            return "L'anxiété avant un rendez-vous est normale ! Techniques : respiration profonde (4-7-8), visualisation positive, et rappelle-toi que l'autre personne peut être aussi nerveuse. Concentre-toi sur le plaisir de découvrir quelqu'un !"
        elif "émotions" in prompt_lower:
            return "Les émotions contradictoires en amour sont humaines. Elles reflètent souvent nos peurs et nos désirs. Prends le temps d'identifier chaque émotion et sa source. L'auto-compassion est clé !"
        else:
            return "Psychologiquement, les relations nous révèlent beaucoup sur nous-mêmes. Chaque interaction est une opportunité d'apprendre et de grandir. Sois patient avec toi-même !"

    elif category == "sexology":
        if "libido" in prompt_lower:
            return "La libido varie selon de nombreux facteurs : stress, hormones, relation, santé. C'est normal qu'elle fluctue. Communication avec ton/ta partenaire et consultation médicale si préoccupations persistantes."
        else:
            return "En sexologie, la communication et le consentement sont fondamentaux. Chaque personne est unique, prenez le temps de vous découvrir mutuellement sans pression."

    elif category == "friendship":
        return "En tant qu'amie, je te conseille d'être patient avec toi-même. Les relations prennent du temps à se développer. Reste authentique, communique tes besoins, et n'oublie pas de prendre soin de toi !"

    else:  # general
        if "bonjour" in prompt_lower:
            return "Un simple 'Bonjour' avec un sourire sincère est parfait ! Tu peux ajouter un compliment sur quelque chose que tu remarques (style, sourire, etc.) ou poser une question sur le contexte."
        else:
            return "Chaque situation relationnelle est unique. L'important est de rester authentique, d'écouter activement, et de communiquer avec bienveillance. Tu as tout en toi pour réussir !"

async def generate_image_deepinfra(prompt: str, style: str = "realistic", size: str = "1024x1024") -> str:
    """Génère une image avec DeepInfra"""
    try:
        deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        image_model = os.getenv('DEEPINFRA_MODEL_IMAGE', 'stabilityai/sd3.5')

        if not deepinfra_key:
            raise Exception("DEEPINFRA_API_KEY non configurée")

        url = f"https://api.deepinfra.com/v1/inference/{image_model}"

        # Améliorer le prompt selon le style
        style_prompts = {
            "realistic": "photorealistic, high quality, detailed, professional photography",
            "artistic": "artistic, creative, beautiful, aesthetic, masterpiece",
            "cartoon": "cartoon style, animated, colorful, fun, illustration",
            "portrait": "portrait photography, professional headshot, studio lighting, high quality"
        }

        enhanced_prompt = f"{prompt}, {style_prompts.get(style, style_prompts['realistic'])}"

        headers = {
            "Authorization": f"Bearer {deepinfra_key}",
            "Content-Type": "application/json"
        }

        # Convertir la taille
        width, height = map(int, size.split('x'))

        data = {
            "prompt": enhanced_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
            "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy"
        }

        # Appel synchrone dans un thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, headers=headers, json=data, timeout=60)
        )

        response.raise_for_status()
        result = response.json()

        # Récupérer l'image en base64
        if 'images' in result and len(result['images']) > 0:
            image_b64 = result['images'][0]
            # Corriger le padding base64 si nécessaire
            missing_padding = len(image_b64) % 4
            if missing_padding:
                image_b64 += '=' * (4 - missing_padding)
            return image_b64
        else:
            raise Exception("Aucune image générée")

    except Exception as e:
        print(f"Erreur génération image: {str(e)}")
        raise Exception(f"Génération d'image échouée: {str(e)}")

def optimize_image_prompt_for_meetvoice(prompt: str, category: str = "general") -> str:
    """Optimise le prompt d'image pour MeetVoice"""

    # Mots-clés à éviter pour rester approprié
    safe_prompt = prompt.lower()

    # Suggestions selon la catégorie
    if category == "seduction":
        if "profil" in safe_prompt or "photo" in safe_prompt:
            return f"Professional headshot portrait, {prompt}, confident smile, good lighting, attractive, stylish"
        elif "style" in safe_prompt or "look" in safe_prompt:
            return f"Fashion photography, {prompt}, trendy, stylish, modern, attractive"
    elif category == "psychology":
        return f"Calming, peaceful, {prompt}, serene atmosphere, soft lighting, wellness"
    elif category == "friendship":
        return f"Friendly, warm, {prompt}, positive vibes, social, happy"

    # Par défaut
    return f"High quality, {prompt}, professional, clean, modern"

# Variables globales pour le nettoyage
image_cache = {}
last_cleanup = 0

def cleanup_old_images():
    """Nettoie les images en cache plus anciennes que 5 minutes"""
    global image_cache, last_cleanup
    import time

    current_time = time.time()

    # Nettoyer seulement toutes les 60 secondes
    if current_time - last_cleanup < 60:
        return

    # Supprimer les images plus anciennes que 5 minutes (300 secondes)
    expired_keys = []
    for key, data in image_cache.items():
        if current_time - data['timestamp'] > 300:  # 5 minutes
            expired_keys.append(key)

    for key in expired_keys:
        del image_cache[key]
        print(f"🗑️ Image supprimée du cache: {key}")

    last_cleanup = current_time

    if expired_keys:
        print(f"🧹 Nettoyage: {len(expired_keys)} images supprimées")

def store_image_temporarily(image_b64: str) -> str:
    """Stocke temporairement une image et retourne un ID unique"""
    import time

    # Nettoyer les anciennes images
    cleanup_old_images()

    # Générer un ID unique
    image_id = str(uuid.uuid4())

    # Stocker avec timestamp
    image_cache[image_id] = {
        'data': image_b64,
        'timestamp': time.time()
    }

    print(f"💾 Image stockée temporairement: {image_id}")
    return image_id

def get_and_delete_image(image_id: str) -> str:
    """Récupère une image et la supprime immédiatement du cache"""
    if image_id in image_cache:
        image_data = image_cache[image_id]['data']
        del image_cache[image_id]
        print(f"🗑️ Image récupérée et supprimée: {image_id}")
        return image_data
    else:
        raise Exception(f"Image non trouvée: {image_id}")

# ==================== FONCTIONS WEB ====================

async def search_web_duckduckgo(query: str, max_results: int = 5) -> list:
    """Recherche web avec DuckDuckGo (plus permissif)"""
    try:
        # DuckDuckGo est plus tolérant aux requêtes automatisées
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        results = []
        search_results = soup.find_all('div', class_='result')[:max_results]

        for result in search_results:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem:
                title = title_elem.get_text().strip()
                link = title_elem.get('href')
                snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                # Nettoyer l'URL DuckDuckGo
                if link.startswith('/l/?uddg='):
                    link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])

                results.append({
                    'title': title,
                    'url': link,
                    'snippet': snippet,
                    'source': 'DuckDuckGo'
                })

        return results

    except Exception as e:
        print(f"Erreur recherche DuckDuckGo: {e}")
        return []

async def search_web_fallback(query: str, max_results: int = 5) -> list:
    """Recherche web avec fallback DuckDuckGo -> Actualités"""
    # Essayer DuckDuckGo d'abord
    results = await search_web_duckduckgo(query, max_results)

    if results:
        return results

    # Fallback : rechercher dans les actualités
    print("Fallback vers recherche d'actualités...")
    news_results = await search_news_rss(query, max_results)

    # Convertir le format actualités en format recherche
    web_results = []
    for article in news_results:
        web_results.append({
            'title': article.get('title'),
            'url': article.get('url'),
            'snippet': article.get('summary', '')[:200],
            'source': f"Actualités - {article.get('source')}"
        })

    return web_results

async def search_news_rss(topic: str, max_results: int = 5) -> list:
    """Recherche d'actualités via RSS"""
    try:
        # Sources RSS françaises populaires
        rss_sources = [
            f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}&hl=fr&gl=FR&ceid=FR:fr",
            "https://www.lemonde.fr/rss/une.xml",
            "https://www.franceinfo.fr/rss/",
            "https://www.20minutes.fr/rss/une.xml"
        ]

        all_articles = []

        for rss_url in rss_sources[:2]:  # Limiter à 2 sources pour la vitesse
            try:
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:max_results]:
                    article = {
                        'title': entry.get('title', 'Sans titre'),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', 'Source inconnue')
                    }
                    all_articles.append(article)

            except Exception as e:
                print(f"Erreur RSS {rss_url}: {e}")
                continue

        # Trier par date et limiter
        return all_articles[:max_results]

    except Exception as e:
        print(f"Erreur recherche actualités: {e}")
        return []

async def open_url_in_browser(url: str) -> bool:
    """Ouvre une URL dans une nouvelle fenêtre/onglet du navigateur"""
    try:
        # Utiliser webbrowser pour ouvrir dans une nouvelle fenêtre
        webbrowser.open_new_tab(url)
        print(f"🌐 URL ouverte dans le navigateur: {url}")
        return True
    except Exception as e:
        print(f"Erreur ouverture navigateur: {e}")
        return False

async def browse_with_playwright(url: str, action: str = "screenshot") -> dict:
    """Navigation avec Playwright pour screenshots et extraction"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
            )

            page = await browser.new_page()

            # Configurer le timeout
            timeout = int(os.getenv('BROWSER_TIMEOUT', '30000'))
            page.set_default_timeout(timeout)

            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            result = {'url': url, 'action': action}

            if action == "screenshot":
                screenshot = await page.screenshot(full_page=True)
                result['screenshot'] = base64.b64encode(screenshot).decode('utf-8')

            elif action == "extract_text":
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Supprimer les scripts et styles
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                # Nettoyer le texte
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)

                result['text'] = text[:2000]  # Limiter à 2000 caractères
                result['title'] = soup.title.string if soup.title else "Sans titre"

            await browser.close()
            return result

    except Exception as e:
        print(f"Erreur Playwright: {e}")
        return {'error': str(e), 'url': url}

# Fonction de compatibilité (ancien nom)
async def call_ai_with_fallback(prompt: str, system_prompt: str = "") -> tuple[str, str]:
    """Fonction de compatibilité - utilise le routage intelligent"""
    category = categorize_question(prompt)
    return await call_ai_with_smart_routing(prompt, system_prompt, category)

def categorize_question(prompt: str) -> str:
    """Catégorise la question pour adapter la réponse"""
    prompt_lower = prompt.lower()

    # Mots-clés pour chaque catégorie
    seduction_keywords = ["séduction", "draguer", "plaire", "charme", "attirance", "flirt", "rendez-vous", "date", "approche"]
    psychology_keywords = ["stress", "anxiété", "confiance", "estime", "peur", "timidité", "émotions", "mental", "psychologie"]
    sexology_keywords = ["sexe", "sexuel", "intimité", "plaisir", "libido", "désir", "relation intime", "sexualité"]
    friendship_keywords = ["ami", "conseil", "écoute", "soutien", "aide", "problème", "discussion"]

    # Compter les occurrences
    categories = {
        "seduction": sum(1 for keyword in seduction_keywords if keyword in prompt_lower),
        "psychology": sum(1 for keyword in psychology_keywords if keyword in prompt_lower),
        "sexology": sum(1 for keyword in sexology_keywords if keyword in prompt_lower),
        "friendship": sum(1 for keyword in friendship_keywords if keyword in prompt_lower)
    }

    # Retourner la catégorie dominante
    max_category = max(categories, key=categories.get)
    return max_category if categories[max_category] > 0 else "general"

def get_system_prompt(category: str) -> str:
    """Retourne le prompt système adapté à la catégorie"""
    base_personality = """Tu es Sophie, une IA bienveillante qui combine plusieurs expertises :
- Coach en séduction experte et moderne
- Psychologue empathique et professionnelle
- Sexologue ouverte et sans jugement
- Amie fidèle et de confiance

Tu réponds toujours avec empathie, respect et professionnalisme. Tes réponses sont concises (2-4 phrases), pratiques et adaptées à la situation."""

    category_prompts = {
        "seduction": f"""{base_personality}

FOCUS SÉDUCTION : Donne des conseils de séduction modernes, respectueux et authentiques. Encourage la confiance en soi et l'authenticité plutôt que la manipulation.""",

        "psychology": f"""{base_personality}

FOCUS PSYCHOLOGIE : Adopte une approche psychologique bienveillante. Aide à comprendre les émotions, développer la confiance en soi et gérer le stress relationnel.""",

        "sexology": f"""{base_personality}

FOCUS SEXOLOGIE : Réponds aux questions intimes avec professionnalisme et ouverture. Promeut une sexualité saine, consensuelle et épanouissante.""",

        "friendship": f"""{base_personality}

FOCUS AMITIÉ : Sois une amie attentive qui écoute, soutient et conseille avec bienveillance. Offre du réconfort et des perspectives positives.""",

        "general": f"""{base_personality}

APPROCHE GÉNÉRALE : Adapte ta réponse selon le contexte en puisant dans toutes tes expertises."""
    }

    return category_prompts.get(category, category_prompts["general"])

# Endpoints
@app.get("/")
async def root():
    return {
        "api": "MeetVoice TTS",
        "version": "2.0",
        "voice": "Denise",
        "questions": len(QUESTIONS)
    }

@app.get("/voices")
async def get_voices():
    """Liste des voix disponibles"""
    try:
        voices = await edge_tts.list_voices()

        # Filtrer les voix françaises
        french_voices = [
            {
                "name": voice["Name"],
                "short_name": voice["ShortName"],
                "gender": voice["Gender"],
                "locale": voice["Locale"]
            }
            for voice in voices
            if voice["Locale"].startswith("fr-")
        ]

        return {
            "voices": french_voices,
            "default_voice": VOICE,
            "total_voices": len(french_voices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        # Générer l'audio en bytes
        audio_bytes = await generate_tts_bytes(request.text, request.voice, request.rate, request.pitch)

        # Retourner en base64 pour compatibilité avec les autres endpoints
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        return {
            "text": request.text,
            "voice": request.voice,
            "audio": audio_b64,
            "format": "mp3",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/file")
async def text_to_speech_file(request: TTSRequest):
    """Version qui retourne un fichier MP3 directement"""
    try:
        audio_path = await generate_tts(request.text, request.voice, request.rate, request.pitch)
        return FileResponse(audio_path, media_type="audio/mpeg", filename="tts.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inscription/question/{question_number}")
async def get_question(question_number: int):
    if question_number < 1 or question_number > len(QUESTIONS):
        raise HTTPException(status_code=404, detail="Question non trouvée")
    
    question_text = QUESTIONS[question_number - 1]
    try:
        audio_path = await generate_tts(question_text)
        return FileResponse(audio_path, media_type="audio/mpeg", filename=f"q{question_number}.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inscription/info")
async def inscription_info():
    return {
        "total_questions": len(QUESTIONS),
        "voice": "Denise",
        "message": "Toutes les questions utilisent la même voix"
    }

@app.get("/inscription/question/genre/{genre}")
async def get_question_by_genre(genre: str):
    """Questions spécifiques selon le genre"""

    questions_genre = {
        "homme": [
            "Portez-vous une barbe, moustache, bouc ou autre pilosité faciale ?",
            "Quel est votre style de coiffure masculine préféré ?"
        ],
        "femme": [
            "Utilisez-vous du maquillage régulièrement ?",
            "Quelle est votre routine beauté ?"
        ],
        "autre": [
            "Comment préférez-vous exprimer votre style personnel ?",
            "Quels sont vos accessoires favoris ?"
        ]
    }

    if genre.lower() not in questions_genre:
        raise HTTPException(status_code=400, detail="Genre non reconnu. Utilisez: homme, femme, autre")

    # Pour l'exemple, on prend la première question du genre
    question_text = questions_genre[genre.lower()][0]

    try:
        audio_path = await generate_tts(question_text)
        return FileResponse(audio_path, media_type="audio/mpeg", filename=f"question_{genre}.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inscription/barbe")
async def get_question_barbe():
    """Question conditionnelle pour les hommes : barbe, moustache, etc."""
    question_text = "Une petite question spéciale pour vous, messieurs ! Portez-vous une barbe, une moustache, un bouc ou avez-vous un autre style de pilosité faciale ?"
    try:
        audio_path = await generate_tts(question_text)
        return FileResponse(audio_path, media_type="audio/mpeg", filename="question_barbe.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inscription/generate-all")
async def generate_all():
    try:
        generated = []
        for i, question in enumerate(QUESTIONS, 1):
            audio_path = await generate_tts(question)
            generated.append({
                "question": i,
                "text": question,
                "cached": os.path.exists(audio_path)
            })
        
        return {
            "success": True,
            "message": f"Toutes les {len(QUESTIONS)} questions générées",
            "voice": "Denise",
            "files": generated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia")
async def endpoint_ia(request: IARequest):
    """Endpoint IA complet : Coach séduction/psychologue/sexologue/amie avec vocal et écrit"""
    try:
        import time
        start_time = time.time()

        # 1. Catégoriser la question
        category = categorize_question(request.prompt)

        # 2. Obtenir le prompt système adapté
        system_prompt = get_system_prompt(category)

        result = {
            "prompt": request.prompt,
            "category": category,
            "prompt_audio": None,
            "response": None,
            "response_audio": None,
            "ai_provider": None,
            "processing_time": 0
        }

        # 3. Générer l'audio du prompt si demandé
        if request.include_prompt_audio:
            prompt_audio_bytes = await generate_tts_bytes(
                request.prompt,
                request.voice,
                request.rate,
                request.pitch
            )
            result["prompt_audio"] = base64.b64encode(prompt_audio_bytes).decode('utf-8')

        # 4. Appeler l'IA avec routage intelligent
        ia_response, ai_provider = await call_ai_with_smart_routing(request.prompt, system_prompt, category)
        result["response"] = ia_response
        result["ai_provider"] = ai_provider

        # 5. Générer l'audio de la réponse IA (toujours)
        response_audio_bytes = await generate_tts_bytes(
            ia_response,
            request.voice,
            request.rate,
            request.pitch
        )
        result["response_audio"] = base64.b64encode(response_audio_bytes).decode('utf-8')

        # 6. Calculer le temps de traitement
        result["processing_time"] = round(time.time() - start_time, 2)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/simple")
async def endpoint_ia_simple(request: IASimpleRequest):
    """Endpoint IA simplifié : réponse écrite seulement avec fallback"""
    try:
        # 1. Catégoriser la question
        category = categorize_question(request.prompt)

        # 2. Obtenir le prompt système adapté
        system_prompt = get_system_prompt(category)

        # 3. Appeler l'IA avec fallback
        ia_response, ai_provider = await call_ai_with_fallback(request.prompt, system_prompt)

        return {
            "prompt": request.prompt,
            "category": category,
            "response": ia_response,
            "ai_provider": ai_provider,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/routing-test")
async def test_ai_routing(request: IASimpleRequest):
    """Test du routage IA pour voir quelle IA serait choisie"""
    try:
        # Catégoriser la question
        category = categorize_question(request.prompt)

        # Déterminer le routage
        use_gemini_first = should_use_gemini(request.prompt, category)

        return {
            "prompt": request.prompt,
            "category": category,
            "recommended_ai": "google_gemini" if use_gemini_first else "deepinfra",
            "routing_explanation": {
                "use_gemini_first": use_gemini_first,
                "category_influence": f"Catégorie '{category}' influence le choix",
                "content_analysis": "Analyse du contenu de la question effectuée"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/image")
async def generate_image(request: ImageRequest):
    """Génère une image avec IA pour MeetVoice"""
    try:
        import time
        start_time = time.time()

        # Catégoriser pour optimiser le prompt
        category = categorize_question(request.prompt)

        # Optimiser le prompt pour MeetVoice
        optimized_prompt = optimize_image_prompt_for_meetvoice(request.prompt, category)

        # Générer l'image
        image_base64 = await generate_image_deepinfra(
            optimized_prompt,
            request.style,
            request.size
        )

        # Stocker temporairement l'image (sera supprimée après envoi)
        image_id = store_image_temporarily(image_base64)

        processing_time = round(time.time() - start_time, 2)

        # Récupérer et supprimer immédiatement l'image
        final_image = get_and_delete_image(image_id)

        return {
            "original_prompt": request.prompt,
            "optimized_prompt": optimized_prompt,
            "category": category,
            "style": request.style,
            "size": request.size,
            "image": final_image,
            "processing_time": processing_time,
            "status": "success",
            "cleanup_info": "Image automatiquement supprimée après envoi"
        }

    except Exception as e:
        return {
            "original_prompt": request.prompt,
            "error": str(e),
            "status": "error"
        }

@app.post("/ia/image-simple")
async def generate_image_simple(request: dict):
    """Génération d'image simplifiée"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt requis")

        # Paramètres par défaut
        image_request = ImageRequest(
            prompt=prompt,
            style=request.get("style", "realistic"),
            size=request.get("size", "1024x1024")
        )

        result = await generate_image(image_request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/web-search")
async def web_search(request: WebSearchRequest):
    """Recherche web avec ouverture automatique dans le navigateur"""
    try:
        import time
        start_time = time.time()

        # Rechercher sur le web avec fallback
        search_results = await search_web_fallback(request.query, request.max_results)

        processing_time = round(time.time() - start_time, 2)

        # Ouvrir automatiquement dans le navigateur si demandé
        browser_opened = False
        if request.open_browser and search_results:
            # Ouvrir le premier résultat
            first_result = search_results[0]
            browser_opened = await open_url_in_browser(first_result['url'])

        return {
            "query": request.query,
            "results_count": len(search_results),
            "results": search_results,
            "browser_opened": browser_opened,
            "processing_time": processing_time,
            "status": "success"
        }

    except Exception as e:
        return {
            "query": request.query,
            "error": str(e),
            "status": "error"
        }

@app.post("/ia/news")
async def get_news(request: NewsRequest):
    """Recherche d'actualités avec ouverture dans le navigateur"""
    try:
        import time
        start_time = time.time()

        # Rechercher les actualités
        news_results = await search_news_rss(request.topic, request.max_results)

        processing_time = round(time.time() - start_time, 2)

        # Ouvrir automatiquement dans le navigateur si demandé
        browser_opened = False
        if request.open_browser and news_results:
            # Ouvrir le premier article
            first_article = news_results[0]
            browser_opened = await open_url_in_browser(first_article['url'])

        return {
            "topic": request.topic,
            "category": request.category,
            "articles_count": len(news_results),
            "articles": news_results,
            "browser_opened": browser_opened,
            "processing_time": processing_time,
            "status": "success"
        }

    except Exception as e:
        return {
            "topic": request.topic,
            "error": str(e),
            "status": "error"
        }

@app.post("/ia/browse")
async def browse_url(request: BrowseRequest):
    """Navigation web avec ouverture automatique"""
    try:
        import time
        start_time = time.time()

        result = {"url": request.url, "action": request.action}

        # Ouvrir dans le navigateur si demandé
        browser_opened = False
        if request.open_browser:
            browser_opened = await open_url_in_browser(request.url)
            result["browser_opened"] = browser_opened

        # Actions supplémentaires avec Playwright
        if request.action in ["screenshot", "extract_text"]:
            playwright_result = await browse_with_playwright(request.url, request.action)
            result.update(playwright_result)

        processing_time = round(time.time() - start_time, 2)
        result["processing_time"] = processing_time
        result["status"] = "success"

        return result

    except Exception as e:
        return {
            "url": request.url,
            "error": str(e),
            "status": "error"
        }

@app.post("/description")
async def generate_profile_description(request: DescriptionRequest):
    """Génère une description de profil optimisée pour les sites de rencontre"""
    try:
        import time
        start_time = time.time()

        # Construire le prompt selon les informations utilisateur
        user_info = request.user_info
        style = request.style
        length = request.length

        # Extraire les informations clés (format MeetVoice)
        age = user_info.get('age', '')
        physique = user_info.get('physique', '')
        gouts = user_info.get('gouts', '')
        recherche = user_info.get('recherche', '')

        # Extraire les éléments VENDEURS (non-visibles)
        selling_points = extract_selling_points(physique, gouts)

        # Extraire aussi le format standard
        interests = user_info.get('interests', [])
        profession = user_info.get('profession', '')
        personality = user_info.get('personality', [])
        relationship_goals = user_info.get('relationship_goals', '')

        # Construire le prompt personnalisé et attractif
        prompt_parts = [
            f"Crée une description de profil {style} et TRÈS ATTRACTIVE pour un site de rencontre.",
            "IMPORTANT: Utilise les informations spécifiques fournies pour créer quelque chose d'UNIQUE et PERSONNEL.",
            "Évite les phrases génériques comme 'j'aime découvrir de nouvelles choses' ou 'rencontrer des gens intéressants'.",
        ]

        # Utiliser les données MeetVoice si disponibles
        if physique:
            prompt_parts.append(f"Physique et apparence: {physique}")

        if gouts:
            prompt_parts.append(f"Goûts et personnalité: {gouts}")

        if recherche:
            prompt_parts.append(f"Type de relation recherchée: {recherche}")

        # Sinon utiliser le format standard
        if age and not physique:
            prompt_parts.append(f"Âge: {age} ans")

        if interests and not gouts:
            interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)
            prompt_parts.append(f"Centres d'intérêt: {interests_str}")

        if profession and not physique:
            prompt_parts.append(f"Profession: {profession}")

        if personality and not gouts:
            personality_str = ", ".join(personality) if isinstance(personality, list) else str(personality)
            prompt_parts.append(f"Personnalité: {personality_str}")

        if relationship_goals and not recherche:
            prompt_parts.append(f"Recherche: {relationship_goals}")

        # Instructions spécifiques selon le style - AMÉLIORÉES
        style_instructions = {
            "attractif": "Crée un profil IRRÉSISTIBLE qui donne envie de matcher immédiatement. Mets en avant les atouts physiques, la personnalité charismatique et les éléments uniques qui le distinguent. Sois confiant et séduisant sans être arrogant. Utilise des détails spécifiques qui créent de l'attraction.",
            "drôle": "Crée un profil HILARANT qui fait sourire et donne envie de discuter. Utilise l'humour intelligent, l'autodérision charmante et des références amusantes. Évite le générique, sois créatif et original dans l'humour.",
            "mystérieux": "Crée un profil INTRIGUANT qui suscite la curiosité et l'envie d'en savoir plus. Utilise des éléments exotiques, des passions uniques et des formulations qui créent du mystère. Laisse des zones d'ombre fascinantes.",
            "sincère": "Crée un profil AUTHENTIQUE et touchant qui montre la vraie personnalité. Sois honnête mais attractif, utilise des détails personnels qui créent de la connexion émotionnelle."
        }

        prompt_parts.append(f"Instructions: {style_instructions.get(style, style_instructions['attractif'])}")

        # Instructions de longueur avec limite de 2000 caractères
        length_instructions = {
            "court": "Maximum 2-3 phrases courtes et percutantes (300-500 caractères).",
            "moyen": "Entre 4-6 phrases bien construites (500-1000 caractères).",
            "long": "Un paragraphe détaillé de 7-10 phrases (1000-1500 caractères)."
        }

        prompt_parts.append(f"Longueur: {length_instructions.get(length, length_instructions['moyen'])}")

        # Instructions finales pour maximiser l'attractivité
        prompt_parts.extend([
            "RÈGLES IMPORTANTES:",
            "- LIMITE ABSOLUE : Maximum 2000 caractères (très important !)",
            "- NE RÉPÈTE JAMAIS les informations physiques visibles (taille, poids, couleur yeux, cheveux) - c'est déjà dans le profil !",
            "- CONCENTRE-TOI sur les éléments INVISIBLES mais ATTRACTIFS : personnalité, passions, talents, expériences, valeurs",
            "- Utilise les détails UNIQUES : langues rares, origines, goûts musicaux spécifiques, traits de caractère",
            "- Évite absolument les phrases clichés comme 'j'aime découvrir', 'rencontrer des gens', 'nouvelles aventures'",
            "- Crée quelque chose d'UNIQUE qui se démarque et donne envie de matcher",
            "- Mets en avant la PERSONNALITÉ, les PASSIONS et ce qui rend cette personne SPÉCIALE",
            "- Écris à la première personne comme si c'était la personne qui parle",
            "- Écris directement la description finale sans introduction ni explication."
        ])

        full_prompt = " ".join(prompt_parts)

        # Appeler l'IA pour générer la description
        response, ai_provider = await call_ai_with_smart_routing(full_prompt, "", "seduction")

        # Vérifier et limiter à 2000 caractères
        if len(response) > 2000:
            # Tronquer intelligemment à la dernière phrase complète
            truncated = response[:2000]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')

            # Trouver la dernière ponctuation
            last_punct = max(last_period, last_exclamation, last_question)

            if last_punct > 1500:  # Si on a une phrase complète raisonnable
                response = truncated[:last_punct + 1]
            else:
                response = truncated[:2000]  # Sinon tronquer brutalement

        processing_time = round(time.time() - start_time, 2)

        return {
            "description": response,
            "character_count": len(response),
            "within_limit": len(response) <= 2000,
            "style": style,
            "length": length,
            "ai_provider": ai_provider,
            "user_info_used": bool(user_info),
            "processing_time": processing_time,
            "status": "success"
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@app.get("/ia/cache/status")
async def cache_status():
    """Statut du cache d'images"""
    import time
    current_time = time.time()

    cache_info = []
    total_size = 0

    for image_id, data in image_cache.items():
        age = current_time - data['timestamp']
        size = len(data['data'])
        total_size += size

        cache_info.append({
            "id": image_id[:8] + "...",  # ID tronqué pour sécurité
            "age_seconds": round(age, 1),
            "size_kb": round(size / 1024, 1)
        })

    return {
        "images_in_cache": len(image_cache),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "last_cleanup": round(current_time - last_cleanup, 1) if last_cleanup else "Jamais",
        "cache_details": cache_info[:5]  # Limiter à 5 pour éviter les gros retours
    }

@app.post("/ia/cache/cleanup")
async def force_cleanup():
    """Force le nettoyage du cache d'images"""
    old_count = len(image_cache)
    cleanup_old_images()
    new_count = len(image_cache)

    return {
        "message": "Nettoyage forcé effectué",
        "images_removed": old_count - new_count,
        "images_remaining": new_count
    }

@app.get("/ia/status")
async def ia_status():
    """Diagnostic du statut des clés API"""
    google_key = os.getenv('GOOGLE_API_KEY')
    deepinfra_key = os.getenv('DEEPINFRA_API_KEY')

    return {
        "google_gemini": {
            "configured": bool(google_key and google_key != "your_google_gemini_api_key_here"),
            "key_preview": f"{google_key[:10]}..." if google_key and len(google_key) > 10 else "Non configurée"
        },
        "deepinfra": {
            "configured": bool(deepinfra_key and deepinfra_key != "your_deepinfra_api_key_here"),
            "key_preview": f"{deepinfra_key[:10]}..." if deepinfra_key and len(deepinfra_key) > 10 else "Non configurée",
            "model": os.getenv('DEEPINFRA_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')
        },
        "fallback_mode": not (google_key and google_key != "your_google_gemini_api_key_here") and not (deepinfra_key and deepinfra_key != "your_deepinfra_api_key_here"),
        "env_file_loaded": os.path.exists('.env')
    }

@app.get("/cache/stats")
async def cache_stats():
    cache_files = [f for f in os.listdir("cache") if f.endswith(".mp3")] if os.path.exists("cache") else []
    total_size = sum(os.path.getsize(f"cache/{f}") for f in cache_files) if cache_files else 0

    return {
        "cache_files": len(cache_files),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "voice": "Denise"
    }

if __name__ == "__main__":
    import uvicorn
    # Configuration optimisée pour performance maximale
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        workers=4,              # Multi-processus pour performance
        loop="uvloop",          # Loop optimisé (si disponible)
        http="httptools",       # Parser HTTP rapide (si disponible)
        access_log=False,       # Désactiver logs d'accès pour performance
        reload=False            # Pas de reload en production
    )
