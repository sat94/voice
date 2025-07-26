#!/usr/bin/env python3
"""
Script pour consulter les conversations enregistrées en base de données
"""

from database import get_database_service
from datetime import datetime, timedelta

def consulter_conversations():
    """Affiche les conversations récentes"""
    
    print("📊 CONSULTATION DES CONVERSATIONS ENREGISTRÉES")
    print("=" * 60)
    
    try:
        db_service = get_database_service()
        
        # Récupérer les conversations récentes (dernières 24h)
        conversations = db_service.get_recent_conversations(limit=20)
        
        if not conversations:
            print("❌ Aucune conversation trouvée")
            return
        
        print(f"✅ {len(conversations)} conversations trouvées\n")
        
        for i, conv in enumerate(conversations, 1):
            print(f"🔹 CONVERSATION #{conv['id']} ({i}/{len(conversations)})")
            print(f"   📅 Date: {conv['timestamp']}")
            print(f"   👤 User: {conv['user_id'] or 'Anonyme'}")
            print(f"   🤖 Provider: {conv['provider']}")
            print(f"   ⏱️ Temps: {conv['processing_time']:.3f}s")
            print(f"   💰 Coût: ${conv['cost']:.4f}")
            print(f"   🎤 Audio: {'✅' if conv['audio_generated'] else '❌'}")
            
            # Prompt (tronqué)
            prompt = conv['prompt'][:100] + "..." if len(conv['prompt']) > 100 else conv['prompt']
            print(f"   📝 Prompt: {prompt}")
            
            # Réponse (tronquée)
            response = conv['response'][:150] + "..." if len(conv['response']) > 150 else conv['response']
            print(f"   💬 Réponse: {response}")
            
            if conv['rating']:
                print(f"   ⭐ Note: {conv['rating']}/5")
            
            print("-" * 50)
        
        # Statistiques globales
        print("\n📈 STATISTIQUES GLOBALES:")
        stats = db_service.get_system_stats()
        
        print(f"   📊 Total conversations: {stats.get('total_conversations', 0)}")
        print(f"   👥 Utilisateurs uniques: {stats.get('unique_users', 0)}")
        print(f"   🤖 Provider principal: {stats.get('main_provider', 'N/A')}")
        print(f"   ⏱️ Temps moyen: {stats.get('avg_processing_time', 0):.3f}s")
        print(f"   💰 Coût total: ${stats.get('total_cost', 0):.4f}")
        print(f"   ⭐ Note moyenne: {stats.get('avg_rating', 0):.1f}/5")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def consulter_par_utilisateur(user_id: str):
    """Affiche les conversations d'un utilisateur spécifique"""
    
    print(f"👤 CONVERSATIONS DE L'UTILISATEUR: {user_id}")
    print("=" * 60)
    
    try:
        db_service = get_database_service()
        conversations = db_service.get_user_conversations(user_id, limit=10)
        
        if not conversations:
            print(f"❌ Aucune conversation trouvée pour {user_id}")
            return
        
        print(f"✅ {len(conversations)} conversations trouvées\n")
        
        for i, conv in enumerate(conversations, 1):
            print(f"🔹 CONVERSATION #{conv['id']}")
            print(f"   📅 {conv['timestamp']}")
            print(f"   🤖 {conv['provider']} ({conv['processing_time']:.3f}s)")
            print(f"   📝 {conv['prompt'][:80]}...")
            print(f"   💬 {conv['response'][:100]}...")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def consulter_par_type(provider: str):
    """Affiche les conversations par type de provider"""
    
    print(f"🤖 CONVERSATIONS DU PROVIDER: {provider}")
    print("=" * 60)
    
    try:
        db_service = get_database_service()
        conversations = db_service.get_conversations_by_provider(provider, limit=15)
        
        if not conversations:
            print(f"❌ Aucune conversation trouvée pour {provider}")
            return
        
        print(f"✅ {len(conversations)} conversations trouvées\n")
        
        for conv in conversations:
            print(f"🔹 #{conv['id']} - {conv['timestamp']}")
            print(f"   👤 {conv['user_id'] or 'Anonyme'}")
            print(f"   📝 {conv['prompt'][:60]}...")
            print(f"   ⏱️ {conv['processing_time']:.3f}s")
            print()
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--user" and len(sys.argv) > 2:
            consulter_par_utilisateur(sys.argv[2])
        elif sys.argv[1] == "--provider" and len(sys.argv) > 2:
            consulter_par_type(sys.argv[2])
        else:
            print("Usage:")
            print("  python3 consulter_conversations.py                    # Toutes les conversations")
            print("  python3 consulter_conversations.py --user USER_ID    # Par utilisateur")
            print("  python3 consulter_conversations.py --provider gemini # Par provider")
    else:
        consulter_conversations()
