# Système RAG pour Coach de Séduction
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGSeduction:
    def __init__(self):
        # Base de connaissances sur la séduction
        self.base_connaissances = {
            "premier_contact": [
                {
                    "situation": "Premier message sur app de rencontre",
                    "conseil": "Personnalisez toujours votre message selon le profil. Mentionnez un détail spécifique de ses photos ou sa bio.",
                    "exemple": "J'ai vu que tu aimais la randonnée ! Quel est ton sentier préféré dans la région ?",
                    "tags": ["premier_message", "personnalisation", "app_rencontre"]
                },
                {
                    "situation": "Aborder quelqu'un en personne",
                    "conseil": "Commencez par un compliment sincère ou une observation sur le contexte. Soyez naturel.",
                    "exemple": "Excusez-moi, je ne pouvais pas m'empêcher de remarquer votre livre. Comment trouvez-vous cet auteur ?",
                    "tags": ["approche_directe", "compliment", "contexte"]
                }
            ],
            "conversation": [
                {
                    "situation": "Maintenir une conversation intéressante",
                    "conseil": "Utilisez la règle 70/30 : 70% d'écoute, 30% de partage. Posez des questions ouvertes.",
                    "exemple": "C'est fascinant ! Comment en êtes-vous venue à vous passionner pour ça ?",
                    "tags": ["ecoute_active", "questions_ouvertes", "equilibre"]
                },
                {
                    "situation": "Éviter les silences gênants",
                    "conseil": "Préparez des sujets de transition : FORD (Famille, Occupation, Récréation, Rêves).",
                    "exemple": "Au fait, qu'est-ce qui vous passionne le plus en ce moment ?",
                    "tags": ["transition", "FORD", "silence"]
                }
            ],
            "confiance": [
                {
                    "situation": "Manque de confiance en soi",
                    "conseil": "La confiance vient de l'acceptation de soi. Listez vos qualités et réussites passées.",
                    "exemple": "Chaque matin, rappelez-vous 3 choses dont vous êtes fier(e).",
                    "tags": ["estime_de_soi", "acceptation", "exercice_quotidien"]
                },
                {
                    "situation": "Peur du rejet",
                    "conseil": "Le rejet n'est pas personnel. C'est une incompatibilité, pas un jugement sur votre valeur.",
                    "exemple": "Si elle dit non, c'est qu'elle n'est pas la bonne personne pour vous.",
                    "tags": ["rejet", "mindset", "resilience"]
                }
            ],
            "rendez_vous": [
                {
                    "situation": "Choisir le lieu du premier rendez-vous",
                    "conseil": "Optez pour un lieu public, décontracté, qui permet la conversation. Évitez le cinéma.",
                    "exemple": "Un café cosy, une balade dans un parc, un marché local.",
                    "tags": ["lieu", "premier_rdv", "conversation"]
                },
                {
                    "situation": "Gérer le stress du premier rendez-vous",
                    "conseil": "Préparez quelques sujets de conversation mais restez flexible. L'objectif est de passer un bon moment.",
                    "exemple": "Respirez profondément et rappelez-vous : vous êtes là pour apprendre à connaître cette personne.",
                    "tags": ["stress", "preparation", "mindset"]
                }
            ]
        }
        
        # Créer l'index de recherche
        self.vectorizer = TfidfVectorizer(stop_words='french')
        self.creer_index()
    
    def creer_index(self):
        """Crée l'index de recherche pour le RAG"""
        self.documents = []
        self.metadonnees = []
        
        for categorie, conseils in self.base_connaissances.items():
            for conseil in conseils:
                # Combiner tous les textes pour la recherche
                texte_complet = f"{conseil['situation']} {conseil['conseil']} {' '.join(conseil['tags'])}"
                self.documents.append(texte_complet)
                self.metadonnees.append({
                    "categorie": categorie,
                    "conseil": conseil,
                    "score": 0
                })
        
        # Créer la matrice TF-IDF
        self.matrice_tfidf = self.vectorizer.fit_transform(self.documents)
    
    def rechercher_conseils(self, question, top_k=3):
        """Recherche les conseils les plus pertinents"""
        # Vectoriser la question
        question_vec = self.vectorizer.transform([question])
        
        # Calculer la similarité cosinus
        similarities = cosine_similarity(question_vec, self.matrice_tfidf).flatten()
        
        # Récupérer les top_k résultats
        indices_top = np.argsort(similarities)[::-1][:top_k]
        
        conseils_pertinents = []
        for idx in indices_top:
            if similarities[idx] > 0.1:  # Seuil de pertinence
                conseil = self.metadonnees[idx].copy()
                conseil["score"] = similarities[idx]
                conseils_pertinents.append(conseil)
        
        return conseils_pertinents
    
    def generer_contexte_rag(self, question):
        """Génère le contexte enrichi pour le prompt"""
        conseils_pertinents = self.rechercher_conseils(question)
        
        if not conseils_pertinents:
            return ""
        
        contexte = "\n\nConseils pertinents de ma base de connaissances:\n"
        
        for i, conseil in enumerate(conseils_pertinents, 1):
            contexte += f"""
{i}. Situation: {conseil['conseil']['situation']}
   Conseil: {conseil['conseil']['conseil']}
   Exemple: {conseil['conseil']['exemple']}
"""
        
        contexte += "\nUtilise ces informations pour enrichir ta réponse, mais adapte-les à la situation spécifique de l'utilisateur.\n"
        
        return contexte
    
    def ajouter_conseil(self, categorie, situation, conseil, exemple, tags):
        """Ajoute un nouveau conseil à la base de connaissances"""
        nouveau_conseil = {
            "situation": situation,
            "conseil": conseil,
            "exemple": exemple,
            "tags": tags
        }
        
        if categorie not in self.base_connaissances:
            self.base_connaissances[categorie] = []
        
        self.base_connaissances[categorie].append(nouveau_conseil)
        
        # Recréer l'index
        self.creer_index()
    
    def sauvegarder_base(self, fichier="base_connaissances_seduction.json"):
        """Sauvegarde la base de connaissances"""
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(self.base_connaissances, f, ensure_ascii=False, indent=2)
    
    def charger_base(self, fichier="base_connaissances_seduction.json"):
        """Charge la base de connaissances depuis un fichier"""
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                self.base_connaissances = json.load(f)
            self.creer_index()
            return True
        except FileNotFoundError:
            print(f"Fichier {fichier} non trouvé. Utilisation de la base par défaut.")
            return False

