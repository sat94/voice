#!/bin/bash
# Script pour diagnostiquer et corriger le problème CORS

echo "🔍 DIAGNOSTIC CORS MEETVOICE"
echo "================================"

# 1. Vérifier si l'API tourne
echo "1. Test API directe (port 8001)..."
if curl -s http://localhost:8001/ > /dev/null; then
    echo "✅ API sur port 8001 : OK"
else
    echo "❌ API sur port 8001 : NON ACCESSIBLE"
    echo "   Démarrez l'API avec: python3 main.py"
fi

# 2. Tester les headers CORS direct
echo ""
echo "2. Headers CORS API directe..."
curl -s -I -H "Origin: http://localhost:8083" http://localhost:8001/inscription/question/1 | grep -i "access-control"

# 3. Tester les headers CORS via Nginx
echo ""
echo "3. Headers CORS via Nginx..."
curl -s -I -H "Origin: http://localhost:8083" https://aaaazealmmmma.duckdns.org/inscription/question/1 | grep -i "access-control"

# 4. Compter les headers Access-Control-Allow-Origin
echo ""
echo "4. Nombre de headers Access-Control-Allow-Origin via Nginx..."
count=$(curl -s -I https://aaaazealmmmma.duckdns.org/inscription/question/1 | grep -c "Access-Control-Allow-Origin")
echo "   Nombre trouvé: $count"
if [ "$count" -gt 1 ]; then
    echo "   ❌ PROBLÈME: Plus d'un header trouvé!"
else
    echo "   ✅ OK: Un seul header"
fi

# 5. Vérifier la config Nginx
echo ""
echo "5. Vérification config Nginx..."
if grep -q "add_header Access-Control-Allow-Origin" /etc/nginx/sites-available/meetvoice-tts 2>/dev/null; then
    echo "   ❌ PROBLÈME: Headers CORS encore dans Nginx"
    echo "   Solution: Supprimer les lignes add_header Access-Control dans Nginx"
elif grep -q "add_header Access-Control-Allow-Origin" meetvoice-tts.nginx.conf 2>/dev/null; then
    echo "   ❌ PROBLÈME: Headers CORS dans le fichier local meetvoice-tts.nginx.conf"
    echo "   Solution: Copier le fichier corrigé vers Nginx"
else
    echo "   ✅ OK: Pas de headers CORS dans Nginx"
fi

# 6. Proposer des solutions
echo ""
echo "🛠️ SOLUTIONS PROPOSÉES:"
echo "================================"

echo "A. Redémarrer les services:"
echo "   sudo systemctl reload nginx"
echo "   # Arrêter main.py et relancer: python3 main.py"

echo ""
echo "B. Copier la config Nginx corrigée:"
echo "   sudo cp meetvoice-tts.nginx.conf /etc/nginx/sites-available/meetvoice-tts"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"

echo ""
echo "C. Test temporaire sans Nginx:"
echo "   Dans Vue.js, utiliser: https://aaaazealmmmma.duckdns.org:8001/inscription/question/1"

echo ""
echo "D. Vérifier les processus:"
echo "   ps aux | grep python"
echo "   ps aux | grep nginx"

# 7. Test final
echo ""
echo "🧪 TEST FINAL:"
echo "================================"
echo "Testez cette URL dans votre navigateur:"
echo "https://aaaazealmmmma.duckdns.org/inscription/question/1"
echo ""
echo "Et cette URL directe:"
echo "https://aaaazealmmmma.duckdns.org:8001/inscription/question/1"
echo ""
echo "Si la deuxième marche mais pas la première, le problème vient de Nginx."
