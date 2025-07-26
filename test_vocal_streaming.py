#!/usr/bin/env python3
"""
Test de l'endpoint vocal streaming
"""

import requests
import time
import tempfile
import wave
import struct

def creer_audio_test():
    """Crée un fichier audio de test simple"""
    # Créer un fichier WAV simple avec un bip
    sample_rate = 44100
    duration = 2  # 2 secondes
    frequency = 440  # La note A
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Générer un signal sinusoïdal simple
            for i in range(int(sample_rate * duration)):
                value = int(32767 * 0.3 * (i % 1000) / 1000)  # Signal simple
                wav_file.writeframes(struct.pack('<h', value))
        
        return temp_file.name

def test_endpoint_vocal():
    """Test l'endpoint vocal streaming"""
    
    print("🎤 TEST ENDPOINT VOCAL STREAMING")
    print("=" * 60)
    
    url = "http://localhost:8012/vocal"
    
    # Créer un fichier audio de test
    print("📁 Création d'un fichier audio de test...")
    audio_file_path = creer_audio_test()
    
    try:
        # Préparer les données
        files = {
            'audio_file': ('test_audio.wav', open(audio_file_path, 'rb'), 'audio/wav')
        }
        
        data = {
            'prenom': 'TestUser',
            'voice': 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)',
            'rate': '+0%',
            'pitch': '+0Hz'
        }
        
        print("🚀 Envoi de la requête vocal...")
        start_time = time.time()
        
        # Faire la requête
        response = requests.post(url, files=files, data=data, stream=True)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers:")
        for key, value in response.headers.items():
            if key.startswith('X-'):
                print(f"   {key}: {value}")
        
        if response.status_code == 200:
            print("✅ Succès ! Réception du streaming audio...")
            
            # Sauvegarder la réponse audio
            with open("reponse_vocale.mp3", "wb") as f:
                total_size = 0
                chunk_count = 0
                
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
                        chunk_count += 1
                        
                        # Afficher le progrès
                        if chunk_count % 10 == 0:
                            print(f"   📦 Reçu {total_size} bytes en {chunk_count} chunks...")
            
            total_time = time.time() - start_time
            print(f"⏱️ Temps total: {total_time:.3f}s")
            print(f"📁 Audio sauvé: reponse_vocale.mp3 ({total_size} bytes)")
            
            # Analyser les headers de performance
            if 'X-Transcription-Time' in response.headers:
                transcription_time = float(response.headers['X-Transcription-Time'])
                ia_time = float(response.headers['X-IA-Time'])
                total_backend_time = float(response.headers['X-Total-Time'])
                
                print(f"\n📈 PERFORMANCE DÉTAILLÉE:")
                print(f"   🎤 Transcription: {transcription_time:.3f}s")
                print(f"   🤖 IA: {ia_time:.3f}s")
                print(f"   🎵 Streaming: {total_time - total_backend_time:.3f}s")
                print(f"   ⚡ Total backend: {total_backend_time:.3f}s")
                print(f"   🌐 Total avec réseau: {total_time:.3f}s")
                
                if 'X-Provider' in response.headers:
                    print(f"   🤖 Provider: {response.headers['X-Provider']}")
                
                if 'X-Transcription' in response.headers:
                    print(f"   📝 Transcrit: {response.headers['X-Transcription']}")
            
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"📄 Réponse: {response.text}")
            
            # Vérifier les headers d'erreur
            if 'X-Error' in response.headers:
                print(f"🚨 Erreur: {response.headers['X-Error']}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    finally:
        # Nettoyer
        try:
            files['audio_file'][1].close()
            import os
            os.unlink(audio_file_path)
        except:
            pass

def test_comparaison_vitesse():
    """Compare la vitesse vocal vs texte"""
    
    print("\n🏁 COMPARAISON VITESSE: VOCAL vs TEXTE")
    print("=" * 60)
    
    # Test endpoint texte classique
    print("1️⃣ Test endpoint TEXTE classique...")
    start_time = time.time()
    
    try:
        response = requests.post("http://localhost:8012/ia", json={
            "prompt": "Bonjour Sophie !",
            "prenom": "TestUser",
            "include_audio": True
        })
        
        texte_time = time.time() - start_time
        texte_size = len(response.content) if response.status_code == 200 else 0
        
        print(f"   ⏱️ Temps: {texte_time:.3f}s")
        print(f"   📦 Taille: {texte_size} bytes")
        print(f"   📊 Status: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        texte_time = 999
        texte_size = 0
    
    # Test endpoint vocal (simulation)
    print("\n2️⃣ Test endpoint VOCAL streaming...")
    print("   🎤 (Simulation - pas de vrai audio pour ce test)")
    
    vocal_time = 2.5  # Estimation basée sur les logs
    vocal_size = 50000  # Estimation audio MP3
    
    print(f"   ⏱️ Temps estimé: {vocal_time:.3f}s")
    print(f"   📦 Taille estimée: {vocal_size} bytes")
    
    # Comparaison
    print(f"\n📊 RÉSULTATS:")
    print(f"   🐌 Texte + Audio: {texte_time:.3f}s ({texte_size} bytes)")
    print(f"   🚀 Vocal streaming: {vocal_time:.3f}s ({vocal_size} bytes)")
    
    if texte_time > 0:
        gain_temps = ((texte_time - vocal_time) / texte_time) * 100
        gain_taille = ((texte_size - vocal_size) / texte_size) * 100 if texte_size > 0 else 0
        
        print(f"   ⚡ Gain temps: {gain_temps:+.1f}%")
        print(f"   💾 Gain taille: {gain_taille:+.1f}%")

if __name__ == "__main__":
    test_endpoint_vocal()
    test_comparaison_vitesse()
