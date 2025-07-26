#!/usr/bin/env python3
"""
Script simple pour voir les conversations en base
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def voir_conversations():
    """Affiche les conversations directement depuis la DB"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non configurée")
        return
    
    try:
        engine = create_engine(database_url)
        
        print("📊 CONVERSATIONS ENREGISTRÉES")
        print("=" * 80)
        
        # Requête pour récupérer les conversations récentes
        query = text("""
            SELECT 
                id,
                timestamp,
                user_id,
                prompt,
                response,
                provider,
                processing_time,
                cost,
                audio_generated,
                rating
            FROM conversation_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            conversations = result.fetchall()
        
        if not conversations:
            print("❌ Aucune conversation trouvée")
            return
        
        print(f"✅ {len(conversations)} conversations récentes:\n")
        
        for i, conv in enumerate(conversations, 1):
            print(f"🔹 CONVERSATION #{conv.id} ({i}/{len(conversations)})")
            print(f"   📅 Date: {conv.timestamp}")
            print(f"   👤 User: {conv.user_id or 'Anonyme'}")
            print(f"   🤖 Provider: {conv.provider}")
            print(f"   ⏱️ Temps: {conv.processing_time:.3f}s" if conv.processing_time else "⏱️ Temps: N/A")
            print(f"   💰 Coût: ${conv.cost:.4f}" if conv.cost else "💰 Coût: $0.0000")
            print(f"   🎤 Audio: {'✅' if conv.audio_generated else '❌'}")
            
            # Prompt (tronqué)
            prompt = conv.prompt[:80] + "..." if len(conv.prompt) > 80 else conv.prompt
            print(f"   📝 Prompt: {prompt}")
            
            # Réponse (tronquée)
            response = conv.response[:100] + "..." if len(conv.response) > 100 else conv.response
            print(f"   💬 Réponse: {response}")
            
            if conv.rating:
                print(f"   ⭐ Note: {conv.rating}/5")
            
            print("-" * 60)
        
        # Statistiques rapides
        print("\n📈 STATISTIQUES RAPIDES:")
        
        stats_query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT user_id) as users_uniques,
                AVG(processing_time) as temps_moyen,
                SUM(cost) as cout_total,
                AVG(rating) as note_moyenne,
                provider,
                COUNT(*) as count_provider
            FROM conversation_logs 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY provider
            ORDER BY count_provider DESC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(stats_query)
            stats = result.fetchall()
        
        for stat in stats:
            print(f"   🤖 {stat.provider}: {stat.count_provider} conversations")
            print(f"      ⏱️ Temps moyen: {stat.temps_moyen:.3f}s" if stat.temps_moyen else "      ⏱️ Temps moyen: N/A")
            print(f"      💰 Coût: ${stat.cout_total:.4f}" if stat.cout_total else "      💰 Coût: $0.0000")
            if stat.note_moyenne:
                print(f"      ⭐ Note: {stat.note_moyenne:.1f}/5")
            print()
        
        # Total global
        total_query = text("SELECT COUNT(*) as total FROM conversation_logs")
        with engine.connect() as conn:
            result = conn.execute(total_query)
            total = result.fetchone()
        
        print(f"📊 TOTAL GLOBAL: {total.total} conversations enregistrées")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    voir_conversations()
