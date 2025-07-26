#!/bin/bash
# MeetVoice App - Script de démarrage propre
# ==========================================

set -e  # Arrêter en cas d'erreur

echo "🚀 Démarrage MeetVoice App avec Virtual Environment"
echo "=================================================="

# Vérifier que le virtual environment existe
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment non trouvé !"
    echo "💡 Créez-le avec: python3 -m venv venv"
    exit 1
fi

# Vérifier que le fichier .env existe
if [ ! -f ".env" ]; then
    echo "⚠️ Fichier .env non trouvé !"
    echo "💡 Créez-le avec vos variables d'environnement"
    exit 1
fi

# Activer le virtual environment
echo "📦 Activation du virtual environment..."
source venv/bin/activate

# Vérifier les dépendances
echo "🔍 Vérification des dépendances..."
pip check || {
    echo "⚠️ Problème de dépendances détecté"
    echo "💡 Réinstallez avec: pip install -r requirements.txt"
}

# Afficher les informations
echo "✅ Virtual environment activé"
echo "🐍 Python: $(python --version)"
echo "📦 Pip: $(pip --version)"
echo "📁 Working directory: $(pwd)"

# Démarrer l'application
echo "🌐 Démarrage de l'application..."
echo "🔗 URL: https://aaaazealmmmma.duckdns.org"
echo "📚 Documentation: https://aaaazealmmmma.duckdns.org/docs"
echo ""
echo "🛑 Pour arrêter: Ctrl+C"
echo "=================================================="

# Lancer avec uvicorn
python meetvoice_app_complete.py
