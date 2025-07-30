#!/usr/bin/env python3
"""
MeetVoice - Application Simple avec 30 Questions d'Inscription
API FastAPI ultra-simple pour les questions d'inscription avec synthèse vocale
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
import asyncio
import os
from groq import Groq
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Groq (ultra-rapide)
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY non trouvée dans le fichier .env")
groq_client = Groq(api_key=groq_api_key)

# Modèle de données pour la description
class UserProfile(BaseModel):
    prenom: str
    physique: str

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

# Voix française Denise
VOICE = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"

async def generate_audio(text: str) -> bytes:
    """Génère l'audio TTS avec Edge TTS"""
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        print(f"Erreur TTS: {e}")
        return b""

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
            "description": "POST /description"
        }
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

        print("🚀 Appel à Groq (ultra-rapide)...")

        # Appel à Groq avec Llama 3.1 8B
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Modèle rapide et disponible
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.8
        )

        print("✅ Réponse Groq reçue")

        description = response.choices[0].message.content.strip()

        return {
            "success": True,
            "description": description,
            "prompt_used": prompt,
            "prenom": profile.prenom
        }

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Erreur génération description: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🎵 MeetVoice Questions - Démarrage")
    print(f"📝 {len(QUESTIONS)} questions d'inscription disponibles")
    print("🌐 Serveur: http://localhost:8001")
    print("📚 Documentation: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
