#!/usr/bin/env python3
# API IA Finale : UN SEUL ENDPOINT qui gère tout
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import requests
import asyncio
import base64
import os
import time
import json
from typing import Dict
from dotenv import load_dotenv
from database import get_database_service, db_manager
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeetVoice IA Coach", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Service de base de données
db_service = get_database_service()

# Gestionnaire de connexions WebSocket
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

# Modèles
class IARequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es Sophie, coach de séduction experte et bienveillante. Réponds de manière concise et pratique."
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    include_audio: bool = True  # Par défaut, inclure l'audio
    user_id: str = None  # Identifiant utilisateur optionnel

class FeedbackRequest(BaseModel):
    conversation_id: int
    rating: int  # 1-5
    comment: str = ""
    category: str = "general"
    improvement_suggestion: str = ""
    user_id: str = None

class DescriptionRequest(BaseModel):
    prenom: str = Field(..., description="Prénom de la personne")
    physique: str = Field(..., description="Description physique")
    gouts: str = Field(..., description="Goûts et centres d'intérêt")
    recherche: Literal["amical", "amoureuse", "libertin"] = Field(..., description="Type de relation recherchée")
    user_id: str = Field(default="anonymous", description="ID utilisateur")
    style_description: Literal["elegant", "decontracte", "seducteur", "authentique"] = Field(default="authentique")
    longueur: Literal["courte", "moyenne", "longue"] = Field(default="moyenne")

def is_gemini_censored(response_json):
    """Détecte si Gemini a censuré la réponse"""
    try:
        if 'candidates' not in response_json or not response_json['candidates']:
            return True
        
        candidate = response_json['candidates'][0]
        
        # Vérifier le finishReason
        finish_reason = candidate.get('finishReason', '')
        if finish_reason in ['SAFETY', 'RECITATION', 'OTHER']:
            return True
        
        # Vérifier si il y a du contenu
        if 'content' not in candidate or not candidate['content'].get('parts'):
            return True
        
        return False
        
    except Exception:
        return True

def extract_gemini_text(response_json):
    """Extrait le texte de la réponse Gemini"""
    try:
        return response_json['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return "Désolée, je n'ai pas pu générer de réponse."

async def call_gemini(prompt: str, system_prompt: str = "") -> dict:
    """Appel à l'API Gemini"""
    try:
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GEMINI_API_KEY')
        
        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            raise Exception("GEMINI_API_KEY non configurée")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        
        # Construction du prompt complet
        full_prompt = f"{system_prompt}\n\nUtilisateur: {prompt}\n\nSophie:"
        
        data = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 300
            }
        }
        
        # Appel synchrone dans un thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, json=data, timeout=15)
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        raise Exception(f"Erreur Gemini: {str(e)}")

