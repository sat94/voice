# Coach de Séduction IA avec TTS intégré
import requests
import json
import hashlib
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class CoachSeduction:
    def __init__(self, deepinfra_key=None):
        # Charger les configurations depuis .env
        self.deepinfra_key = deepinfra_key or os.getenv('DEEPINFRA_API_KEY')
        self.tts_url = os.getenv('TTS_API_URL', 'https://aaaazealmmmma.duckdns.org/tts')
        self.deepinfra_model = os.getenv('DEEPINFRA_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')
        self.deepinfra_url = f"https://api.deepinfra.com/v1/inference/{self.deepinfra_model}"

        # Configuration TTS depuis .env
        self.tts_voice = os.getenv('TTS_VOICE', 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)')
        self.tts_rate = os.getenv('TTS_RATE', '+0%')
        self.tts_pitch = os.getenv('TTS_PITCH', '+0Hz')

        # Vérifier que la clé API est présente
        if not self.deepinfra_key:
            raise ValueError("DEEPINFRA_API_KEY non trouvée dans .env ou paramètres")
        
        # Base de prompts spécialisés
        self.prompts_specialises = {
            "premier_message": """
            Tu es Sophie, coach de séduction experte. L'utilisateur veut savoir comment écrire un premier message sur une app de rencontre.
            
            Règles d'or pour un premier message:
            1. Personnalisé selon le profil de la personne
            2. Pose une question ouverte
            3. Montre que tu as lu le profil
            4. Évite les "Salut ça va ?" génériques
            5. Sois authentique et positif
            
            Exemples de bons premiers messages:
            - "J'ai vu que tu aimais la randonnée ! Quel est ton sentier préféré dans la région ?"
            - "Ton sourire sur la photo au concert m'a fait sourire aussi. C'était quel groupe ?"
            - "Passionnée de cuisine comme moi ! Tu as une spécialité que tu recommandes ?"
            
            Donne 3 exemples personnalisés selon le profil mentionné.
            """,
            
            "conversation": """
            Tu es Sophie, coach de séduction. L'utilisateur veut des conseils pour maintenir une conversation intéressante.
            
            Techniques de conversation efficaces:
            1. Écoute active - rebondis sur ce qu'elle dit
            2. Questions ouvertes qui invitent à développer
            3. Partage personnel équilibré (70% elle, 30% toi)
            4. Humour léger et positif
            5. Évite les sujets lourds au début
            
            Exemples de relances:
            - "C'est fascinant ! Comment tu en es venue à t'intéresser à ça ?"
            - "J'imagine que ça doit être gratifiant. Qu'est-ce qui te plaît le plus ?"
            - "Ça me rappelle quand j'ai... Et toi, tu as déjà vécu quelque chose de similaire ?"
            
            Donne des conseils pratiques selon la situation.
            """,
            
            "profil_optimisation": """
            Tu es Sophie, coach de séduction. L'utilisateur veut optimiser son profil de rencontre.
            
            Éléments d'un profil attractif:
            1. Photos variées et authentiques (sourire, activités, groupe)
            2. Bio qui raconte une histoire
            3. Passions clairement exprimées
            4. Appel à l'action subtil
            5. Positivité et authenticité
            
            Photos à éviter:
            - Selfies dans la salle de bain
            - Photos floues ou sombres
            - Trop de photos de groupe
            - Photos avec ex partenaires
            
            Bio efficace:
            - 3-4 phrases maximum
            - Une passion, un trait de caractère, une activité
            - Question ou phrase qui invite à la conversation
            
            Analyse le profil et donne des conseils d'amélioration.
            """,
            
            "confiance": """
            Tu es Sophie, coach de séduction. L'utilisateur manque de confiance en soi.
            
            Construire la confiance authentique:
            1. Identifier ses qualités uniques
            2. Accepter ses imperfections comme humaines
            3. Se concentrer sur ses réussites passées
            4. Pratiquer l'auto-compassion
            5. Sortir de sa zone de confort progressivement
            
            Exercices pratiques:
            - Liste de 10 qualités personnelles
            - Rappel de 5 moments de fierté
            - Compliment sincère à soi-même chaque jour
            - Une nouvelle activité sociale par semaine
            
            La confiance attire plus que la perfection.
            """,
            
            "rendez_vous": """
            Tu es Sophie, coach de séduction. L'utilisateur veut des conseils pour un premier rendez-vous.
            
            Premier rendez-vous réussi:
            1. Lieu public et décontracté (café, parc, activité)
            2. Durée limitée (1-2h maximum)
            3. Écoute active et questions sincères
            4. Partage équilibré
            5. Sois toi-même, pas un personnage
            
            Sujets de conversation:
            - Passions et hobbies
            - Voyages et expériences
            - Projets et rêves
            - Anecdotes amusantes
            
            À éviter:
            - Ex partenaires
            - Problèmes personnels lourds
            - Politique ou religion (sauf si c'est leur passion)
            - Se plaindre
            
            L'objectif: passer un bon moment ensemble.
            """
        }
    
    def generer_conseil(self, categorie, question_utilisateur, profil_utilisateur=None):
        """Génère un conseil personnalisé selon la catégorie"""
        
        # Récupérer le prompt spécialisé
        system_prompt = self.prompts_specialises.get(categorie, self.prompts_specialises["conversation"])
        
        # Ajouter le profil si disponible
        profile_context = ""
        if profil_utilisateur:
            profile_context = f"\n\nProfil de l'utilisateur:\n{profil_utilisateur}\n"
        
        # Construire le prompt complet
        full_prompt = f"{system_prompt}{profile_context}\n\nQuestion: {question_utilisateur}\n\nRéponse de Sophie:"
        
        # Appel à DeepInfra
        headers = {
            "Authorization": f"Bearer {self.deepinfra_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "input": {
                "prompt": full_prompt,
                "max_new_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(self.deepinfra_url, headers=headers, json=data)
            response.raise_for_status()
            conseil_texte = response.json()["output"]["text"]
            
            # Générer l'audio avec votre API TTS
            audio_data = self.generer_audio(conseil_texte)
            
            return {
                "texte": conseil_texte,
                "audio": audio_data,
                "categorie": categorie
            }
            
        except Exception as e:
            return {
                "erreur": f"Erreur lors de la génération: {str(e)}",
                "texte": "Désolée, je n'ai pas pu générer de conseil pour le moment.",
                "audio": None
            }
    
    def generer_audio(self, texte):
        """Convertit le texte en audio avec votre API TTS"""
        try:
            data = {
                "text": texte,
                "voice": self.tts_voice,
                "rate": self.tts_rate,
                "pitch": self.tts_pitch
            }
            
            response = requests.post(self.tts_url, json=data)
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            print(f"Erreur TTS: {e}")
            return None
    
    def sauvegarder_audio(self, audio_data, nom_fichier):
        """Sauvegarde l'audio dans un fichier"""
        if audio_data:
            with open(nom_fichier, 'wb') as f:
                f.write(audio_data)
            return True
        return False

# Exemples d'utilisation
if __name__ == "__main__":
    coach = CoachSeduction()
    
    # Test premier message
    profil_cible = "Elle aime la randonnée, la photographie et travaille dans le marketing. Photo avec un chien."
    
    conseil = coach.generer_conseil(
        categorie="premier_message",
        question_utilisateur="Comment lui écrire un premier message qui sort du lot ?",
        profil_utilisateur=profil_cible
    )
    
    print("Conseil de Sophie:")
    print(conseil["texte"])
    
    # Sauvegarder l'audio
    if conseil["audio"]:
        coach.sauvegarder_audio(conseil["audio"], "conseil_sophie.mp3")
        print("Audio sauvegardé dans conseil_sophie.mp3")
