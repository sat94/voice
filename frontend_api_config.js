// Configuration API pour le frontend Vue.js
// Corrige les problèmes de connexion avec les APIs

const API_CONFIG = {
  // API principale (Django ou FastAPI selon votre setup)
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://aaaazealmmmma.duckdns.org' 
    : 'http://localhost:8001',
  
  // APIs spécialisées
  APIS: {
    // API TTS et questions d'inscription (main.py - port 8001)
    TTS: process.env.NODE_ENV === 'production'
      ? 'https://aaaazealmmmma.duckdns.org:8001'
      : 'http://localhost:8001',
    
    // API IA finale (api_ia_final.py - port 8004)  
    IA: process.env.NODE_ENV === 'production'
      ? 'https://aaaazealmmmma.duckdns.org:8004'
      : 'http://localhost:8004',
    
    // API conversation vocale (voice_conversation_api.py - port 8010)
    VOICE: process.env.NODE_ENV === 'production'
      ? 'https://aaaazealmmmma.duckdns.org:8010'
      : 'http://localhost:8010'
  },
  
  // Endpoints spécifiques
  ENDPOINTS: {
    // Questions d'inscription
    INSCRIPTION_QUESTION: (questionNumber) => 
      `${API_CONFIG.APIS.TTS}/inscription/question/${questionNumber}`,
    
    INSCRIPTION_INFO: () => 
      `${API_CONFIG.APIS.TTS}/inscription/info`,
    
    INSCRIPTION_GENERATE_ALL: () => 
      `${API_CONFIG.APIS.TTS}/inscription/generate-all`,
    
    // IA Chat
    IA_CHAT: () => 
      `${API_CONFIG.APIS.IA}/ia`,
    
    IA_WEBSOCKET: (userId) => 
      `${API_CONFIG.APIS.IA.replace('http', 'ws')}/ws/chat/${userId}`,
    
    // TTS libre
    TTS_GENERATE: () => 
      `${API_CONFIG.APIS.TTS}/tts`,
    
    // Conversation vocale
    VOICE_CALL: (userId) => 
      `${API_CONFIG.APIS.VOICE.replace('http', 'ws')}/ws/voice-call/${userId}`
  }
};

// Fonction helper pour les requêtes avec gestion d'erreurs
class APIClient {
  static async request(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      console.log(`🌐 API Request: ${url}`);
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      console.error(`❌ API Error for ${url}:`, error);
      throw error;
    }
  }

  // Questions d'inscription
  static async getQuestion(questionNumber) {
    const url = API_CONFIG.ENDPOINTS.INSCRIPTION_QUESTION(questionNumber);
    return await this.request(url);
  }

  static async getInscriptionInfo() {
    const url = API_CONFIG.ENDPOINTS.INSCRIPTION_INFO();
    const response = await this.request(url);
    return await response.json();
  }

  static async generateAllQuestions() {
    const url = API_CONFIG.ENDPOINTS.INSCRIPTION_GENERATE_ALL();
    const response = await this.request(url, { method: 'POST' });
    return await response.json();
  }

  // IA Chat
  static async sendToIA(prompt, systemPrompt = "Tu es Sophie, coach de séduction.", includeAudio = true) {
    const url = API_CONFIG.ENDPOINTS.IA_CHAT();
    const response = await this.request(url, {
      method: 'POST',
      body: JSON.stringify({
        prompt,
        system_prompt: systemPrompt,
        include_audio: includeAudio,
        user_id: 'vue_frontend_user',
        voice: 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)'
      })
    });
    return await response.json();
  }

  // TTS libre
  static async generateTTS(text, voice = 'Denise') {
    const url = API_CONFIG.ENDPOINTS.TTS_GENERATE();
    const response = await this.request(url, {
      method: 'POST',
      body: JSON.stringify({
        text,
        voice,
        rate: '+0%',
        pitch: '+0Hz'
      })
    });
    return response; // Retourne la réponse pour récupérer le blob audio
  }
}

// WebSocket helpers
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = {};
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        console.log(`🔌 Connecting to WebSocket: ${this.url}`);
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.emit('message', data);
        };
        
        this.ws.onclose = () => {
          console.log('❌ WebSocket disconnected');
          this.emit('disconnect');
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          reject(error);
        };
        
      } catch (error) {
        reject(error);
      }
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('❌ WebSocket not connected');
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Export pour utilisation dans Vue.js
export { API_CONFIG, APIClient, WebSocketClient };

// Exemple d'utilisation dans un composant Vue.js :
/*
import { APIClient, WebSocketClient, API_CONFIG } from './frontend_api_config.js';

export default {
  data() {
    return {
      currentQuestion: 1,
      wsClient: null
    }
  },
  
  async mounted() {
    // Tester la connexion API
    try {
      const info = await APIClient.getInscriptionInfo();
      console.log('📋 Info inscription:', info);
    } catch (error) {
      console.error('❌ Erreur API:', error);
    }
  },
  
  methods: {
    async playQuestion(questionNumber) {
      try {
        // Récupérer l'audio de la question
        const response = await APIClient.getQuestion(questionNumber);
        const audioBlob = await response.blob();
        
        // Créer et jouer l'audio
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        await audio.play();
        
        console.log(`✅ Question ${questionNumber} jouée`);
      } catch (error) {
        console.error(`❌ Erreur lecture question ${questionNumber}:`, error);
      }
    },
    
    async connectToIA() {
      try {
        const userId = 'vue_user_' + Date.now();
        const wsUrl = API_CONFIG.ENDPOINTS.IA_WEBSOCKET(userId);
        
        this.wsClient = new WebSocketClient(wsUrl);
        await this.wsClient.connect();
        
        this.wsClient.on('message', (data) => {
          console.log('📨 Message IA:', data);
          // Traiter les messages de l'IA
        });
        
      } catch (error) {
        console.error('❌ Erreur connexion IA:', error);
      }
    }
  }
}
*/