async def call_deepinfra(prompt: str, system_prompt: str = "") -> str:
    """Appel à l'API DeepInfra (fallback)"""
    try:
        deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        deepinfra_model = os.getenv('DEEPINFRA_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')
        
        if not deepinfra_key:
            raise Exception("DEEPINFRA_API_KEY non configurée")
        
        url = f"https://api.deepinfra.com/v1/inference/{deepinfra_model}"
        
        # Construction du prompt complet
        full_prompt = f"{system_prompt}\n\nUtilisateur: {prompt}\n\nSophie:"
        
        headers = {
            "Authorization": f"Bearer {deepinfra_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "input": full_prompt,
            "max_new_tokens": 800,
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
        
        # Extraire la réponse selon le format DeepInfra
        if "results" in result and len(result["results"]) > 0:
            return result["results"][0]["generated_text"]
        elif "output" in result:
            return result["output"]
        else:
            return "Désolée, je n'ai pas pu générer de réponse."
        
    except Exception as e:
        raise Exception(f"Erreur DeepInfra: {str(e)}")

async def call_ai_hybrid(prompt: str, system_prompt: str = "") -> dict:
    """Appel IA hybride : Gemini d'abord, puis DeepInfra si censuré"""
    
    start_time = time.time()
    
    try:
        # 1. Essayer Gemini d'abord (gratuit + rapide)
        print(f"🔄 Tentative avec Gemini pour: {prompt[:50]}...")
        gemini_response = await call_gemini(prompt, system_prompt)
        
        # 2. Vérifier si censuré
        if not is_gemini_censored(gemini_response):
            response_text = extract_gemini_text(gemini_response)
            processing_time = round(time.time() - start_time, 2)
            
            print(f"✅ Gemini a répondu en {processing_time}s")
            return {
                "response": response_text,
                "provider": "gemini",
                "cost": 0.0,
                "processing_time": processing_time,
                "fallback_used": False
            }
        
        # 3. Si censuré, utiliser DeepInfra
        print("⚠️ Gemini censuré, fallback vers DeepInfra...")
        deepinfra_response = await call_deepinfra(prompt, system_prompt)
        processing_time = round(time.time() - start_time, 2)
        
        print(f"✅ DeepInfra a répondu en {processing_time}s")
        return {
            "response": deepinfra_response,
            "provider": "deepinfra", 
            "cost": 0.001,
            "processing_time": processing_time,
            "fallback_used": True
        }
        
    except Exception as gemini_error:
        # 4. En cas d'erreur Gemini, fallback vers DeepInfra
        print(f"❌ Erreur Gemini: {gemini_error}")
        print("🔄 Fallback vers DeepInfra...")
        
        try:
            deepinfra_response = await call_deepinfra(prompt, system_prompt)
            processing_time = round(time.time() - start_time, 2)
            
            print(f"✅ DeepInfra a répondu en {processing_time}s")
            return {
                "response": deepinfra_response,
                "provider": "deepinfra",
                "cost": 0.001,
                "processing_time": processing_time,
                "fallback_used": True
            }
        except Exception as deepinfra_error:
            raise HTTPException(
                status_code=500, 
                detail=f"Erreur Gemini: {gemini_error} | Erreur DeepInfra: {deepinfra_error}"
            )

async def generate_tts_audio(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Génère l'audio TTS via l'API existante"""
    try:
        tts_url = os.getenv('TTS_API_URL', 'https://aaaazealmmmma.duckdns.org/tts')
        
        data = {
            "text": text,
            "voice": voice,
            "rate": rate,
            "pitch": pitch
        }
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(tts_url, json=data, timeout=30)
        )
        
        response.raise_for_status()
        return response.content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

async def stream_ai_response(prompt: str, system_prompt: str):
    """Génère une réponse IA en streaming mot par mot"""
    try:
        # Appeler l'IA hybride normalement
        ai_result = await call_ai_hybrid(prompt, system_prompt)
        response_text = ai_result["response"]

        # Simuler le streaming en découpant la réponse
        words = response_text.split()
        current_text = ""

        for i, word in enumerate(words):
            current_text += word + " "
            yield {
                "type": "text_chunk",
                "content": word + " ",
                "full_text": current_text.strip(),
                "is_complete": i == len(words) - 1,
                "word_index": i,
                "total_words": len(words),
                "provider": ai_result["provider"],
                "fallback_used": ai_result["fallback_used"]
            }
            await asyncio.sleep(0.08)  # Délai pour simuler le streaming

        # Retourner les métadonnées finales
        yield {
            "type": "metadata",
            "provider": ai_result["provider"],
            "cost": ai_result["cost"],
            "processing_time": ai_result["processing_time"],
            "fallback_used": ai_result["fallback_used"],
            "is_complete": True
        }

    except Exception as e:
        yield {
            "type": "error",
            "message": str(e),
            "is_complete": True
        }

def generer_description_attractive(personne: DescriptionRequest) -> dict:
    """Génère une description attractive pour profil de rencontre"""

    # Templates par type de recherche
    templates = {
        "amical": {
            "intro": "Salut ! Je suis {prenom}, une personne {trait} qui adore {activite}.",
            "corps": "Physiquement, je suis {physique_reformule}. Ce qui me passionne : {gouts_reformules}.",
            "conclusion": "Si tu cherches quelqu'un avec qui partager de bons moments, n'hésite pas !"
        },
        "amoureuse": {
            "intro": "Je suis {prenom}, et je crois encore aux belles rencontres.",
            "corps": "Physiquement, {physique_reformule}. J'adore {gouts_reformules} et je rêve de partager ces moments avec quelqu'un de spécial.",
            "conclusion": "Je recherche quelqu'un avec qui construire de beaux projets et partager les petits bonheurs du quotidien."
        },
        "libertin": {
            "intro": "Salut, je suis {prenom}, {trait_sensuel} qui assume pleinement sa sensualité.",
            "corps": "Physiquement, {physique_reformule}. J'aime {gouts_reformules} et je cultive l'art de vivre pleinement.",
            "conclusion": "Je cherche des personnes ouvertes pour des moments complices et sans prise de tête."
        }
    }

    # Reformulations
    def reformuler_physique(physique: str) -> str:
        reformulations = {
            "grand": "élancé(e)", "petit": "de taille harmonieuse", "mince": "svelte",
            "sportif": "athlétique", "ronde": "aux courbes généreuses",
            "brun": "aux cheveux châtains", "blond": "aux cheveux dorés",
            "yeux bleus": "au regard azur", "yeux verts": "au regard émeraude"
        }
        physique_lower = physique.lower()
        for mot, reformulation in reformulations.items():
            if mot in physique_lower:
                physique = physique.replace(mot, reformulation)
        return physique if physique else "avec un charme naturel"

    def reformuler_gouts(gouts: str) -> str:
        reformulations = {
            "sport": "l'activité physique", "lecture": "les bons livres",
            "cinema": "le 7ème art", "musique": "l'univers musical",
            "voyage": "la découverte de nouveaux horizons", "cuisine": "l'art culinaire"
        }
        gouts_lower = gouts.lower()
        for mot, reformulation in reformulations.items():
            if mot in gouts_lower:
                gouts = gouts.replace(mot, reformulation)
        return gouts

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

    # Construire la description selon la longueur
    if personne.longueur == "courte":
        description = template["intro"].format(**variables)
    elif personne.longueur == "longue":
        description = f"{template['intro'].format(**variables)} {template['corps'].format(**variables)} {template['conclusion'].format(**variables)}"
    else:  # moyenne
        description = f"{template['intro'].format(**variables)} {template['corps'].format(**variables)}"

    # Calculer le score d'attractivité
    score = 50
    if len(personne.physique) > 30: score += 20
    if len(personne.gouts) > 40: score += 20
    if len(description) > 100: score += 10

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

@app.get("/")
async def root():
    return {
        "api": "MeetVoice IA Coach",
        "version": "3.0",
        "description": "UN SEUL ENDPOINT pour tout gérer",
        "endpoint": "/ia",
        "providers": ["gemini (gratuit)", "deepinfra (fallback)"],
        "features": ["texte", "audio", "fallback automatique"]
    }

@app.post("/ia")
async def endpoint_ia_unifie(request: IARequest):
    """ENDPOINT UNIQUE qui gère tout : texte + audio optionnel + fallback automatique"""
    try:
        start_time = time.time()
        
        # 1. Appel IA hybride (Gemini → DeepInfra si nécessaire)
        ai_result = await call_ai_hybrid(request.prompt, request.system_prompt)
        
        result = {
            "prompt": request.prompt,
            "response": ai_result["response"],
            "provider": ai_result["provider"],
            "cost": ai_result["cost"],
            "fallback_used": ai_result["fallback_used"],
            "ai_time": ai_result["processing_time"]
        }
        
        # 2. Générer l'audio si demandé
        if request.include_audio:
            print("🎤 Génération audio...")
            response_audio_bytes = await generate_tts_audio(
                ai_result["response"],
                request.voice,
                request.rate,
                request.pitch
            )
            result["response_audio"] = base64.b64encode(response_audio_bytes).decode('utf-8')
            result["audio_size"] = len(response_audio_bytes)
        else:
            result["response_audio"] = None
            result["audio_size"] = 0
        
        # 3. Temps total
        result["total_time"] = round(time.time() - start_time, 2)
        result["tts_time"] = round(result["total_time"] - ai_result["processing_time"], 2) if request.include_audio else 0

        # 4. Enregistrer en base de données
        try:
            conversation_id = db_service.log_conversation(
                prompt=request.prompt,
                response=ai_result["response"],
                provider=ai_result["provider"],
                processing_time=result["total_time"],
                user_id=request.user_id,
                system_prompt=request.system_prompt,
                fallback_used=ai_result["fallback_used"],
                cost=ai_result["cost"],
                voice_settings={
                    "voice": request.voice,
                    "rate": request.rate,
                    "pitch": request.pitch
                },
                audio_generated=request.include_audio
            )
            result["conversation_id"] = conversation_id
            logger.info(f"Conversation enregistrée avec ID: {conversation_id}")
        except Exception as e:
            logger.error(f"Erreur enregistrement BDD: {e}")
            result["conversation_id"] = None

        print(f"✅ Réponse complète générée en {result['total_time']}s")

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """🚀 NOUVEAU: Endpoint WebSocket pour chat en temps réel"""
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Recevoir le message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Valider les données
            prompt = message_data.get("prompt", "")
            system_prompt = message_data.get("system_prompt", "Tu es Sophie, coach de séduction experte et bienveillante.")
            include_audio = message_data.get("include_audio", True)
            voice = message_data.get("voice", "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)")
            rate = message_data.get("rate", "+0%")
            pitch = message_data.get("pitch", "+0Hz")

            if not prompt:
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": "Prompt requis"
                })
                continue

            # Indiquer le début du traitement
            await manager.send_message(user_id, {
                "type": "processing_start",
                "message": "Sophie réfléchit..."
            })

            start_time = time.time()
            full_response = ""
            ai_metadata = {}

            try:
                # 🔄 Streaming de la réponse IA
                async for chunk in stream_ai_response(prompt, system_prompt):
                    await manager.send_message(user_id, chunk)

                    if chunk["type"] == "text_chunk" and chunk["is_complete"]:
                        full_response = chunk["full_text"]
                    elif chunk["type"] == "metadata":
                        ai_metadata = chunk

                # 🎵 Générer l'audio si demandé
                if include_audio and full_response:
                    await manager.send_message(user_id, {
                        "type": "audio_generation_start",
                        "message": "Génération de l'audio..."
                    })

                    try:
                        audio_data = await generate_tts_audio(full_response, voice, rate, pitch)
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                        await manager.send_message(user_id, {
                            "type": "audio_complete",
                            "audio": f"data:audio/mp3;base64,{audio_base64}",
                            "message": "Audio généré avec succès"
                        })
                    except Exception as audio_error:
                        await manager.send_message(user_id, {
                            "type": "audio_error",
                            "message": f"Erreur audio: {str(audio_error)}"
                        })

                # 💾 Enregistrer en base de données
                total_time = time.time() - start_time
                try:
                    conversation_id = db_service.log_conversation(
                        prompt=prompt,
                        response=full_response,
                        provider=ai_metadata.get("provider", "websocket"),
                        processing_time=total_time,
                        user_id=user_id,
                        system_prompt=system_prompt,
                        fallback_used=ai_metadata.get("fallback_used", False),
                        cost=ai_metadata.get("cost", 0.0),
                        voice_settings={"voice": voice, "rate": rate, "pitch": pitch},
                        audio_generated=include_audio
                    )

                    # Envoyer la confirmation finale
                    await manager.send_message(user_id, {
                        "type": "conversation_complete",
                        "conversation_id": conversation_id,
                        "total_time": total_time,
                        "provider": ai_metadata.get("provider"),
                        "cost": ai_metadata.get("cost", 0.0),
                        "message": "✅ Conversation terminée avec succès"
                    })

                except Exception as db_error:
                    await manager.send_message(user_id, {
                        "type": "database_error",
                        "message": f"Erreur BDD: {str(db_error)}"
                    })

            except Exception as e:
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": f"Erreur: {str(e)}"
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Erreur WebSocket {user_id}: {e}")
        manager.disconnect(user_id)

@app.get("/ia/stats")
async def stats():
    """Statistiques de l'API"""
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GEMINI_API_KEY')
    
    return {
        "api": "MeetVoice IA Coach v3.0",
        "endpoint": "/ia",
        "configuration": {
            "gemini": bool(gemini_key and gemini_key != "your_gemini_api_key_here"),
            "deepinfra": bool(os.getenv('DEEPINFRA_API_KEY')),
            "tts": bool(os.getenv('TTS_API_URL'))
        },
        "features": {
            "hybrid_ai": "Gemini (gratuit) → DeepInfra (fallback)",
            "audio_generation": "TTS intégré",
            "voice_selection": "Changement de voix supporté",
            "automatic_fallback": "Transparent pour l'utilisateur"
        },
        "costs": {
            "gemini": "Gratuit (15 req/min)",
            "deepinfra": "~0.001€ par requête",
            "tts": "Gratuit (votre API)"
        }
    }

@app.post("/feedback")
async def add_feedback(feedback: FeedbackRequest):
    """Ajouter un feedback utilisateur"""
    try:
        success = db_service.add_feedback(
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            user_id=feedback.user_id,
            category=feedback.category,
            comment=feedback.comment,
            improvement_suggestion=feedback.improvement_suggestion
        )

        if success:
            return {
                "success": True,
                "message": "Feedback enregistré avec succès",
                "conversation_id": feedback.conversation_id
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur enregistrement feedback")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/description")
async def generer_description(personne: DescriptionRequest):
    """🎯 Génère une description attractive pour profil de rencontre"""
    try:
        start_time = time.time()

        logger.info(f"🎯 Génération description pour {personne.prenom} (recherche: {personne.recherche})")

        # Générer la description
        result = generer_description_attractive(personne)

        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        result["provider"] = "description_generator"

        # Enregistrer en base de données
        try:
            conversation_id = db_service.log_conversation(
                prompt=f"Description de {personne.prenom}: {personne.physique} | {personne.gouts}",
                response=result["description"],
                provider="description_generator",
                processing_time=processing_time,
                user_id=personne.user_id,
                system_prompt=f"Génération description {personne.recherche}",
                fallback_used=False,
                cost=0.001,
                voice_settings={"type": "description", "recherche": personne.recherche},
                audio_generated=False
            )
            result["conversation_id"] = conversation_id
            logger.info(f"✅ Description enregistrée: conversation_id={conversation_id}")
        except Exception as db_error:
            logger.warning(f"⚠️ Erreur enregistrement BDD: {db_error}")

        return result

    except Exception as e:
        logger.error(f"❌ Erreur génération description: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/user/{user_id}")
async def get_user_stats(user_id: str):
    """Statistiques d'un utilisateur"""
    try:
        stats = db_service.get_user_stats(user_id)
        return {
            "user_id": user_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/system")
async def get_system_stats():
    """Statistiques système globales"""
    try:
        stats = db_service.get_system_stats()
        return {
            "system_stats": stats,
            "database_connected": db_manager.test_connection()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/database")
async def database_health():
    """Vérification de la santé de la base de données"""
    try:
        is_connected = db_manager.test_connection()
        return {
            "database_connected": is_connected,
            "database_url": os.getenv('DATABASE_URL', '').split('@')[1] if '@' in os.getenv('DATABASE_URL', '') else 'Non configurée',
            "status": "OK" if is_connected else "ERROR"
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "status": "ERROR"
        }

@app.get("/ws/stats")
async def websocket_stats():
    """📊 Statistiques des connexions WebSocket"""
    return {
        "websocket_connections": {
            "active_count": len(manager.active_connections),
            "connected_users": list(manager.active_connections.keys())
        },
        "api_mode": "HYBRIDE",
        "endpoints": {
            "rest": "POST /ia (compatible existant)",
            "websocket": "WS /ws/chat/{user_id} (nouveau streaming)",
            "fallback": "Automatique REST si WebSocket échoue"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
