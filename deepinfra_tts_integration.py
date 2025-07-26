#!/usr/bin/env python3
"""
Intégration des modèles TTS de DeepInfra
Modèles vocaux directs pour génération audio optimisée
"""

import requests
import asyncio
import base64
import json
import time
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class DeepInfraTTS:
    def __init__(self):
        self.api_key = os.getenv('DEEPINFRA_API_KEY')
        self.base_url = "https://api.deepinfra.com/v1/inference"
        
        # Modèles TTS disponibles sur DeepInfra
        self.available_models = {
            "kokoro": {
                "model_id": "hexgrad/Kokoro-82M",
                "description": "Modèle TTS léger 82M paramètres, qualité élevée",
                "voices": [
                    "af_bella", "af_nicole", "af_sarah", "af_sky",
                    "am_adam", "am_michael", "bf_emma", "bf_isabella",
                    "bm_george", "bm_lewis"
                ],
                "languages": ["en", "fr", "es", "de", "it"],
                "speed_range": [0.5, 2.0],
                "quality": "high"
            },
            "orpheus": {
                "model_id": "orpheus-tts",  # À vérifier
                "description": "Speech-LLM basé sur Llama, génération empathique",
                "voices": ["default", "empathetic", "professional"],
                "languages": ["en", "fr"],
                "speed_range": [0.8, 1.5],
                "quality": "premium"
            }
        }
    
    async def list_available_models(self) -> Dict:
        """Liste tous les modèles TTS disponibles"""
        return {
            "deepinfra_tts_models": self.available_models,
            "recommended": "kokoro",
            "total_models": len(self.available_models)
        }
    
    async def generate_audio_kokoro(self, text: str, voice: str = "af_bella", speed: float = 1.0) -> bytes:
        """Génère l'audio avec le modèle Kokoro-82M"""
        try:
            url = f"{self.base_url}/hexgrad/Kokoro-82M"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "preset_voice": [voice],  # Corrigé: preset_voice est un array
                "speed": speed,
                "output_format": "mp3"
            }
            
            logger.info(f"🎵 Génération Kokoro TTS: {text[:50]}... (voix: {voice})")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                # Debug: voir la vraie réponse
                result = response.json()
                logger.info(f"🔍 Réponse Kokoro: {list(result.keys())}")

                if 'audio' in result and result['audio']:
                    # L'audio est déjà en bytes ou base64 encodé
                    if isinstance(result['audio'], str):
                        # Corriger le padding base64 si nécessaire
                        audio_b64 = result['audio']
                        # Ajouter le padding manquant
                        missing_padding = len(audio_b64) % 4
                        if missing_padding:
                            audio_b64 += '=' * (4 - missing_padding)
                        return base64.b64decode(audio_b64)
                    else:
                        return result['audio']
                else:
                    logger.warning(f"Pas d'audio dans la réponse Kokoro: {result}")
                    return b""
            else:
                logger.error(f"Erreur Kokoro TTS: {response.status_code} - {response.text}")
                return b""
                
        except Exception as e:
            logger.error(f"Erreur génération Kokoro: {e}")
            return b""
    
    async def generate_audio_orpheus(self, text: str, voice: str = "empathetic", speed: float = 1.0) -> bytes:
        """Génère l'audio avec le modèle Orpheus TTS"""
        try:
            # URL à ajuster selon la vraie API Orpheus
            url = f"{self.base_url}/orpheus-tts"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "voice_style": voice,
                "speed": speed,
                "format": "mp3"
            }
            
            logger.info(f"🎵 Génération Orpheus TTS: {text[:50]}... (style: {voice})")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Erreur Orpheus TTS: {response.status_code} - {response.text}")
                return b""
                
        except Exception as e:
            logger.error(f"Erreur génération Orpheus: {e}")
            return b""
    
    async def generate_audio_optimized(self, text: str, model: str = "kokoro", **kwargs) -> Dict:
        """Génère l'audio avec le modèle optimal"""
        start_time = time.time()
        
        try:
            if model == "kokoro":
                audio_data = await self.generate_audio_kokoro(
                    text, 
                    voice=kwargs.get('voice', 'af_bella'),
                    speed=kwargs.get('speed', 1.0)
                )
            elif model == "orpheus":
                audio_data = await self.generate_audio_orpheus(
                    text,
                    voice=kwargs.get('voice', 'empathetic'),
                    speed=kwargs.get('speed', 1.0)
                )
            else:
                raise ValueError(f"Modèle non supporté: {model}")
            
            processing_time = time.time() - start_time
            
            return {
                "success": len(audio_data) > 0,
                "audio_data": audio_data,
                "model_used": model,
                "processing_time": processing_time,
                "audio_size": len(audio_data),
                "text_length": len(text),
                "cost_estimate": self.estimate_cost(len(text), model)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": model,
                "processing_time": time.time() - start_time
            }
    
    def estimate_cost(self, text_length: int, model: str) -> float:
        """Estime le coût de génération"""
        # Coûts estimés (à ajuster selon les vrais tarifs DeepInfra)
        cost_per_char = {
            "kokoro": 0.00001,  # Très économique
            "orpheus": 0.00003  # Plus cher mais meilleure qualité
        }
        
        return text_length * cost_per_char.get(model, 0.00002)
    
    async def test_all_models(self, test_text: str = "Bonjour, ceci est un test de synthèse vocale.") -> Dict:
        """Teste tous les modèles disponibles"""
        results = {}
        
        for model_name in self.available_models.keys():
            logger.info(f"🧪 Test du modèle: {model_name}")
            
            result = await self.generate_audio_optimized(
                test_text, 
                model=model_name
            )
            
            results[model_name] = {
                "success": result["success"],
                "processing_time": result["processing_time"],
                "audio_size": result.get("audio_size", 0),
                "cost_estimate": result.get("cost_estimate", 0),
                "error": result.get("error")
            }
            
            # Délai entre les tests
            await asyncio.sleep(1)
        
        return {
            "test_text": test_text,
            "results": results,
            "recommendation": self.get_best_model(results)
        }
    
    def get_best_model(self, test_results: Dict) -> str:
        """Détermine le meilleur modèle basé sur les tests"""
        successful_models = {
            name: data for name, data in test_results.items() 
            if data["success"]
        }
        
        if not successful_models:
            return "aucun"
        
        # Critères: vitesse + qualité + coût
        best_model = min(successful_models.keys(), 
                        key=lambda x: successful_models[x]["processing_time"])
        
        return best_model

