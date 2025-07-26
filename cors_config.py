#!/usr/bin/env python3
"""
Configuration CORS unifiée pour toutes les APIs MeetVoice
Évite les conflits de headers CORS
"""

from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app, api_name="MeetVoice API"):
    """
    Configure CORS de manière uniforme pour toutes les APIs
    """
    
    # Origines autorisées
    allowed_origins = [
        "http://localhost:8080",      # Vue.js dev
        "http://localhost:8083",      # Vue.js dev (votre port)
        "http://localhost:3000",      # React dev
        "https://aaaazealmmmma.duckdns.org",  # Production
        "https://meetvoice.app",      # Si vous avez un autre domaine
    ]
    
    # Configuration CORS optimisée
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Origines spécifiques au lieu de "*"
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-API-Key",
            "Cache-Control"
        ],
        expose_headers=["Content-Length", "Content-Type"],
        max_age=3600  # Cache preflight requests for 1 hour
    )
    
    print(f"✅ CORS configuré pour {api_name}")
    print(f"   Origines autorisées: {len(allowed_origins)}")
    
    return app

# Middleware personnalisé pour debug CORS
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def cors_debug_middleware(request: Request, call_next):
    """
    Middleware de debug pour les problèmes CORS
    """
    
    # Log de la requête
    origin = request.headers.get("origin", "No origin")
    method = request.method
    path = request.url.path
    
    logger.info(f"🌐 {method} {path} from {origin}")
    
    # Traiter la requête
    if method == "OPTIONS":
        # Réponse preflight personnalisée
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = origin if origin != "No origin" else "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "3600"
        response.status_code = 200
        return response
    
    try:
        response = await call_next(request)
        
        # Ajouter headers CORS si pas déjà présents
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = origin if origin != "No origin" else "*"
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur dans cors_debug_middleware: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)},
            headers={
                "Access-Control-Allow-Origin": origin if origin != "No origin" else "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )

def add_cors_debug(app):
    """
    Ajoute le middleware de debug CORS
    """
    app.middleware("http")(cors_debug_middleware)
    print("🔍 Middleware debug CORS ajouté")
    return app

# Configuration spécifique par environnement
import os

def get_cors_config():
    """
    Retourne la configuration CORS selon l'environnement
    """
    
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "allow_origins": [
                "https://aaaazealmmmma.duckdns.org",
                "https://meetvoice.app"
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "max_age": 86400  # 24h en production
        }
    else:
        return {
            "allow_origins": [
                "http://localhost:8080",
                "http://localhost:8083", 
                "http://localhost:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8083"
            ],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "max_age": 3600
        }

# Fonction helper pour vérifier les URLs
def validate_api_urls():
    """
    Valide que les URLs d'API sont correctes
    """
    
    apis = {
        "TTS/Inscription": "http://localhost:8001",
        "IA Finale": "http://localhost:8004", 
        "WebSocket Chat": "http://localhost:8005",
        "Vocal Optimisé": "http://localhost:8006",
        "DeepInfra TTS": "http://localhost:8008",
        "Vocal Français": "http://localhost:8009",
        "Conversation Vocale": "http://localhost:8010"
    }
    
    print("🔍 URLs des APIs:")
    for name, url in apis.items():
        print(f"   {name}: {url}")
    
    print("\n📋 Endpoints d'inscription disponibles:")
    print("   GET  /inscription/question/{1-30}")
    print("   GET  /inscription/info") 
    print("   POST /inscription/generate-all")
    
    print("\n🤖 Endpoints IA disponibles:")
    print("   POST /ia")
    print("   WS   /ws/chat/{user_id}")
    
    return apis

# Test de connectivité
import requests
import asyncio

async def test_api_connectivity():
    """
    Teste la connectivité des APIs
    """
    
    apis_to_test = [
        ("TTS/Inscription", "http://localhost:8001"),
        ("IA Finale", "http://localhost:8004"),
    ]
    
    results = {}
    
    for name, base_url in apis_to_test:
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            results[name] = {
                "status": "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}",
                "url": base_url,
                "response_time": response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException as e:
            results[name] = {
                "status": f"❌ ERROR: {str(e)}",
                "url": base_url,
                "response_time": None
            }
    
    print("🔍 Test de connectivité des APIs:")
    for name, result in results.items():
        print(f"   {name}: {result['status']} ({result['url']})")
        if result['response_time']:
            print(f"      Temps de réponse: {result['response_time']:.3f}s")
    
    return results

if __name__ == "__main__":
    print("🔧 Configuration CORS MeetVoice")
    print("=" * 50)
    
    # Valider les URLs
    validate_api_urls()
    
    # Tester la connectivité
    print("\n🧪 Test de connectivité...")
    asyncio.run(test_api_connectivity())
    
    # Afficher la config CORS
    print("\n⚙️ Configuration CORS:")
    config = get_cors_config()
    for key, value in config.items():
        print(f"   {key}: {value}")
