# 🎯 TEST DES NOUVELLES FONCTIONNALITÉS IA

## 🎭 **1. JEU DE RÔLE IA - SIMULATION DE RENDEZ-VOUS**

### **✅ Fonctionnalités implémentées :**

#### **🚀 Démarrer une simulation :**
```bash
curl -X POST http://localhost:8001/roleplay/start-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "date_name": "Sarah",
    "date_age": 26,
    "date_interests": ["voyages", "cuisine", "sport"],
    "date_personality": "extravertie",
    "scenario": "premier_rendez_vous_cafe",
    "user_name": "Alexandre"
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "simulation_id": "sim_abc12345",
  "date_profile": {
    "name": "Sarah",
    "age": 26,
    "interests": ["voyages", "cuisine", "sport"],
    "personality": "extravertie",
    "scenario": "premier_rendez_vous_cafe"
  },
  "scenario_description": "☕ Premier rendez-vous dans un café cosy. Ambiance détendue, apprendre à se connaître.",
  "first_message": "Salut Alexandre ! *sourire un peu gêné* Alors, tu as trouvé facilement ? J'espère que je ne t'ai pas fait attendre...",
  "coaching_tip": "💡 Elle semble un peu nerveuse, mets-la à l'aise avec une réponse détendue et rassurante !",
  "interest_level": 50,
  "tips": [
    "Sois naturel et authentique",
    "Pose des questions sur elle",
    "Écoute ses réponses attentivement",
    "Partage des choses sur toi aussi"
  ]
}
```

#### **💬 Envoyer un message dans la simulation :**
```bash
curl -X POST http://localhost:8001/roleplay/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_abc12345",
    "user_message": "Salut Sarah ! Pas de souci, je viens juste d'arriver. Tu es encore plus jolie qu'en photo !",
    "session_id": "roleplay_test"
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "date_response": "*rougit légèrement* Oh merci, c'est gentil ! Toi aussi tu es très bien. Alors, qu'est-ce que tu prends comme boisson ?",
  "coaching": {
    "message_quality": "Bonne",
    "engagement": "Moyen",
    "enthusiasm": "Élevé",
    "positivity": 1,
    "tips": ["✅ Excellent ! Ton positivisme transparaît"]
  },
  "interest_level": 63,
  "conversation_score": 25,
  "suggestions": [
    "Elle semble réceptive, tu peux être plus personnel",
    "Réponds à sa question et pose-en une en retour"
  ],
  "scenario_status": {
    "status": "😊 Très bien ! Bonne connexion",
    "phase": "Début de conversation",
    "advice": "Concentre-toi sur briser la glace et la mettre à l'aise"
  }
}
```

#### **📊 Consulter le statut d'une simulation :**
```bash
curl http://localhost:8001/roleplay/simulation/sim_abc12345
```

### **🎯 Scénarios disponibles :**
- `premier_rendez_vous_cafe` - ☕ Café cosy, première rencontre
- `diner_restaurant` - 🍽️ Dîner romantique, deuxième rendez-vous
- `activite_fun` - 🎳 Mini-golf/bowling, ambiance décontractée
- `cafe_deuxieme_rdv` - ☕ Deuxième café, plus de complicité

---

## 🔍 **2. ANALYSE DES MICRO-SIGNAUX**

### **✅ Fonctionnalités implémentées :**

