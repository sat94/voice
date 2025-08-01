#!/usr/bin/env python3
"""
Script pour lister toutes les voix Edge TTS disponibles
"""

import asyncio
import edge_tts

async def list_french_voices():
    """Liste toutes les voix françaises disponibles"""
    print("🎤 Voix françaises disponibles dans Edge TTS :")
    print("=" * 60)
    
    voices = await edge_tts.list_voices()
    french_voices = [v for v in voices if v["Locale"].startswith("fr-")]
    
    for voice in french_voices:
        name = voice["Name"]
        gender = voice["Gender"]
        locale = voice["Locale"]
        display_name = voice["FriendlyName"]
        
        print(f"🎵 {name}")
        print(f"   Genre: {gender}")
        print(f"   Région: {locale}")
        print(f"   Nom: {display_name}")
        print("-" * 40)

async def test_voice(voice_name: str, text: str = "Bonjour, ceci est un test de voix."):
    """Teste une voix spécifique"""
    try:
        print(f"🧪 Test de la voix: {voice_name}")
        communicate = edge_tts.Communicate(text, voice_name)
        
        # Sauvegarder un échantillon
        filename = f"test_{voice_name.replace('-', '_')}.mp3"
        await communicate.save(filename)
        print(f"✅ Échantillon sauvegardé: {filename}")
        
    except Exception as e:
        print(f"❌ Erreur avec {voice_name}: {str(e)}")

async def main():
    # Lister toutes les voix françaises
    await list_french_voices()
    
    print("\n" + "=" * 60)
    print("🧪 Test des voix pour psychologie :")
    
    # Tester quelques voix candidates pour psychologie
    psychology_candidates = [
        "fr-FR-DeniseNeural",
        "fr-FR-EloiseNeural", 
        "fr-FR-JosephineNeural",
        "fr-FR-YvetteNeural",
        "fr-FR-CoralieNeural"
    ]
    
    test_text = "Bonjour, je suis votre psychologue. Je suis là pour vous accompagner avec bienveillance."
    
    for voice in psychology_candidates:
        await test_voice(voice, test_text)
        print()

if __name__ == "__main__":
    asyncio.run(main())