# Intégration avec le coach de séduction
class CoachSeductionRAG:
    def __init__(self, deepinfra_key="vUn0KAjMKPENsoI6AKCPsfXdpcYqZquJ"):
        self.coach = CoachSeduction(deepinfra_key)
        self.rag = RAGSeduction()
    
    def generer_conseil_enrichi(self, categorie, question_utilisateur, profil_utilisateur=None):
        """Génère un conseil enrichi avec RAG"""
        
        # Récupérer le contexte RAG
        contexte_rag = self.rag.generer_contexte_rag(question_utilisateur)
        
        # Modifier le prompt pour inclure le contexte RAG
        prompt_base = self.coach.prompts_specialises.get(categorie, self.coach.prompts_specialises["conversation"])
        prompt_enrichi = prompt_base + contexte_rag
        
        # Temporairement modifier le prompt
        self.coach.prompts_specialises[f"{categorie}_temp"] = prompt_enrichi
        
        # Générer le conseil
        conseil = self.coach.generer_conseil(f"{categorie}_temp", question_utilisateur, profil_utilisateur)
        
        # Nettoyer le prompt temporaire
        del self.coach.prompts_specialises[f"{categorie}_temp"]
        
        return conseil

# Exemple d'utilisation
if __name__ == "__main__":
    # Test du système RAG
    rag = RAGSeduction()
    
    question = "Comment aborder une fille dans un café ?"
    conseils = rag.rechercher_conseils(question)
    
    print("Conseils trouvés:")
    for conseil in conseils:
        print(f"- {conseil['conseil']['conseil']}")
        print(f"  Exemple: {conseil['conseil']['exemple']}")
        print(f"  Score: {conseil['score']:.3f}\n")
    
    # Test du coach enrichi
    coach_rag = CoachSeductionRAG()
    conseil_enrichi = coach_rag.generer_conseil_enrichi(
        "premier_contact",
        "Comment aborder une fille qui lit dans un café ?",
        "Je suis timide mais j'aime lire aussi"
    )
    
    print("Conseil enrichi de Sophie:")
    print(conseil_enrichi["texte"])
