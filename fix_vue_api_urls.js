// Script de correction pour les URLs d'API dans le composant Vue.js
// Corrige les problèmes 404 et CORS

// Configuration des URLs correctes
const API_URLS = {
  // En développement
  development: {
    TTS_BASE: 'http://localhost:8001',
    IA_BASE: 'http://localhost:8004',
    VOICE_BASE: 'http://localhost:8010'
  },
  
  // En production
  production: {
    TTS_BASE: 'https://aaaazealmmmma.duckdns.org:8001',
    IA_BASE: 'https://aaaazealmmmma.duckdns.org:8004', 
    VOICE_BASE: 'https://aaaazealmmmma.duckdns.org:8010'
  }
};

// Détection de l'environnement
const ENV = process.env.NODE_ENV || 'development';
const CURRENT_URLS = API_URLS[ENV];

// Fonctions corrigées pour votre composant VoiceInterviewSimple.vue
const VoiceInterviewFixes = {
  
  // Fonction corrigée pour jouer une question
  async playQuestion(questionNumber) {
    try {
      // URL corrigée (sans double slash)
      const url = `${CURRENT_URLS.TTS_BASE}/inscription/question/${questionNumber}`;
      
      console.log(`🎵 Lecture question ${questionNumber}: ${url}`);
      
      // Requête avec gestion d'erreurs améliorée
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'audio/mpeg, audio/wav, audio/*',
          'Cache-Control': 'no-cache'
        },
        mode: 'cors'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Vérifier le type de contenu
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.startsWith('audio/')) {
        throw new Error(`Type de contenu invalide: ${contentType}`);
      }
      
      // Convertir en blob et jouer
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Créer et configurer l'élément audio
      const audio = new Audio(audioUrl);
      audio.preload = 'auto';
      
      // Promesse pour attendre la fin de lecture
      return new Promise((resolve, reject) => {
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl); // Nettoyer la mémoire
          console.log(`✅ Question ${questionNumber} terminée`);
          resolve();
        };
        
        audio.onerror = (error) => {
          URL.revokeObjectURL(audioUrl);
          console.error(`❌ Erreur lecture audio:`, error);
          reject(new Error('Erreur lecture audio'));
        };
        
        audio.onloadstart = () => {
          console.log(`🔄 Chargement audio question ${questionNumber}...`);
        };
        
        audio.oncanplay = () => {
          console.log(`▶️ Lecture question ${questionNumber}`);
        };
        
        // Démarrer la lecture
        audio.play().catch(reject);
      });
      
    } catch (error) {
      console.error(`❌ Erreur lecture question ${questionNumber}:`, error);
      
      // Afficher une erreur utilisateur plus claire
      if (error.message.includes('404')) {
        throw new Error(`Question ${questionNumber} non trouvée sur le serveur`);
      } else if (error.message.includes('CORS')) {
        throw new Error('Problème de connexion au serveur (CORS)');
      } else if (error.message.includes('Failed to fetch')) {
        throw new Error('Serveur non accessible. Vérifiez que l\'API TTS est démarrée.');
      } else {
        throw error;
      }
    }
  },
  
  // Fonction pour obtenir les infos d'inscription
  async getInscriptionInfo() {
    try {
      const url = `${CURRENT_URLS.TTS_BASE}/inscription/info`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('📋 Info inscription:', data);
      return data;
      
    } catch (error) {
      console.error('❌ Erreur récupération info inscription:', error);
      throw error;
    }
  },
  
  // Fonction pour envoyer à l'IA
  async sendToIA(prompt, includeAudio = true) {
    try {
      const url = `${CURRENT_URLS.IA_BASE}/ia`;
      
      const requestData = {
        prompt: prompt,
        system_prompt: "Tu es Sophie, coach de séduction experte et bienveillante.",
        include_audio: includeAudio,
        user_id: 'vue_frontend_user',
        voice: 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)',
        rate: '+0%',
        pitch: '+0Hz'
      };
      
      console.log('🤖 Envoi à l\'IA:', { prompt: prompt.substring(0, 50) + '...', includeAudio });
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Réponse IA reçue:', {
        provider: data.provider,
        hasAudio: !!data.audio,
        responseLength: data.response?.length || 0
      });
      
      return data;
      
    } catch (error) {
      console.error('❌ Erreur envoi IA:', error);
      throw error;
    }
  },
  
  // Fonction pour tester la connectivité des APIs
  async testAPIsConnectivity() {
    const results = {};
    
    const apisToTest = [
      { name: 'TTS/Inscription', url: `${CURRENT_URLS.TTS_BASE}/` },
      { name: 'IA', url: `${CURRENT_URLS.IA_BASE}/` },
      { name: 'Voice', url: `${CURRENT_URLS.VOICE_BASE}/` }
    ];
    
    for (const api of apisToTest) {
      try {
        const startTime = Date.now();
        const response = await fetch(api.url, { 
          method: 'GET',
          mode: 'cors',
          timeout: 5000 
        });
        const endTime = Date.now();
        
        results[api.name] = {
          status: response.ok ? 'OK' : `Error ${response.status}`,
          responseTime: endTime - startTime,
          url: api.url
        };
        
      } catch (error) {
        results[api.name] = {
          status: `Error: ${error.message}`,
          responseTime: null,
          url: api.url
        };
      }
    }
    
    console.log('🔍 Test connectivité APIs:', results);
    return results;
  }
};

