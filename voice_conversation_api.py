#!/usr/bin/env python3
"""
API pour conversation vocale bidirectionnelle avec l'IA
Simulation d'appel téléphonique avec Speech-to-Text + IA + Text-to-Speech
"""

import asyncio
import json
import time
import base64
import io
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import speech_recognition as sr
import os
from dotenv import load_dotenv
from database import get_database_service
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeetVoice Conversation Vocale", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db_service = get_database_service()

class VoiceConversationManager:
    def __init__(self):
        self.active_calls: Dict[str, Dict] = {}
        self.recognizer = sr.Recognizer()
    
    async def start_call(self, websocket: WebSocket, user_id: str):
        """Démarre un appel vocal"""
        await websocket.accept()
        
        self.active_calls[user_id] = {
            "websocket": websocket,
            "start_time": time.time(),
            "conversation_history": [],
            "is_speaking": False,
            "is_listening": True
        }
        
        logger.info(f"📞 Appel démarré: {user_id}")
        
        # Message de bienvenue
        await self.send_message(user_id, {
            "type": "call_started",
            "message": "Bonjour ! Je suis Sophie, votre coach vocal. Comment allez-vous ?",
            "status": "listening"
        })
        
        # Générer et envoyer l'audio de bienvenue
        welcome_audio = await self.generate_welcome_audio()
        if welcome_audio:
            await self.send_audio(user_id, welcome_audio, "Bonjour ! Je suis Sophie, votre coach vocal. Comment allez-vous ?")
    
    def end_call(self, user_id: str):
        """Termine un appel"""
        if user_id in self.active_calls:
            call_duration = time.time() - self.active_calls[user_id]["start_time"]
            logger.info(f"📞 Appel terminé: {user_id} (durée: {call_duration:.1f}s)")
            del self.active_calls[user_id]
    
    async def send_message(self, user_id: str, message: dict):
        """Envoie un message WebSocket"""
        if user_id in self.active_calls:
            try:
                await self.active_calls[user_id]["websocket"].send_text(json.dumps(message))
                return True
            except:
                self.end_call(user_id)
                return False
        return False
    
    async def send_audio(self, user_id: str, audio_data: bytes, text: str):
        """Envoie l'audio de réponse"""
        await self.send_message(user_id, {
            "type": "ai_speaking",
            "audio": base64.b64encode(audio_data).decode(),
            "text": text,
            "status": "speaking"
        })
    
    async def process_voice_input(self, user_id: str, audio_data: bytes) -> str:
        """Convertit la voix en texte (Speech-to-Text)"""
        try:
            # Convertir les bytes audio en format compatible
            audio_file = io.BytesIO(audio_data)
            
            # Utiliser speech_recognition avec Google (gratuit)
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='fr-FR')
                
            logger.info(f"🎤 STT: {text}")
            return text
            
        except sr.UnknownValueError:
            return "Je n'ai pas bien compris, pouvez-vous répéter ?"
        except sr.RequestError as e:
            logger.error(f"Erreur STT: {e}")
            return "Désolée, j'ai un problème technique."
        except Exception as e:
            logger.error(f"Erreur traitement audio: {e}")
            return "Je n'ai pas pu traiter votre message vocal."
    
    async def generate_ai_response(self, user_input: str, user_id: str) -> Dict:
        """Génère la réponse IA"""
        try:
            # Utiliser votre système IA existant
            system_prompt = "Tu es Sophie, coach de séduction vocale. Réponds comme dans une conversation téléphonique naturelle, de manière concise et engageante."
            
            # Simuler l'appel IA (remplacez par votre vraie fonction)
            if "bonjour" in user_input.lower() or "salut" in user_input.lower():
                response = "Bonjour ! Je suis ravie de vous parler. Comment puis-je vous aider aujourd'hui dans votre développement personnel ?"
            elif "confiance" in user_input.lower():
                response = "La confiance en soi, c'est fondamental ! Dites-moi, dans quelles situations vous sentez-vous le moins à l'aise ?"
            elif "merci" in user_input.lower():
                response = "Je vous en prie ! C'est un plaisir de vous accompagner. Avez-vous d'autres questions ?"
            else:
                response = f"C'est intéressant ce que vous me dites. Pouvez-vous m'en dire plus sur '{user_input}' ?"
            
            return {
                "response": response,
                "provider": "conversation_ai",
                "processing_time": 0.8,
                "cost": 0.002
            }
            
        except Exception as e:
            logger.error(f"Erreur IA: {e}")
            return {
                "response": "Excusez-moi, j'ai eu un petit problème technique. Pouvez-vous répéter ?",
                "provider": "error",
                "processing_time": 0.1,
                "cost": 0.0
            }
    
    async def generate_tts_audio(self, text: str) -> bytes:
        """Génère l'audio TTS (utilise votre fonction existante)"""
        try:
            # Utiliser votre fonction TTS existante
            # Simulé ici, remplacez par votre vraie fonction generer_audio_tts()
            await asyncio.sleep(0.5)  # Simuler génération TTS
            return f"tts_audio_for_{text[:20]}".encode()
            
        except Exception as e:
            logger.error(f"Erreur TTS: {e}")
            return b""
    
    async def generate_welcome_audio(self) -> bytes:
        """Génère l'audio de bienvenue"""
        return await self.generate_tts_audio("Bonjour ! Je suis Sophie, votre coach vocal. Comment allez-vous ?")