# Instance globale
deepinfra_tts = DeepInfraTTS()

async def main():
    """Test des modèles TTS DeepInfra"""
    print("🎵 TEST DES MODÈLES TTS DEEPINFRA")
    print("=" * 50)
    
    # Lister les modèles
    models = await deepinfra_tts.list_available_models()
    print(f"📋 Modèles disponibles: {list(models['deepinfra_tts_models'].keys())}")
    
    # Tester tous les modèles
    test_results = await deepinfra_tts.test_all_models(
        "Bonjour ! Je suis Sophie, votre coach de séduction. Comment puis-je vous aider aujourd'hui ?"
    )
    
    print("\n📊 RÉSULTATS DES TESTS:")
    for model, result in test_results["results"].items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {model}:")
        print(f"   Temps: {result['processing_time']:.2f}s")
        print(f"   Taille audio: {result['audio_size']} bytes")
        print(f"   Coût estimé: {result['cost_estimate']:.6f}€")
        if result.get("error"):
            print(f"   Erreur: {result['error']}")
    
    print(f"\n🏆 Modèle recommandé: {test_results['recommendation']}")
    
    # Test de génération optimisée
    if test_results['recommendation'] != "aucun":
        print(f"\n🎯 Test génération optimisée avec {test_results['recommendation']}...")
        
        result = await deepinfra_tts.generate_audio_optimized(
            "Excellente question ! Voici mes conseils pour améliorer votre confiance en vous.",
            model=test_results['recommendation'],
            voice="af_bella",
            speed=1.1
        )
        
        if result["success"]:
            print(f"✅ Génération réussie:")
            print(f"   Modèle: {result['model_used']}")
            print(f"   Temps: {result['processing_time']:.2f}s")
            print(f"   Taille: {result['audio_size']} bytes")
            print(f"   Coût: {result['cost_estimate']:.6f}€")
        else:
            print(f"❌ Erreur: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
