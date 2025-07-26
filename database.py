#!/usr/bin/env python3
"""
Module de gestion de la base de données PostgreSQL
Connexion, modèles et opérations CRUD pour l'API MeetVoice
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base SQLAlchemy
Base = declarative_base()

class DatabaseManager:
    """Gestionnaire de base de données PostgreSQL"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL non configurée dans .env")
        
        self.engine = None
        self.SessionLocal = None
        self.init_database()
    
    def init_database(self):
        """Initialise la connexion à la base de données"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False  # Mettre à True pour debug SQL
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Créer les tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Base de données initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur initialisation base de données: {e}")
            raise
    
    def get_session(self) -> Session:
        """Retourne une session de base de données"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test la connexion à la base de données"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Test connexion échoué: {e}")
            return False

# Modèles de données
class ConversationLog(Base):
    """Table des logs de conversations IA"""
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(100), index=True)  # Identifiant utilisateur (optionnel)
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text)
    response = Column(Text, nullable=False)
    provider = Column(String(50))  # "gemini", "deepinfra"
    fallback_used = Column(Boolean, default=False)
    processing_time = Column(Float)
    cost = Column(Float, default=0.0)
    voice_settings = Column(JSON)  # Paramètres TTS utilisés
    audio_generated = Column(Boolean, default=False)
    rating = Column(Integer)  # Note utilisateur (1-5)
    feedback = Column(Text)  # Commentaire utilisateur

class UserProfile(Base):
    """Table des profils utilisateurs - Compatible avec Django Compte"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    # UUID compatible avec Django
    django_user_id = Column(String(36), unique=True, index=True, nullable=True)  # UUID Django
    user_id = Column(String(100), unique=True, index=True, nullable=False)  # Identifiant simple
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(250), nullable=True)
    nom = Column(String(250), nullable=True)
    prenom = Column(String(250), nullable=True)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date_joined = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    date_de_naissance = Column(DateTime, nullable=True)

    # Informations personnelles (compatibles Django)
    phone = Column(String(15), nullable=True)
    sexe = Column(String(30), nullable=True)
    taille = Column(Integer, nullable=True)
    poids = Column(String(3), nullable=True)
    ethnique = Column(String(30), nullable=True)
    religion = Column(String(30), nullable=True)
    yeux = Column(String(30), nullable=True)
    silhouette = Column(String(30), nullable=True)
    situation = Column(String(30), nullable=True)
    hair_color = Column(String(30), nullable=True)
    hair_style = Column(String(30), nullable=True)
    glasses = Column(String(30), nullable=True)
    facial_hair = Column(String(30), nullable=True)
    bio = Column(Text, nullable=True)

    # Adresse
    adresse = Column(String(200), nullable=True)
    ville = Column(String(100), nullable=True)
    departement = Column(String(100), nullable=True)
    pays = Column(String(100), nullable=True)
    code_postal = Column(String(10), nullable=True)

    # Statistiques
    vues = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    matches = Column(Integer, default=0)

    # Spécifique à l'IA
    conversation_count = Column(Integer, default=0)
    last_interaction = Column(DateTime)
    favorite_voice = Column(String(200))
    ai_preferences = Column(JSON)  # Préférences IA spécifiques
    voice_settings = Column(JSON)  # Paramètres TTS préférés
    coaching_level = Column(String(50), default="beginner")  # Niveau de coaching
    topics_of_interest = Column(JSON)  # Sujets d'intérêt pour l'IA

class FeedbackEntry(Base):
    """Table des feedbacks utilisateurs"""
    __tablename__ = "feedback_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    conversation_id = Column(Integer, index=True)  # Référence à ConversationLog
    user_id = Column(String(100), index=True)
    category = Column(String(50))  # "coaching", "technique", "general"
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    improvement_suggestion = Column(Text)
    resolved = Column(Boolean, default=False)

class SystemMetrics(Base):
    """Table des métriques système"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # "ms", "count", "percent", etc.
    additional_data = Column(JSON)

class AISession(Base):
    """Table des sessions IA pour tracking avancé"""
    __tablename__ = "ai_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=True)
    django_user_id = Column(String(36), index=True, nullable=True)  # UUID Django
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_conversations = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    session_type = Column(String(50), default="coaching")  # "coaching", "casual", "support"
    user_satisfaction = Column(Integer, nullable=True)  # Note globale de session
    session_notes = Column(Text, nullable=True)

