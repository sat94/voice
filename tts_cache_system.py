#!/usr/bin/env python3
"""
Système de cache TTS intelligent pour optimiser le vocal
"""

import hashlib
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TTSCacheSystem:
    def __init__(self, cache_dir: str = "./tts_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, bytes] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "generated": 0}
        
        # Phrases communes pré-générées
        self.common_phrases = [
            "Excellente question !",
            "Voici mes conseils :",
            "Premièrement,",
            "Deuxièmement,", 
            "Troisièmement,",
            "L'important est de",
            "Tu peux aussi",
            "N'hésite pas à",
            "Bonne chance !",
            "J'espère que ça t'aide !"
        ]
        
        # Pré-générer les phrases communes au démarrage
        asyncio.create_task(self.pregenerate_common_phrases())
    
    def get_cache_key(self, text: str, voice: str, rate: str, pitch: str) -> str:
        """Génère une clé de cache unique"""
        content = f"{text}|{voice}|{rate}|{pitch}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cache_path(self, cache_key: str) -> Path:
        """Retourne le chemin du fichier de cache"""
        return self.cache_dir / f"{cache_key}.mp3"
    
    async def get_cached_audio(self, text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> Optional[bytes]:
        """Récupère l'audio du cache si disponible"""
        cache_key = self.get_cache_key(text, voice, rate, pitch)
        
        # 1. Vérifier le cache mémoire (le plus rapide)
        if cache_key in self.memory_cache:
            self.cache_stats["hits"] += 1
            logger.info(f"🚀 Cache mémoire HIT: {text[:30]}...")
            return self.memory_cache[cache_key]
        
        # 2. Vérifier le cache disque
        cache_path = self.get_cache_path(cache_key)
        if cache_path.exists():
            try:
                audio_data = cache_path.read_bytes()
                # Mettre en cache mémoire pour la prochaine fois
                self.memory_cache[cache_key] = audio_data
                self.cache_stats["hits"] += 1
                logger.info(f"💾 Cache disque HIT: {text[:30]}...")
                return audio_data
            except Exception as e:
                logger.error(f"Erreur lecture cache: {e}")
        
        # 3. Pas de cache trouvé
        self.cache_stats["misses"] += 1
        return None
    
    async def cache_audio(self, text: str, voice: str, audio_data: bytes, rate: str = "+0%", pitch: str = "+0Hz"):
        """Met en cache l'audio généré"""
        cache_key = self.get_cache_key(text, voice, rate, pitch)
        
        try:
            # Cache mémoire
            self.memory_cache[cache_key] = audio_data
            
            # Cache disque
            cache_path = self.get_cache_path(cache_key)
            cache_path.write_bytes(audio_data)
            
            logger.info(f"💾 Audio mis en cache: {text[:30]}...")
            
        except Exception as e:
            logger.error(f"Erreur mise en cache: {e}")
    
    async def generate_or_get_audio(self, text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
        """Récupère du cache ou génère l'audio"""
        
        # Essayer le cache d'abord
        cached_audio = await self.get_cached_audio(text, voice, rate, pitch)
        if cached_audio:
            return cached_audio
        
        # Générer l'audio (votre logique TTS existante)
        logger.info(f"🎵 Génération TTS: {text[:30]}...")
        audio_data = await self.generate_tts_audio(text, voice, rate, pitch)
        
        # Mettre en cache
        await self.cache_audio(text, voice, audio_data, rate, pitch)
        self.cache_stats["generated"] += 1
        
        return audio_data
    
    async def generate_tts_audio(self, text: str, voice: str, rate: str, pitch: str) -> bytes:
        """Génère l'audio TTS (remplacez par votre vraie logique)"""
        # Simuler la génération TTS
        await asyncio.sleep(0.5)  # Temps de génération simulé
        return f"audio_data_for_{text[:10]}".encode()
    
    async def pregenerate_common_phrases(self):
        """Pré-génère les phrases communes au démarrage"""
        logger.info("🚀 Pré-génération des phrases communes...")
        
        voice = "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        
        for phrase in self.common_phrases:
            try:
                await self.generate_or_get_audio(phrase, voice)
                await asyncio.sleep(0.1)  # Éviter la surcharge
            except Exception as e:
                logger.error(f"Erreur pré-génération {phrase}: {e}")
        
        logger.info(f"✅ {len(self.common_phrases)} phrases communes pré-générées")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du cache"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "generated": self.cache_stats["generated"],
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "disk_cache_files": len(list(self.cache_dir.glob("*.mp3"))),
            "common_phrases_cached": len(self.common_phrases)
        }
    
    def clear_cache(self):
        """Vide le cache"""
        # Vider le cache mémoire
        self.memory_cache.clear()
        
        # Vider le cache disque
        for cache_file in self.cache_dir.glob("*.mp3"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Erreur suppression cache: {e}")
        
        logger.info("🗑️ Cache vidé")

# Instance globale
tts_cache = TTSCacheSystem()

# Fonction d'aide pour l'intégration
async def get_optimized_audio(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Fonction principale pour obtenir l'audio optimisé"""
    return await tts_cache.generate_or_get_audio(text, voice, rate, pitch)
