# Système de feedback pour améliorer les prompts
import json
import sqlite3
from datetime import datetime
from collections import defaultdict

class FeedbackSystem:
    def __init__(self, db_path="feedback_seduction.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données de feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                categorie TEXT,
                question TEXT,
                profil_utilisateur TEXT,
                reponse_ia TEXT,
                rating INTEGER,
                feedback_texte TEXT,
                prompt_utilise TEXT,
                amelioration_suggeree TEXT
            )
        ''')
        
        # Table des métriques de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metriques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                categorie TEXT,
                nb_interactions INTEGER,
                rating_moyen REAL,
                taux_satisfaction REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def enregistrer_interaction(self, categorie, question, profil_utilisateur, 
                              reponse_ia, rating, feedback_texte="", prompt_utilise=""):
        """Enregistre une interaction avec feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interactions 
            (timestamp, categorie, question, profil_utilisateur, reponse_ia, 
             rating, feedback_texte, prompt_utilise)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            categorie,
            question,
            profil_utilisateur or "",
            reponse_ia,
            rating,
            feedback_texte,
            prompt_utilise
        ))
        
        conn.commit()
        conn.close()
    
    def analyser_performance(self, categorie=None, jours=30):
        """Analyse la performance des prompts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Requête de base
        query = '''
            SELECT categorie, AVG(rating) as rating_moyen, COUNT(*) as nb_interactions,
                   SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as taux_satisfaction
            FROM interactions 
            WHERE datetime(timestamp) >= datetime('now', '-{} days')
        '''.format(jours)
        
        if categorie:
            query += f" AND categorie = '{categorie}'"
        
        query += " GROUP BY categorie ORDER BY rating_moyen DESC"
        
        cursor.execute(query)
        resultats = cursor.fetchall()
        
        conn.close()
        
        return [
            {
                "categorie": row[0],
                "rating_moyen": round(row[1], 2),
                "nb_interactions": row[2],
                "taux_satisfaction": round(row[3], 1)
            }
            for row in resultats
        ]
    
    def identifier_problemes(self, seuil_rating=3.0):
        """Identifie les prompts qui performent mal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT categorie, question, reponse_ia, rating, feedback_texte
            FROM interactions 
            WHERE rating < ? AND feedback_texte != ""
            ORDER BY rating ASC, timestamp DESC
            LIMIT 20
        ''', (seuil_rating,))
        
        problemes = cursor.fetchall()
        conn.close()
        
        return [
            {
                "categorie": row[0],
                "question": row[1],
                "reponse_ia": row[2],
                "rating": row[3],
                "feedback": row[4]
            }
            for row in problemes
        ]
    
    def generer_suggestions_amelioration(self):
        """Génère des suggestions d'amélioration basées sur les feedbacks"""
        problemes = self.identifier_problemes()
        
        suggestions = defaultdict(list)
        
        for probleme in problemes:
            categorie = probleme["categorie"]
            feedback = probleme["feedback"].lower()
            
            # Analyse des patterns de feedback
            if "trop long" in feedback or "verbeux" in feedback:
                suggestions[categorie].append("Raccourcir les réponses")
            
            if "pas assez concret" in feedback or "trop théorique" in feedback:
                suggestions[categorie].append("Ajouter plus d'exemples pratiques")
            
            if "pas personnalisé" in feedback or "générique" in feedback:
                suggestions[categorie].append("Mieux utiliser le profil utilisateur")
            
            if "ton inapproprié" in feedback or "trop formel" in feedback:
                suggestions[categorie].append("Ajuster le ton (plus décontracté)")
            
            if "manque d'empathie" in feedback:
                suggestions[categorie].append("Ajouter plus d'empathie et de compréhension")
        
        # Dédupliquer les suggestions
        suggestions_finales = {}
        for categorie, liste_suggestions in suggestions.items():
            suggestions_finales[categorie] = list(set(liste_suggestions))
        
        return suggestions_finales
    
    def optimiser_prompts(self, coach_seduction):
        """Optimise automatiquement les prompts basé sur les feedbacks"""
        suggestions = self.generer_suggestions_amelioration()
        
        prompts_optimises = {}
        
        for categorie, ameliorations in suggestions.items():
            if categorie in coach_seduction.prompts_specialises:
                prompt_original = coach_seduction.prompts_specialises[categorie]
                
                # Appliquer les améliorations
                prompt_optimise = prompt_original
                
                if "Raccourcir les réponses" in ameliorations:
                    prompt_optimise += "\n\nIMPORTANT: Sois concise et va droit au but. Maximum 3 paragraphes."
                
                if "Ajouter plus d'exemples pratiques" in ameliorations:
                    prompt_optimise += "\n\nIMPORTANT: Donne toujours des exemples concrets et applicables immédiatement."
                
                if "Mieux utiliser le profil utilisateur" in ameliorations:
                    prompt_optimise += "\n\nIMPORTANT: Personnalise ta réponse selon le profil mentionné. Fais des références directes."
                
                if "Ajuster le ton (plus décontracté)" in ameliorations:
                    prompt_optimise += "\n\nIMPORTANT: Utilise un ton amical et décontracté, comme une conversation entre amis."
                
                if "Ajouter plus d'empathie et de compréhension" in ameliorations:
                    prompt_optimise += "\n\nIMPORTANT: Montre de l'empathie et de la compréhension. Valide les émotions de l'utilisateur."
                
                prompts_optimises[categorie] = prompt_optimise
        
        return prompts_optimises
    
    def exporter_rapport(self, fichier="rapport_feedback.json"):
        """Exporte un rapport complet"""
        rapport = {
            "date_generation": datetime.now().isoformat(),
            "performance_globale": self.analyser_performance(),
            "problemes_identifies": self.identifier_problemes(),
            "suggestions_amelioration": self.generer_suggestions_amelioration()
        }
        
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        return rapport