// Configuration WebSocket corrigée
const WebSocketConfig = {
  
  // URL WebSocket pour l'IA
  getIAWebSocketURL(userId) {
    const baseUrl = CURRENT_URLS.IA_BASE.replace('http', 'ws');
    return `${baseUrl}/ws/chat/${userId}`;
  },
  
  // URL WebSocket pour la conversation vocale
  getVoiceWebSocketURL(userId) {
    const baseUrl = CURRENT_URLS.VOICE_BASE.replace('http', 'ws');
    return `${baseUrl}/ws/voice-call/${userId}`;
  },
  
  // Créer une connexion WebSocket avec retry
  async createWebSocket(url, maxRetries = 3) {
    let retries = 0;
    
    while (retries < maxRetries) {
      try {
        console.log(`🔌 Tentative connexion WebSocket: ${url} (${retries + 1}/${maxRetries})`);
        
        const ws = new WebSocket(url);
        
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            ws.close();
            reject(new Error('Timeout connexion WebSocket'));
          }, 10000);
          
          ws.onopen = () => {
            clearTimeout(timeout);
            console.log('✅ WebSocket connecté');
            resolve(ws);
          };
          
          ws.onerror = (error) => {
            clearTimeout(timeout);
            console.error('❌ Erreur WebSocket:', error);
            reject(error);
          };
        });
        
      } catch (error) {
        retries++;
        if (retries >= maxRetries) {
          throw new Error(`Échec connexion WebSocket après ${maxRetries} tentatives: ${error.message}`);
        }
        
        // Attendre avant de réessayer
        await new Promise(resolve => setTimeout(resolve, 1000 * retries));
      }
    }
  }
};

// Export pour utilisation dans Vue.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { VoiceInterviewFixes, WebSocketConfig, API_URLS, CURRENT_URLS };
} else if (typeof window !== 'undefined') {
  window.VoiceInterviewFixes = VoiceInterviewFixes;
  window.WebSocketConfig = WebSocketConfig;
  window.API_URLS = API_URLS;
  window.CURRENT_URLS = CURRENT_URLS;
}

// Instructions d'utilisation dans votre composant Vue.js :
/*
// Dans votre composant VoiceInterviewSimple.vue, remplacez :

// AVANT (qui cause l'erreur 404) :
async playQuestion(questionNumber) {
  const response = await fetch(`https://aaaazealmmmma.duckdns.org//inscription/question/${questionNumber}`);
  // ...
}

// APRÈS (corrigé) :
import { VoiceInterviewFixes } from './fix_vue_api_urls.js';

export default {
  methods: {
    async playQuestion(questionNumber) {
      try {
        await VoiceInterviewFixes.playQuestion(questionNumber);
        // Question jouée avec succès
      } catch (error) {
        this.showError(`Erreur lecture question: ${error.message}`);
      }
    },
    
    async sendToIA(prompt) {
      try {
        const response = await VoiceInterviewFixes.sendToIA(prompt, true);
        // Traiter la réponse IA
        return response;
      } catch (error) {
        this.showError(`Erreur IA: ${error.message}`);
      }
    },
    
    async testConnectivity() {
      const results = await VoiceInterviewFixes.testAPIsConnectivity();
      console.log('Résultats test:', results);
    }
  },
  
  async mounted() {
    // Tester la connectivité au démarrage
    await this.testConnectivity();
  }
}
*/
