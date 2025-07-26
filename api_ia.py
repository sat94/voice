#!/usr/bin/env python3
# API IA séparée pour tests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import asyncio
import base64
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(title="MeetVoice IA API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Modèles
class IARequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es Sophie, coach de séduction experte et bienveillante. Réponds de manière concise et pratique."
    voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
    rate: str = "+0%"
    pitch: str = "+0Hz"

class SimpleIARequest(BaseModel):
    prompt: str

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
        
        # Format correct pour DeepInfra
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
        raise HTTPException(status_code=500, detail=f"Erreur DeepInfra: {str(e)}")

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
        "api": "MeetVoice IA",
        "version": "1.0",
        "endpoints": ["/ia", "/ia/simple", "/ia/test"]
    }

@app.post("/ia/simple")
async def endpoint_ia_simple(request: SimpleIARequest):
    """Endpoint IA simplifié - texte seulement"""
    try:
        # Appel IA seulement
        system_prompt = "Tu es Sophie, coach de séduction experte. Réponds en 2-3 phrases maximum."
        ia_response = await call_deepinfra(request.prompt, system_prompt)
        
        return {
            "prompt": request.prompt,
            "response": ia_response,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia")
async def endpoint_ia_complet(request: IARequest):
    """Endpoint IA complet : prompt -> DeepInfra -> réponse + audio"""
    try:
        result = {
            "prompt": request.prompt,
            "response": None,
            "response_audio": None,
            "processing_time": 0
        }

        import time
        start_time = time.time()

        # 1. Appeler DeepInfra pour la réponse IA
        ia_response = await call_deepinfra(request.prompt, request.system_prompt)
        result["response"] = ia_response

        # 2. Générer l'audio de la réponse IA seulement
        response_audio_bytes = await generate_tts_audio(
            ia_response,
            request.voice,
            request.rate,
            request.pitch
        )
        result["response_audio"] = base64.b64encode(response_audio_bytes).decode('utf-8')

        # 3. Calculer le temps de traitement
        result["processing_time"] = round(time.time() - start_time, 2)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ia/test")
async def test_ia():
    """Test rapide de l'IA"""
    try:
        test_prompt = "Comment aborder une fille dans un café ?"
        response = await call_deepinfra(test_prompt)
        
        return {
            "test_prompt": test_prompt,
            "test_response": response,
            "status": "IA fonctionnelle"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "IA non fonctionnelle"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