# Interface de feedback pour les utilisateurs
class InterfaceFeedback:
    def __init__(self, feedback_system):
        self.feedback_system = feedback_system
    
    def collecter_feedback(self, categorie, question, profil_utilisateur, 
                          reponse_ia, prompt_utilise):
        """Interface pour collecter le feedback utilisateur"""
        print("\n" + "="*50)
        print("FEEDBACK - Comment trouvez-vous cette réponse ?")
        print("="*50)
        print(f"Question: {question}")
        print(f"Réponse de Sophie: {reponse_ia[:200]}...")
        print("\n")
        
        # Collecte du rating
        while True:
            try:
                rating = int(input("Notez cette réponse de 1 à 5 (5 = excellent): "))
                if 1 <= rating <= 5:
                    break
                else:
                    print("Veuillez entrer un nombre entre 1 et 5.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
        
        # Collecte du feedback textuel
        feedback_texte = input("Commentaires (optionnel): ").strip()
        
        # Enregistrement
        self.feedback_system.enregistrer_interaction(
            categorie, question, profil_utilisateur, reponse_ia,
            rating, feedback_texte, prompt_utilise
        )
        
        print("Merci pour votre feedback ! 🙏")
        return rating, feedback_texte

# Exemple d'utilisation complète
if __name__ == "__main__":
    # Initialisation
    feedback_sys = FeedbackSystem()
    interface = InterfaceFeedback(feedback_sys)
    
    # Simulation d'interactions avec feedback
    interactions_test = [
        {
            "categorie": "premier_message",
            "question": "Comment écrire à une fille qui aime la danse ?",
            "reponse": "Salut ! J'ai vu que tu aimais la danse. Moi aussi j'adore ça ! Tu danses quel style ?",
            "rating": 4,
            "feedback": "Bien mais un peu basique"
        },
        {
            "categorie": "conversation",
            "question": "Comment relancer une conversation qui s'essouffle ?",
            "reponse": "Tu peux poser une question ouverte sur ses passions ou partager une anecdote personnelle...",
            "rating": 2,
            "feedback": "Trop théorique, pas assez concret"
        }
    ]
    
    # Enregistrer les interactions test
    for interaction in interactions_test:
        feedback_sys.enregistrer_interaction(
            interaction["categorie"],
            interaction["question"],
            "",
            interaction["reponse"],
            interaction["rating"],
            interaction["feedback"]
        )
    
    # Analyser la performance
    print("Performance par catégorie:")
    performance = feedback_sys.analyser_performance()
    for perf in performance:
        print(f"- {perf['categorie']}: {perf['rating_moyen']}/5 ({perf['taux_satisfaction']}% satisfaction)")
    
    # Générer des suggestions
    print("\nSuggestions d'amélioration:")
    suggestions = feedback_sys.generer_suggestions_amelioration()
    for categorie, ameliorations in suggestions.items():
        print(f"- {categorie}: {', '.join(ameliorations)}")
