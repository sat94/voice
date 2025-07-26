# 🗄️ Intégration Base de Données PostgreSQL - MeetVoice API

## 📋 Vue d'ensemble

L'API MeetVoice est maintenant intégrée avec une base de données PostgreSQL pour :
- **Enregistrer toutes les conversations** IA avec métadonnées complètes
- **Collecter les feedbacks** utilisateurs pour améliorer le service
- **Générer des statistiques** détaillées d'utilisation
- **Suivre les performances** des différents providers IA

## 🔧 Configuration

### Variables d'environnement (.env)
```bash
# Base de données PostgreSQL
DATABASE_URL=postgresql://appuser:securepassword123@127.0.0.1:5432/appdb
POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=securepassword123
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

### Installation des dépendances
```bash
pip install --break-system-packages psycopg2-binary sqlalchemy alembic python-dotenv
```

## 📊 Structure de la base de données

### Tables créées automatiquement :

#### 1. `conversation_logs` - Logs des conversations IA
- `id` : Identifiant unique
- `timestamp` : Date/heure de la conversation
- `user_id` : Identifiant utilisateur (optionnel)
- `prompt` : Question de l'utilisateur
- `system_prompt` : Prompt système utilisé
- `response` : Réponse de l'IA
- `provider` : Provider utilisé ("gemini", "deepinfra")
- `fallback_used` : Si le fallback a été utilisé
- `processing_time` : Temps de traitement (secondes)
- `cost` : Coût estimé de la requête
- `voice_settings` : Paramètres TTS (JSON)
- `audio_generated` : Si l'audio a été généré
- `rating` : Note utilisateur (1-5)
- `feedback` : Commentaire utilisateur

#### 2. `feedback_entries` - Feedbacks utilisateurs
- `id` : Identifiant unique
- `timestamp` : Date/heure du feedback
- `conversation_id` : Référence à la conversation
- `user_id` : Identifiant utilisateur
- `category` : Catégorie ("coaching", "technique", "general")
- `rating` : Note (1-5)
- `comment` : Commentaire
- `improvement_suggestion` : Suggestion d'amélioration
- `resolved` : Si le feedback a été traité

#### 3. `user_profiles` - Profils utilisateurs
- `id` : Identifiant unique
- `user_id` : Identifiant utilisateur unique
- `created_at` : Date de création
- `updated_at` : Dernière mise à jour
- `name` : Nom de l'utilisateur
- `age` : Âge
- `preferences` : Préférences (JSON)
- `conversation_count` : Nombre de conversations
- `last_interaction` : Dernière interaction
- `favorite_voice` : Voix préférée
- `settings` : Paramètres personnalisés (JSON)

#### 4. `system_metrics` - Métriques système
- `id` : Identifiant unique
- `timestamp` : Date/heure de la métrique
- `metric_name` : Nom de la métrique
- `metric_value` : Valeur
- `metric_unit` : Unité ("ms", "count", "percent")
- `additional_data` : Données supplémentaires (JSON)

## 🚀 Utilisation avec l'API

### Endpoints avec base de données intégrée :

#### POST /ia - Conversation IA (avec enregistrement automatique)
```json
{
  "prompt": "Comment aborder une fille dans un café ?",
  "system_prompt": "Tu es Sophie, coach de séduction experte",
  "user_id": "user123",
  "voice": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)",
  "include_audio": true
}
```

**Réponse :**
```json
{
  "prompt": "Comment aborder une fille dans un café ?",
  "response": "Voici mes conseils...",
  "provider": "gemini",
  "cost": 0.001,
  "fallback_used": false,
  "conversation_id": 42,
  "total_time": 2.3,
  "response_audio": "base64_encoded_audio..."
}
```

#### POST /feedback - Ajouter un feedback
```json
{
  "conversation_id": 42,
  "rating": 4,
  "comment": "Très bonne réponse !",
  "category": "coaching",
  "improvement_suggestion": "Plus d'exemples concrets",
  "user_id": "user123"
}
```

#### GET /stats/system - Statistiques système
```json
{
  "system_stats": {
    "total_conversations": 156,
    "gemini_usage": 120,
    "deepinfra_usage": 36,
    "fallback_rate": 23.08,
    "average_rating": 4.2,
    "total_feedbacks": 89
  },
  "database_connected": true
}
```

#### GET /stats/user/{user_id} - Statistiques utilisateur
```json
{
  "user_id": "user123",
  "stats": {
    "conversation_count": 15,
    "last_interaction": "2025-07-20T20:38:44",
    "average_rating": 4.3,
    "total_feedbacks": 8
  }
}
```

#### GET /health/database - Santé de la base de données
```json
{
  "database_connected": true,
  "database_url": "127.0.0.1:5432/appdb",
  "status": "OK"
}
```

## 🔍 Scripts de test et vérification

### 1. Test de connexion
```bash
python3 test_database.py
```

### 2. API de test simple
```bash
python3 simple_api_test.py
# Démarre sur http://localhost:8005
```

### 3. Vérification du contenu
```bash
python3 check_database_content.py
```

## 📈 Avantages de l'intégration

### 🎯 Pour le développement :
- **Debugging facilité** : Toutes les interactions sont loggées
- **Métriques de performance** : Temps de réponse, taux de fallback
- **Coûts trackés** : Suivi des coûts par provider
- **Qualité mesurée** : Ratings et feedbacks utilisateurs

### 📊 Pour l'analyse :
- **Patterns d'usage** : Quels types de questions sont posées
- **Performance des providers** : Gemini vs DeepInfra
- **Satisfaction utilisateur** : Notes et commentaires
- **Optimisation** : Identifier les points d'amélioration

### 🔧 Pour la maintenance :
- **Monitoring** : Santé de la base de données
- **Historique complet** : Toutes les conversations archivées
- **Rollback possible** : Récupération en cas de problème
- **Scaling data** : Données pour optimiser les performances

## 🛠️ Commandes utiles

### PostgreSQL direct :
```bash
# Se connecter à la base
sudo -u postgres psql -d appdb

