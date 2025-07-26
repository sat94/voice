# 🚀 MeetVoice IA - Production

## 📋 Vue d'ensemble

API de coaching IA avec synthèse vocale et base de données PostgreSQL intégrée.

## 🏗️ Architecture

- **API principale** : `api_ia_final.py` - Endpoints IA avec TTS
- **Base de données** : `database.py` - Gestion PostgreSQL
- **TTS simple** : `main.py` - Service de synthèse vocale
- **Coach IA** : `coach_seduction.py` - Logique de coaching

## ⚙️ Configuration

### Variables d'environnement (.env)
```bash
# IA Providers
GEMINI_API_KEY=your_gemini_key
DEEPINFRA_API_KEY=your_deepinfra_key

# Base de données PostgreSQL
DATABASE_URL=postgresql://appuser:securepassword123@127.0.0.1:5432/appdb
POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=securepassword123
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

### Dépendances
```bash
pip install -r requirements.txt
```

### Base de données
```bash
# PostgreSQL doit être installé et configuré
sudo systemctl start postgresql
```

## 🚀 Démarrage

### API principale (recommandé)
```bash
python3 api_ia_final.py
```
**Port** : 8004  
**Endpoints** : `/ia`, `/feedback`, `/stats/*`, `/health/*`

### API TTS simple
```bash
python3 main.py
```
**Port** : 8003  
**Endpoint** : `/tts`

## 📡 Endpoints principaux

### POST /ia
Conversation IA avec enregistrement automatique en base
```json
{
  "prompt": "Comment aborder quelqu'un ?",
  "system_prompt": "Tu es Sophie, coach de séduction",
  "user_id": "user@example.com",
  "include_audio": true,
  "voice": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
}
```

### POST /feedback
Ajouter un feedback sur une conversation
```json
{
  "conversation_id": 123,
  "rating": 5,
  "comment": "Excellents conseils !",
  "user_id": "user@example.com"
}
```

### GET /stats/system
Statistiques système globales

### GET /stats/user/{user_id}
Statistiques utilisateur spécifiques

### GET /health/database
Vérification santé base de données

## 🗄️ Base de données

### Tables automatiques
- `conversation_logs` - Toutes les conversations IA
- `feedback_entries` - Feedbacks utilisateurs
- `user_profiles` - Profils utilisateurs (compatible Django)
- `coaching_progress` - Progrès de coaching
- `ai_sessions` - Sessions IA avancées

### Données enregistrées automatiquement
- ✅ **Tous les prompts utilisateurs**
- ✅ **Toutes les réponses IA**
- ✅ **Métadonnées complètes** (provider, temps, coût)
- ✅ **Paramètres TTS**
- ✅ **Feedbacks et évaluations**

## 🔒 Sécurité

- ✅ Clés API dans `.env` (non versionnées)
- ✅ Base de données sécurisée
- ✅ CORS configuré
- ✅ Fichiers de test supprimés
- ✅ Logs sécurisés

## 📊 Monitoring

- Logs automatiques des conversations
- Métriques de performance en temps réel
- Statistiques d'utilisation détaillées
- Suivi des coûts par provider

## 🔧 Maintenance

### Logs
```bash
tail -f api.log
```

### Base de données
```bash
# Connexion directe
sudo -u postgres psql -d appdb

# Vérifier les conversations
SELECT COUNT(*) FROM conversation_logs;
```

### Redémarrage
```bash
# Redémarrer l'API
pkill -f api_ia_final.py
python3 api_ia_final.py

# Redémarrer PostgreSQL
sudo systemctl restart postgresql
```

## 📈 Performance

- **Cache TTS** : Fichiers audio mis en cache dans `./cache/`
- **Base de données** : Index optimisés pour les requêtes fréquentes
- **Providers IA** : Fallback automatique Gemini → DeepInfra

## 🌐 Déploiement

### Nginx (optionnel)
Configuration disponible dans `meetvoice-tts.nginx.conf`

### Service systemd (optionnel)
Configuration disponible dans `meetvoice-tts.service`

## ✅ Statut

- ✅ API fonctionnelle
- ✅ Base de données opérationnelle
- ✅ TTS intégré
- ✅ Enregistrement automatique
- ✅ Système de feedback
- ✅ Compatible Django
- ✅ Prêt pour la production

## 📞 Support

En cas de problème :
1. Vérifier les logs : `tail -f api.log`
2. Tester la base de données : `GET /health/database`
3. Vérifier les variables d'environnement
4. Redémarrer les services si nécessaire