class CoachingProgress(Base):
    """Table pour suivre les progrès de coaching"""
    __tablename__ = "coaching_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    django_user_id = Column(String(36), index=True, nullable=True)
    topic = Column(String(100), nullable=False)  # "approach", "conversation", "confidence"
    level_before = Column(Integer, default=1)  # Niveau avant (1-10)
    level_after = Column(Integer, nullable=True)  # Niveau après
    session_count = Column(Integer, default=0)
    last_practice = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    goals = Column(JSON, nullable=True)  # Objectifs spécifiques
    achievements = Column(JSON, nullable=True)  # Réalisations

# Services de base de données
class DatabaseService:
    """Service pour les opérations de base de données"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def log_conversation(self, 
                        prompt: str,
                        response: str,
                        provider: str,
                        processing_time: float,
                        user_id: Optional[str] = None,
                        system_prompt: Optional[str] = None,
                        fallback_used: bool = False,
                        cost: float = 0.0,
                        voice_settings: Optional[Dict] = None,
                        audio_generated: bool = False) -> int:
        """Enregistre une conversation dans la base de données"""
        try:
            with self.db_manager.get_session() as session:
                log_entry = ConversationLog(
                    user_id=user_id,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response=response,
                    provider=provider,
                    fallback_used=fallback_used,
                    processing_time=processing_time,
                    cost=cost,
                    voice_settings=voice_settings or {},
                    audio_generated=audio_generated
                )
                session.add(log_entry)
                session.commit()
                session.refresh(log_entry)
                return log_entry.id
        except Exception as e:
            logger.error(f"Erreur enregistrement conversation: {e}")
            return -1
    
    def add_feedback(self,
                    conversation_id: int,
                    rating: int,
                    user_id: Optional[str] = None,
                    category: str = "general",
                    comment: Optional[str] = None,
                    improvement_suggestion: Optional[str] = None) -> bool:
        """Ajoute un feedback utilisateur"""
        try:
            with self.db_manager.get_session() as session:
                feedback = FeedbackEntry(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    category=category,
                    rating=rating,
                    comment=comment,
                    improvement_suggestion=improvement_suggestion
                )
                session.add(feedback)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Erreur ajout feedback: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'un utilisateur"""
        try:
            with self.db_manager.get_session() as session:
                # Nombre de conversations
                conv_count = session.query(ConversationLog).filter(
                    ConversationLog.user_id == user_id
                ).count()
                
                # Dernière interaction
                last_conv = session.query(ConversationLog).filter(
                    ConversationLog.user_id == user_id
                ).order_by(ConversationLog.timestamp.desc()).first()
                
                # Rating moyen
                avg_rating = session.query(FeedbackEntry).filter(
                    FeedbackEntry.user_id == user_id
                ).with_entities(FeedbackEntry.rating).all()
                
                avg_rating_value = sum([r[0] for r in avg_rating]) / len(avg_rating) if avg_rating else 0
                
                return {
                    "conversation_count": conv_count,
                    "last_interaction": last_conv.timestamp if last_conv else None,
                    "average_rating": round(avg_rating_value, 2),
                    "total_feedbacks": len(avg_rating)
                }
        except Exception as e:
            logger.error(f"Erreur récupération stats utilisateur: {e}")
            return {}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques système"""
        try:
            with self.db_manager.get_session() as session:
                # Total conversations
                total_conversations = session.query(ConversationLog).count()

                # Conversations par provider
                gemini_count = session.query(ConversationLog).filter(
                    ConversationLog.provider == "gemini"
                ).count()

                deepinfra_count = session.query(ConversationLog).filter(
                    ConversationLog.provider == "deepinfra"
                ).count()

                # Fallback rate
                fallback_count = session.query(ConversationLog).filter(
                    ConversationLog.fallback_used == True
                ).count()

                fallback_rate = (fallback_count / total_conversations * 100) if total_conversations > 0 else 0

                # Rating moyen global
                all_ratings = session.query(FeedbackEntry.rating).all()
                avg_rating = sum([r[0] for r in all_ratings]) / len(all_ratings) if all_ratings else 0

                return {
                    "total_conversations": total_conversations,
                    "gemini_usage": gemini_count,
                    "deepinfra_usage": deepinfra_count,
                    "fallback_rate": round(fallback_rate, 2),
                    "average_rating": round(avg_rating, 2),
                    "total_feedbacks": len(all_ratings)
                }
        except Exception as e:
            logger.error(f"Erreur récupération stats système: {e}")
            return {}

    def sync_django_user(self, django_user_data: Dict[str, Any]) -> bool:
        """Synchronise un utilisateur Django avec le profil IA"""
        try:
            with self.db_manager.get_session() as session:
                # Chercher un profil existant
                profile = session.query(UserProfile).filter(
                    UserProfile.django_user_id == django_user_data.get('id')
                ).first()

                if not profile:
                    # Créer un nouveau profil
                    profile = UserProfile(
                        django_user_id=str(django_user_data.get('id')),
                        user_id=django_user_data.get('email', f"user_{django_user_data.get('id')}"),
                        email=django_user_data.get('email'),
                        username=django_user_data.get('username'),
                        nom=django_user_data.get('nom'),
                        prenom=django_user_data.get('prenom'),
                        date_joined=django_user_data.get('date_joined'),
                        date_de_naissance=django_user_data.get('date_de_naissance'),
                        phone=django_user_data.get('numberPhone'),
                        sexe=django_user_data.get('sexe'),
                        taille=django_user_data.get('taille'),
                        poids=django_user_data.get('poids'),
                        ethnique=django_user_data.get('ethnique'),
                        religion=django_user_data.get('religion'),
                        yeux=django_user_data.get('yeux'),
                        silhouette=django_user_data.get('shillouette'),
                        situation=django_user_data.get('situation'),
                        hair_color=django_user_data.get('hair_color'),
                        hair_style=django_user_data.get('hair_style'),
                        glasses=django_user_data.get('glasses'),
                        facial_hair=django_user_data.get('facial_hair'),
                        bio=django_user_data.get('bio'),
                        adresse=django_user_data.get('adresse'),
                        ville=django_user_data.get('ville'),
                        departement=django_user_data.get('departement'),
                        pays=django_user_data.get('pays'),
                        code_postal=django_user_data.get('code_postal'),
                        vues=django_user_data.get('vues', 0),
                        likes=django_user_data.get('likes', 0),
                        matches=django_user_data.get('matches', 0)
                    )
                    session.add(profile)
                else:
                    # Mettre à jour le profil existant
                    for key, value in django_user_data.items():
                        if hasattr(profile, key) and value is not None:
                            setattr(profile, key, value)
                    profile.updated_at = datetime.utcnow()

                session.commit()
                return True

        except Exception as e:
            logger.error(f"Erreur synchronisation utilisateur Django: {e}")
            return False

    def get_user_coaching_progress(self, user_id: str, django_user_id: str = None) -> Dict[str, Any]:
        """Récupère les progrès de coaching d'un utilisateur"""
        try:
            with self.db_manager.get_session() as session:
                # Construire la requête
                query = session.query(CoachingProgress)
                if django_user_id:
                    query = query.filter(CoachingProgress.django_user_id == django_user_id)
                else:
                    query = query.filter(CoachingProgress.user_id == user_id)

                progress_entries = query.all()

                progress_by_topic = {}
                for entry in progress_entries:
                    progress_by_topic[entry.topic] = {
                        "level_before": entry.level_before,
                        "level_after": entry.level_after,
                        "session_count": entry.session_count,
                        "last_practice": entry.last_practice,
                        "goals": entry.goals or {},
                        "achievements": entry.achievements or {}
                    }

                return progress_by_topic

        except Exception as e:
            logger.error(f"Erreur récupération progrès coaching: {e}")
            return {}

    def update_coaching_progress(self, user_id: str, topic: str, new_level: int,
                               django_user_id: str = None, notes: str = None) -> bool:
        """Met à jour les progrès de coaching"""
        try:
            with self.db_manager.get_session() as session:
                # Chercher un progrès existant
                query = session.query(CoachingProgress).filter(
                    CoachingProgress.topic == topic
                )

                if django_user_id:
                    query = query.filter(CoachingProgress.django_user_id == django_user_id)
                else:
                    query = query.filter(CoachingProgress.user_id == user_id)

                progress = query.first()

                if not progress:
                    # Créer un nouveau progrès
                    progress = CoachingProgress(
                        user_id=user_id,
                        django_user_id=django_user_id,
                        topic=topic,
                        level_before=1,
                        level_after=new_level,
                        session_count=1,
                        notes=notes
                    )
                    session.add(progress)
                else:
                    # Mettre à jour
                    progress.level_after = new_level
                    progress.session_count += 1
                    progress.last_practice = datetime.utcnow()
                    if notes:
                        progress.notes = notes

                session.commit()
                return True

        except Exception as e:
            logger.error(f"Erreur mise à jour progrès coaching: {e}")
            return False

# Instance globale
db_manager = DatabaseManager()
db_service = DatabaseService(db_manager)

def get_database_service() -> DatabaseService:
    """Retourne le service de base de données"""
    return db_service
