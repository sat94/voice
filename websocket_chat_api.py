#!/usr/bin/env python3
"""
API WebSocket pour Chat IA en temps réel
Système hybride : WebSocket + fallback REST
"""

import asyncio
import json
import time
import base64
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from database import get_database_service
import logging

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeetVoice WebSocket Chat", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Service de base de données
db_service = get_database_service()

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {
            "connected_at": time.time(),
            "messages_count": 0,
            "last_activity": time.time()
        }
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"User {user_id} disconnected")
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                self.user_sessions[user_id]["last_activity"] = time.time()
                return True
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False

manager = ConnectionManager()

# Modèles
class ChatMessage(BaseModel):
    prompt: str
    system_prompt: str = "Tu es Sophie, coach de séduction experte et bienveillante."
    user_id: str
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
    include_audio: bool = True
    stream: bool = True

# Fonctions IA (simulées - à remplacer par vos vraies fonctions)
async def stream_ai_response(prompt: str, system_prompt: str) -> str:
    """Simule le streaming d'une réponse IA"""
    # Dans la vraie implémentation, vous appelleriez Gemini/DeepInfra en streaming
    response = """Excellente question ! Pour améliorer ta confiance en toi, voici mes conseils :

1. **Travaille ta posture** : Tiens-toi droit, épaules en arrière. Une bonne posture projette naturellement de la confiance.

2. **Pratique le contact visuel** : Commence par des interactions courtes et augmente progressivement.

3. **Prépare des sujets de conversation** : Avoir quelques sujets en tête te donnera plus d'assurance.

4. **Commence petit** : Pratique d'abord avec des situations moins intimidantes.

L'important est de progresser à ton rythme. Chaque petite victoire renforce ta confiance !"""
    
    # Simuler le streaming mot par mot
    words = response.split()
    current_text = ""
    
    for i, word in enumerate(words):
        current_text += word + " "
        yield {
            "type": "text_chunk",
            "content": word + " ",
            "full_text": current_text.strip(),
            "is_complete": i == len(words) - 1
        }
        await asyncio.sleep(0.1)  # Simuler la latence de l'IA

async def generate_audio_chunk(text: str, voice: str) -> str:
    """Génère l'audio pour un chunk de texte"""
    # Simuler la génération audio
    await asyncio.sleep(0.5)
    return f"data:audio/mp3;base64,{base64.b64encode(b'fake_audio_data').decode()}"

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """Endpoint WebSocket principal pour le chat"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Recevoir le message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Valider le message
            try:
                chat_message = ChatMessage(**message_data)
            except Exception as e:
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": f"Format de message invalide: {str(e)}"
                })
                continue
            
            # Indiquer que le traitement commence
            await manager.send_message(user_id, {
                "type": "processing_start",
                "message": "Sophie réfléchit..."
            })
            
            # Variables pour l'enregistrement
            start_time = time.time()
            full_response = ""
            conversation_id = None
            
            try:
                # Streaming de la réponse IA
                async for chunk in stream_ai_response(chat_message.prompt, chat_message.system_prompt):
                    await manager.send_message(user_id, chunk)
                    
                    if chunk["is_complete"]:
                        full_response = chunk["full_text"]
                
                # Générer l'audio si demandé
                if chat_message.include_audio and full_response:
                    await manager.send_message(user_id, {
                        "type": "audio_generation_start",
                        "message": "Génération de l'audio..."
                    })
                    
                    # Générer l'audio par phrases pour un streaming plus fluide
                    sentences = full_response.split('. ')
                    audio_chunks = []
                    
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            audio_chunk = await generate_audio_chunk(sentence, chat_message.voice)
                            audio_chunks.append(audio_chunk)
                            
                            await manager.send_message(user_id, {
                                "type": "audio_chunk",
                                "audio": audio_chunk,
                                "sentence": sentence,
                                "chunk_index": i,
                                "total_chunks": len(sentences)
                            })
                
                # Enregistrer en base de données
                processing_time = time.time() - start_time
                conversation_id = db_service.log_conversation(
                    prompt=chat_message.prompt,
                    response=full_response,
                    provider="websocket_stream",
                    processing_time=processing_time,
                    user_id=chat_message.user_id,
                    system_prompt=chat_message.system_prompt,
                    fallback_used=False,
                    cost=0.002,
                    voice_settings={"voice": chat_message.voice},
                    audio_generated=chat_message.include_audio
                )
                
                # Envoyer la confirmation finale
                await manager.send_message(user_id, {
                    "type": "conversation_complete",
                    "conversation_id": conversation_id,
                    "processing_time": processing_time,
                    "message": "Conversation terminée avec succès"
                })
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement: {e}")
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": f"Erreur lors du traitement: {str(e)}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Erreur WebSocket pour {user_id}: {e}")
        manager.disconnect(user_id)

@app.post("/api/feedback")
async def add_feedback_rest(feedback_data: dict):
    """Endpoint REST pour ajouter un feedback (fallback)"""
    try:
        success = db_service.add_feedback(
            conversation_id=feedback_data.get("conversation_id"),
            rating=feedback_data.get("rating"),
            user_id=feedback_data.get("user_id"),
            category=feedback_data.get("category", "coaching"),
            comment=feedback_data.get("comment", ""),
            improvement_suggestion=feedback_data.get("improvement_suggestion", "")
        )
        
        return {"success": success, "message": "Feedback ajouté"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/connections")
async def get_connection_stats():
    """Statistiques des connexions WebSocket"""
    return {
        "active_connections": len(manager.active_connections),
        "sessions": {
            user_id: {
                "connected_duration": time.time() - session["connected_at"],
                "messages_count": session["messages_count"],
                "last_activity": session["last_activity"]
            }
            for user_id, session in manager.user_sessions.items()
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé"""
    return {
        "status": "OK",
        "websocket_connections": len(manager.active_connections),
        "database_connected": db_service.db_manager.test_connection()
    }

# Endpoint REST de fallback (pour compatibilité)
@app.post("/api/chat/fallback")
async def chat_fallback(message: ChatMessage):
    """Endpoint REST de fallback si WebSocket ne fonctionne pas"""
    try:
        start_time = time.time()
        
        # Générer la réponse complète (non-streaming)
        full_response = ""
        async for chunk in stream_ai_response(message.prompt, message.system_prompt):
            if chunk["is_complete"]:
                full_response = chunk["full_text"]
                break
        
        # Générer l'audio si demandé
        audio_data = None
        if message.include_audio:
            audio_data = await generate_audio_chunk(full_response, message.voice)
        
        # Enregistrer en base
        processing_time = time.time() - start_time
        conversation_id = db_service.log_conversation(
            prompt=message.prompt,
            response=full_response,
            provider="rest_fallback",
            processing_time=processing_time,
            user_id=message.user_id,
            system_prompt=message.system_prompt,
            fallback_used=True,
            cost=0.002,
            voice_settings={"voice": message.voice},
            audio_generated=message.include_audio
        )
        
        return {
            "conversation_id": conversation_id,
            "response": full_response,
            "audio": audio_data,
            "processing_time": processing_time,
            "method": "rest_fallback"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
