#!/usr/bin/env python3
# API IA Hybride : Gemini (principal) + DeepInfra (fallback)
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import asyncio
import base64
import os
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(title="MeetVoice IA Hybride", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Modèle unique
class IARequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es Sophie, coach de séduction experte et bienveillante. Réponds de manière concise et pratique."
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    include_audio: bool = True  # Audio par défaut

def is_gemini_censored(response_json):
    """Détecte si Gemini a censuré la réponse"""
    try:
        if 'candidates' not in response_json:
            return True  # Pas de candidats = problème
        
        if not response_json['candidates']:
            return True  # Liste vide = problème
        
        candidate = response_json['candidates'][0]
        
        # Vérifier le finishReason
        finish_reason = candidate.get('finishReason', '')
        if finish_reason in ['SAFETY', 'RECITATION', 'OTHER']:
            return True  # Censuré
        
        # Vérifier si il y a du contenu
        if 'content' not in candidate:
            return True  # Pas de contenu = censuré
        
        # Vérifier si le contenu est vide
        if not candidate['content'].get('parts'):
            return True  # Contenu vide = censuré
        
        return False  # Tout va bien
        
    except Exception:
        return True  # En cas d'erreur, considérer comme censuré

def extract_gemini_text(response_json):
    """Extrait le texte de la réponse Gemini"""
    try:
        return response_json['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return "Désolée, je n'ai pas pu générer de réponse."

async def call_gemini(prompt: str, system_prompt: str = "") -> dict:
    """Appel à l'API Gemini"""
    try:
        # Essayer les deux noms de variables
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
        print("🔄 Tentative avec Gemini...")
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

@app.get("/")
async def root():
    return {
        "api": "MeetVoice IA Hybride",
        "version": "3.0",
        "description": "UN SEUL ENDPOINT pour tout gérer",
        "endpoint": "/ia",
        "providers": ["gemini (gratuit)", "deepinfra (fallback)"],
        "features": ["texte", "audio par défaut", "fallback automatique", "changement de voix"]
    }

@app.post("/ia/simple")
async def endpoint_ia_simple(request: SimpleIARequest):
    """Endpoint IA hybride simplifié - texte seulement"""
    try:
        # Appel IA hybride
        system_prompt = "Tu es Sophie, coach de séduction experte. Réponds en 2-3 phrases maximum."
        ai_result = await call_ai_hybrid(request.prompt, system_prompt)
        
        return {
            "prompt": request.prompt,
            "response": ai_result["response"],
            "provider": ai_result["provider"],
            "cost": ai_result["cost"],
            "processing_time": ai_result["processing_time"],
            "fallback_used": ai_result["fallback_used"],
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia")
async def endpoint_ia_complet(request: IARequest):
    """Endpoint IA hybride complet avec audio"""
    try:
        start_time = time.time()
        
        # 1. Appel IA hybride
        ai_result = await call_ai_hybrid(request.prompt, request.system_prompt)
        
        # 2. Générer l'audio de la réponse IA
        response_audio_bytes = await generate_tts_audio(
            ai_result["response"],
            request.voice,
            request.rate,
            request.pitch
        )
        
        # 3. Temps total
        total_time = round(time.time() - start_time, 2)
        
        return {
            "prompt": request.prompt,
            "response": ai_result["response"],
            "response_audio": base64.b64encode(response_audio_bytes).decode('utf-8'),
            "provider": ai_result["provider"],
            "cost": ai_result["cost"],
            "processing_time": total_time,
            "ai_time": ai_result["processing_time"],
            "tts_time": round(total_time - ai_result["processing_time"], 2),
            "fallback_used": ai_result["fallback_used"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ia/test")
async def test_ia_hybride():
    """Test du système hybride"""
    tests = [
        "Quelle heure est-il ?",
        "Comment aborder une fille sur internet ?",
        "Comment faire l'amour passionnément ?"  # Test de censure
    ]
    
    results = []
    for prompt in tests:
        try:
            result = await call_ai_hybrid(prompt)
            results.append({
                "prompt": prompt,
                "provider": result["provider"],
                "fallback_used": result["fallback_used"],
                "status": "success"
            })
        except Exception as e:
            results.append({
                "prompt": prompt,
                "error": str(e),
                "status": "error"
            })
    
    return {"test_results": results}

@app.get("/ia/stats")
async def stats_ia():
    """Statistiques de l'IA hybride"""
    return {
        "gemini_configured": bool((os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GEMINI_API_KEY')) and (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GEMINI_API_KEY')) != "your_gemini_api_key_here"),
        "deepinfra_configured": bool(os.getenv('DEEPINFRA_API_KEY')),
        "tts_configured": bool(os.getenv('TTS_API_URL')),
        "estimated_costs": {
            "gemini": "Gratuit (15 req/min)",
            "deepinfra": "~0.001€ par requête",
            "tts": "Gratuit (votre API)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
