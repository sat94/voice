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


# Modèles
class TTSRequest(BaseModel):
    text: str
    voice: str = VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"

class IARequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es Sophie, coach de séduction experte et bienveillante. Réponds de manière concise et pratique."
    include_prompt_audio: bool = True
    voice: str = VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"

# Cache simple
def get_cache_path(text: str) -> str:
    cache_key = hashlib.md5(text.encode()).hexdigest()
    os.makedirs("cache", exist_ok=True)
    return f"cache/{cache_key}.mp3"

async def generate_tts(text: str, voice: str = VOICE, rate: str = "+0%", pitch: str = "+0Hz") -> str:
    cache_path = get_cache_path(text)
    if os.path.exists(cache_path):
        return cache_path

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(cache_path)
    return cache_path

async def generate_tts_bytes(text: str, voice: str = VOICE, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Génère TTS et retourne les bytes directement"""
    cache_path = await generate_tts(text, voice, rate, pitch)
    with open(cache_path, 'rb') as f:
        return f.read()

async def call_deepinfra(prompt: str, system_prompt: str = "") -> str:
    """Appel à l'API DeepInfra"""
    try:
        deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        deepinfra_model = os.getenv('DEEPINFRA_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')

        if not deepinfra_key:
            raise HTTPException(status_code=500, detail="DEEPINFRA_API_KEY non configurée")

        url = f"https://api.deepinfra.com/v1/inference/{deepinfra_model}"

        # Construction du prompt complet
        full_prompt = f"{system_prompt}\n\nUtilisateur: {prompt}\n\nSophie:"

        headers = {
            "Authorization": f"Bearer {deepinfra_key}",
            "Content-Type": "application/json"
        }

        data = {
            "input": {
                "prompt": full_prompt,
                "max_new_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        # Appel synchrone dans un thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, headers=headers, json=data, timeout=30)
        )

        response.raise_for_status()
        result = response.json()

        return result.get("output", {}).get("text", "Désolée, je n'ai pas pu générer de réponse.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur DeepInfra: {str(e)}")

# Endpoints
@app.get("/")
async def root():
    return {
        "api": "MeetVoice TTS",
        "version": "2.0",
        "voice": "Denise",
        "questions": len(QUESTIONS)
    }

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
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
    """Endpoint IA complet : prompt -> TTS -> DeepInfra -> réponse -> TTS"""
    try:
        result = {
            "prompt": request.prompt,
            "prompt_audio": None,
            "response": None,
            "response_audio": None,
            "processing_time": 0
        }

        import time
        start_time = time.time()

        # 1. Générer l'audio du prompt si demandé
        if request.include_prompt_audio:
            prompt_audio_bytes = await generate_tts_bytes(
                request.prompt,
                request.voice,
                request.rate,
                request.pitch
            )
            result["prompt_audio"] = base64.b64encode(prompt_audio_bytes).decode('utf-8')

        # 2. Appeler DeepInfra pour la réponse IA
        ia_response = await call_deepinfra(request.prompt, request.system_prompt)
        result["response"] = ia_response

        # 3. Générer l'audio de la réponse IA
        response_audio_bytes = await generate_tts_bytes(
            ia_response,
            request.voice,
            request.rate,
            request.pitch
        )
        result["response_audio"] = base64.b64encode(response_audio_bytes).decode('utf-8')

        # 4. Calculer le temps de traitement
        result["processing_time"] = round(time.time() - start_time, 2)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/simple")
async def endpoint_ia_simple(request: dict):
    """Endpoint IA simplifié pour tests rapides"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt requis")

        # Appel IA seulement
        system_prompt = "Tu es Sophie, coach de séduction experte. Réponds en 2-3 phrases maximum."
        ia_response = await call_deepinfra(prompt, system_prompt)

        return {
            "prompt": prompt,
            "response": ia_response,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