voice_manager = VoiceConversationManager()

@app.websocket("/ws/voice-call/{user_id}")
async def voice_call_websocket(websocket: WebSocket, user_id: str):
    """WebSocket pour conversation vocale bidirectionnelle"""
    await voice_manager.start_call(websocket, user_id)
    
    try:
        while True:
            # Recevoir les données (peut être audio ou commandes)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "voice_input":
                # L'utilisateur a envoyé de l'audio
                audio_b64 = message.get("audio", "")
                if audio_b64:
                    try:
                        # Décoder l'audio
                        audio_data = base64.b64decode(audio_b64)
                        
                        # Indiquer qu'on traite
                        await voice_manager.send_message(user_id, {
                            "type": "processing",
                            "message": "Je vous écoute...",
                            "status": "processing"
                        })
                        
                        # Speech-to-Text
                        user_text = await voice_manager.process_voice_input(user_id, audio_data)
                        
                        # Générer réponse IA
                        ai_result = await voice_manager.generate_ai_response(user_text, user_id)
                        
                        # Générer audio de réponse
                        response_audio = await voice_manager.generate_tts_audio(ai_result["response"])
                        
                        # Envoyer la réponse complète
                        await voice_manager.send_message(user_id, {
                            "type": "conversation_turn",
                            "user_said": user_text,
                            "ai_response": ai_result["response"],
                            "audio": base64.b64encode(response_audio).decode() if response_audio else "",
                            "processing_time": ai_result["processing_time"],
                            "status": "completed"
                        })
                        
                        # Enregistrer la conversation
                        conversation_id = db_service.log_conversation(
                            prompt=user_text,
                            response=ai_result["response"],
                            provider=f"voice_call_{ai_result['provider']}",
                            processing_time=ai_result["processing_time"],
                            user_id=user_id,
                            system_prompt="Conversation vocale bidirectionnelle",
                            fallback_used=False,
                            cost=ai_result["cost"],
                            voice_settings={"mode": "bidirectional_call"},
                            audio_generated=True
                        )
                        
                        # Ajouter à l'historique
                        if user_id in voice_manager.active_calls:
                            voice_manager.active_calls[user_id]["conversation_history"].append({
                                "user": user_text,
                                "ai": ai_result["response"],
                                "timestamp": time.time(),
                                "conversation_id": conversation_id
                            })
                        
                    except Exception as e:
                        await voice_manager.send_message(user_id, {
                            "type": "error",
                            "message": f"Erreur traitement vocal: {str(e)}",
                            "status": "error"
                        })
            
            elif message_type == "end_call":
                # Terminer l'appel
                await voice_manager.send_message(user_id, {
                    "type": "call_ended",
                    "message": "Au revoir ! J'ai été ravie de vous parler.",
                    "status": "ended"
                })
                break
            
            elif message_type == "mute" or message_type == "unmute":
                # Gérer mute/unmute
                await voice_manager.send_message(user_id, {
                    "type": "status_change",
                    "status": message_type,
                    "message": f"Micro {'coupé' if message_type == 'mute' else 'activé'}"
                })
    
    except WebSocketDisconnect:
        voice_manager.end_call(user_id)
    except Exception as e:
        logger.error(f"Erreur appel vocal: {e}")
        voice_manager.end_call(user_id)

@app.get("/voice-call/stats")
async def voice_call_stats():
    """Statistiques des appels vocaux"""
    return {
        "active_calls": len(voice_manager.active_calls),
        "features": [
            "Speech-to-Text (Google)",
            "IA conversationnelle",
            "Text-to-Speech (Microsoft)",
            "Conversation bidirectionnelle",
            "Enregistrement automatique"
        ],
        "supported_languages": ["fr-FR"],
        "call_quality": "HD Voice",
        "latency": "~2-3s par échange"
    }

@app.get("/")
async def root():
    return {
        "api": "MeetVoice Conversation Vocale",
        "description": "Conversation téléphonique bidirectionnelle avec IA",
        "features": [
            "🎤 Speech-to-Text en temps réel",
            "🤖 IA conversationnelle",
            "🎵 Text-to-Speech premium",
            "📞 Simulation d'appel téléphonique",
            "💾 Enregistrement automatique"
        ],
        "endpoint": "/ws/voice-call/{user_id}",
        "demo": "Ouvrez voice_call_demo.html pour tester"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