#### **🔍 Analyser les micro-signaux d'une conversation :**
```bash
curl -X POST http://localhost:8001/micro-signals/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "user_id": "user_456",
    "messages": [
      {
        "content": "Salut ! Comment ça va ?",
        "timestamp": "2025-01-31T10:00:00Z",
        "sender": "user"
      },
      {
        "content": "Salut ! Ça va bien merci, et toi ? 😊",
        "timestamp": "2025-01-31T10:02:00Z",
        "sender": "assistant"
      },
      {
        "content": "Super ! Tu fais quoi de beau aujourd'hui ?",
        "timestamp": "2025-01-31T10:03:30Z",
        "sender": "user"
      },
      {
        "content": "Je travaille un peu, mais j'ai hâte de finir ! Et toi ? Tu as des projets sympas ? 😄",
        "timestamp": "2025-01-31T10:04:00Z",
        "sender": "assistant"
      }
    ]
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "conversation_id": "conv_123",
  "micro_signals": {
    "interest_level": "Intérêt croissant",
    "engagement_evolution": {
      "trend": "Engagement en hausse",
      "first_half_score": 15,
      "second_half_score": 22,
      "evolution": 7
    },
    "emotional_indicators": {
      "emotional_tone": "Très positif",
      "positive_ratio": 1.0,
      "flirty_ratio": 0.0,
      "negative_ratio": 0.0
    },
    "conversation_health": "Bonne fluidité",
    "response_pattern": {
      "average_response_time": 90.0,
      "speed_category": "Rapide",
      "interpretation": "Bien engagé",
      "consistency": "Consistant"
    },
    "communication_style": {
      "verbosity": "Modéré",
      "curiosity": "Très curieux",
      "expressiveness": "Expressif",
      "avg_message_length": 35.5,
      "question_ratio": 0.75,
      "emoji_ratio": 0.5
    }
  },
  "predictions": {
    "next_optimal_action": "Continue sur cette lancée, approfondis la conversation",
    "best_response_time": "Réponds dans les 5 minutes",
    "success_probability": 78
  },
  "recommendations": [
    "✅ Excellent ! Elle s'intéresse de plus en plus à toi",
    "👍 Parfait ! Tu es très expressif, continue comme ça"
  ],
  "conversation_score": 75,
  "analysis_timestamp": "2025-01-31T10:05:00Z"
}
```

#### **📈 Analyser une conversation existante :**
```bash
curl http://localhost:8001/micro-signals/conversation/default
```

---

## 🧪 **TESTS PRATIQUES**

### **🎭 Test du jeu de rôle complet :**

```bash
# 1. Démarrer une simulation
SIMULATION_ID=$(curl -s -X POST http://localhost:8001/roleplay/start-simulation \
  -H "Content-Type: application/json" \
  -d '{"date_name": "Emma", "scenario": "activite_fun", "user_name": "Alex"}' \
  | jq -r '.simulation_id')

echo "Simulation ID: $SIMULATION_ID"

# 2. Envoyer plusieurs messages
curl -X POST http://localhost:8001/roleplay/send-message \
  -H "Content-Type: application/json" \
  -d "{\"simulation_id\": \"$SIMULATION_ID\", \"user_message\": \"Salut Emma ! Prêt pour me battre au mini-golf ? 😄\"}"

curl -X POST http://localhost:8001/roleplay/send-message \
  -H "Content-Type: application/json" \
  -d "{\"simulation_id\": \"$SIMULATION_ID\", \"user_message\": \"Haha, on verra bien ! Tu joues souvent ?\"}"

# 3. Voir le statut final
curl http://localhost:8001/roleplay/simulation/$SIMULATION_ID
```

### **🔍 Test des micro-signaux :**

```bash
# Analyser une conversation avec différents patterns
curl -X POST http://localhost:8001/micro-signals/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test_microsignals",
    "user_id": "test_user",
    "messages": [
      {"content": "Salut", "timestamp": "2025-01-31T10:00:00Z", "sender": "user"},
      {"content": "Salut ! 😊", "timestamp": "2025-01-31T10:05:00Z", "sender": "assistant"},
      {"content": "Tu fais quoi ?", "timestamp": "2025-01-31T10:06:00Z", "sender": "user"},
      {"content": "Je regarde un film ! Et toi ? 😄", "timestamp": "2025-01-31T10:06:30Z", "sender": "assistant"},
      {"content": "Cool ! Quel genre de film tu aimes ?", "timestamp": "2025-01-31T10:07:00Z", "sender": "user"},
      {"content": "J'adore les comédies romantiques ! Et toi ? Tu as des recommandations ? 💕", "timestamp": "2025-01-31T10:07:15Z", "sender": "assistant"}
    ]
  }'
```

