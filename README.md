# 🎵 MeetVoice TTS API

API de synthèse vocale ultra-légère pour l'application de rencontre MeetVoice.

## ✨ Fonctionnalités

- **30 questions d'inscription** humanisées avec Sophie comme guide
- **Question conditionnelle** pour les hommes (barbe/moustache)
- **Synthèse vocale** avec Edge TTS (Microsoft)
- **Cache intelligent** pour performances optimales
- **Voix Denise** cohérente sur toutes les questions
- **API REST** simple et efficace

## 🚀 Installation

```bash
# Cloner le repository
git clone https://github.com/sat94/voice.git
cd voice

# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
python main.py
```

## 📡 Endpoints

### Questions d'inscription
- `GET /inscription/question/{1-30}` - Questions d'inscription
- `GET /inscription/barbe` - Question conditionnelle (hommes)
- `GET /inscription/info` - Informations générales
- `POST /inscription/generate-all` - Pré-génération complète

### Synthèse vocale
- `POST /tts` - Synthèse vocale libre
- `GET /voices` - Liste des voix disponibles

### Cache
- `GET /cache/stats` - Statistiques du cache

## 🎯 Utilisation

```javascript
// Question d'inscription
fetch('http://localhost:8001/inscription/question/1')
  .then(response => response.blob())
  .then(blob => {
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();
  });

// Question conditionnelle pour hommes
if (genre === 'homme') {
  fetch('http://localhost:8001/inscription/barbe')
    .then(response => response.blob())
    .then(blob => {
      const audio = new Audio(URL.createObjectURL(blob));
      audio.play();
    });
}
```

## 🛠️ Technologies

- **FastAPI** - Framework web moderne
- **Edge TTS** - Synthèse vocale Microsoft (gratuit)
- **Python 3.8+** - Langage de programmation
- **Cache intelligent** - Système de fichiers

## 📊 Performance

- **Cache hit** : < 50ms
- **Génération** : 2-3 secondes
- **Capacité** : 25K+ requêtes/jour
- **Stockage** : ~20 KB par question

## 🌐 Déploiement

Recommandé : **Contabo VPS 20** (5,95€/mois)
- 6 vCPU, 12 GB RAM, 100 GB NVMe
- Parfait pour TTS + IA

## 📝 License

MIT License - Libre d'utilisation

## 👨‍💻 Auteur

Développé pour MeetVoice par sat94