# Voir les tables
\dt

# Compter les conversations
SELECT COUNT(*) FROM conversation_logs;

# Voir les dernières conversations
SELECT * FROM conversation_logs ORDER BY timestamp DESC LIMIT 5;
```

### Maintenance :
```bash
# Redémarrer PostgreSQL
sudo systemctl restart postgresql

# Vérifier le statut
sudo systemctl status postgresql

# Logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

## ✅ Statut actuel

- ✅ Base de données PostgreSQL installée et configurée
- ✅ Tables créées automatiquement
- ✅ Connexion testée et fonctionnelle
- ✅ Enregistrement des conversations
- ✅ Système de feedback opérationnel
- ✅ Statistiques générées
- ✅ API de test fonctionnelle
- ✅ Scripts de vérification disponibles

L'API peut maintenant **lire et écrire** dans la base de données PostgreSQL de manière transparente ! 🎉

---

## 🔗 **INTÉGRATION DJANGO COMPLÈTE**

### 🎯 Compatibilité avec votre modèle `Compte`

Le système est maintenant **100% compatible** avec votre modèle Django `Compte` :

#### ✅ **Champs synchronisés automatiquement :**
- `id` (UUID Django) → `django_user_id`
- `email` → `email`
- `username` → `username`
- `nom` → `nom`
- `prenom` → `prenom`
- `date_joined` → `date_joined`
- `date_de_naissance` → `date_de_naissance`
- `numberPhone` → `phone`
- `sexe` → `sexe`
- `taille` → `taille`
- `poids` → `poids`
- `ethnique` → `ethnique`
- `religion` → `religion`
- `yeux` → `yeux`
- `shillouette` → `silhouette`
- `situation` → `situation`
- `hair_color` → `hair_color`
- `hair_style` → `hair_style`
- `glasses` → `glasses`
- `facial_hair` → `facial_hair`
- `bio` → `bio`
- `adresse` → `adresse`
- `ville` → `ville`
- `departement` → `departement`
- `pays` → `pays`
- `code_postal` → `code_postal`
- `vues` → `vues`
- `likes` → `likes`
- `matches` → `matches`

#### 🆕 **Nouveaux champs spécifiques IA :**
- `conversation_count` : Nombre de conversations IA
- `last_interaction` : Dernière interaction avec l'IA
- `favorite_voice` : Voix TTS préférée
- `ai_preferences` : Préférences IA (JSON)
- `voice_settings` : Paramètres TTS (JSON)
- `coaching_level` : Niveau de coaching
- `topics_of_interest` : Sujets d'intérêt (JSON)

### 📊 **Nouvelles tables ajoutées :**

#### 1. `ai_sessions` - Sessions IA avancées
```sql
- session_id : Identifiant unique de session
- user_id : Email utilisateur
- django_user_id : UUID Django
- started_at : Début de session
- ended_at : Fin de session
- total_conversations : Nombre de conversations
- total_cost : Coût total
- session_type : Type ("coaching", "casual", "support")
- user_satisfaction : Note globale
- session_notes : Notes de session
```

#### 2. `coaching_progress` - Progrès de coaching
```sql
- user_id : Email utilisateur
- django_user_id : UUID Django
- topic : Sujet ("approach", "conversation", "confidence")
- level_before : Niveau avant (1-10)
- level_after : Niveau après (1-10)
- session_count : Nombre de sessions
- last_practice : Dernière pratique
- notes : Notes de progrès
- goals : Objectifs (JSON)
- achievements : Réalisations (JSON)
```

### 🔧 **Méthodes Django disponibles :**

#### Synchronisation utilisateur
```python
db_service.sync_django_user(django_user_data)
```

#### Progrès de coaching
```python
# Mettre à jour
db_service.update_coaching_progress(user_id, topic, new_level, django_user_id, notes)

# Récupérer
progress = db_service.get_user_coaching_progress(user_id, django_user_id)
```

#### Stats utilisateur avec Django
```python
stats = db_service.get_user_stats(user_email)
```

### 🚀 **Intégration avec Django REST Framework**

Voir le fichier `django_api_integration.py` pour des exemples complets de :
- Views Django REST
- Endpoints API
- Authentification
- Gestion des erreurs
- Exemples frontend

### 📈 **Avantages de l'intégration Django :**

1. **Synchronisation automatique** : Les profils Django sont automatiquement synchronisés
2. **UUID support** : Compatible avec les UUID Django
3. **Données complètes** : Toutes les informations du modèle `Compte` sont disponibles
4. **Coaching personnalisé** : Suivi des progrès par utilisateur
5. **Analytics avancées** : Statistiques détaillées par utilisateur Django
6. **Seamless integration** : Intégration transparente avec votre API existante

### ✅ **Tests réussis :**
- ✅ Synchronisation utilisateur Django
- ✅ Enregistrement conversations avec UUID
- ✅ Système de feedback
- ✅ Suivi progrès de coaching
- ✅ Statistiques avancées
- ✅ Compatibilité complète modèle `Compte`

### 🎯 **Résultat final :**

**TOUS les prompts utilisateurs et TOUTES les réponses IA sont automatiquement enregistrés** avec :
- Informations complètes de l'utilisateur Django
- Métadonnées de conversation (provider, temps, coût)
- Paramètres TTS utilisés
- Feedbacks et évaluations
- Progrès de coaching personnalisés

Le système est maintenant **prêt pour la production** avec votre application Django ! 🚀