---

## 📊 **MÉTRIQUES À SURVEILLER**

### **🎭 Jeu de rôle :**
- **Niveau d'intérêt** : 0-100 (doit évoluer selon les messages)
- **Score de conversation** : 0-100 (basé sur longueur + qualité)
- **Qualité du coaching** : Conseils pertinents et personnalisés
- **Réalisme de l'IA** : Réponses naturelles et cohérentes

### **🔍 Micro-signaux :**
- **Précision de l'analyse** : Détection correcte des patterns
- **Pertinence des conseils** : Recommandations utiles
- **Probabilité de succès** : Calcul cohérent (0-100)
- **Temps de réponse** : < 2 secondes pour l'analyse

---

## 🎯 **SCÉNARIOS DE TEST AVANCÉS**

### **🎭 Jeu de rôle - Différents niveaux d'intérêt :**

```bash
# Test 1: Messages positifs (intérêt croissant)
# "Tu es vraiment sympa !" → Intérêt +8
# "J'adore parler avec toi 😊" → Intérêt +11

# Test 2: Messages négatifs (intérêt décroissant)  
# "Bof..." → Intérêt -10
# "Pas terrible" → Intérêt -10

# Test 3: Messages inappropriés (forte baisse)
# Messages avec mots inappropriés → Intérêt -15
```

### **🔍 Micro-signaux - Patterns complexes :**

```bash
# Test 1: Intérêt croissant
# Temps de réponse qui diminue + messages plus longs

# Test 2: Engagement décroissant
# Messages de plus en plus courts + moins d'émojis

# Test 3: Style de communication
# Beaucoup de questions → "Très curieux"
# Messages longs → "Très expressif"
```

---

## 🚀 **INTÉGRATION FRONTEND**

### **Vue.js - Composant jeu de rôle :**
```javascript
// RoleplaySimulation.vue
export default {
  data() {
    return {
      simulationId: null,
      messages: [],
      interestLevel: 50,
      coaching: {}
    }
  },
  
  methods: {
    async startSimulation() {
      const response = await fetch('/roleplay/start-simulation', {
        method: 'POST',
        body: JSON.stringify({
          date_name: 'Sarah',
          scenario: 'premier_rendez_vous_cafe',
          user_name: this.userName
        })
      })
      
      const data = await response.json()
      this.simulationId = data.simulation_id
      this.messages.push({
        sender: 'date',
        content: data.first_message
      })
    },
    
    async sendMessage(message) {
      const response = await fetch('/roleplay/send-message', {
        method: 'POST',
        body: JSON.stringify({
          simulation_id: this.simulationId,
          user_message: message
        })
      })
      
      const data = await response.json()
      this.interestLevel = data.interest_level
      this.coaching = data.coaching
      
      this.messages.push({
        sender: 'date',
        content: data.date_response
      })
    }
  }
}
```

### **Vue.js - Composant micro-signaux :**
```javascript
// MicroSignalsAnalysis.vue
export default {
  methods: {
    async analyzeMicroSignals(conversationId, messages) {
      const response = await fetch('/micro-signals/analyze', {
        method: 'POST',
        body: JSON.stringify({
          conversation_id: conversationId,
          user_id: this.userId,
          messages: messages
        })
      })
      
      const analysis = await response.json()
      
      // Afficher les insights
      this.showInsights(analysis.micro_signals)
      this.showRecommendations(analysis.recommendations)
      this.showPredictions(analysis.predictions)
    }
  }
}
```

---

**🎉 Les deux fonctionnalités sont prêtes à être testées et intégrées dans Meet-Voice !**

**📅 Implémentation terminée le : 31 Janvier 2025**
