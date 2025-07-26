
// Exemple d'utilisation côté frontend (JavaScript)

// 1. Appel IA simple (texte seulement)
async function demanderConseilIA(prompt) {
    try {
        const response = await fetch('https://aaaazealmmmma.duckdns.org/ia/simple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt
            })
        });
        
        const result = await response.json();
        return result.response;
        
    } catch (error) {
        console.error('Erreur IA:', error);
        return null;
    }
}

// 2. Appel IA complet (avec audio)
async function demanderConseilIAAvecAudio(prompt) {
    try {
        const response = await fetch('https://aaaazealmmmma.duckdns.org/ia', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                system_prompt: "Tu es Sophie, coach de séduction experte. Réponds en 2-3 phrases maximum.",
                include_prompt_audio: true,
                voice: "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)",
                rate: "+0%",
                pitch: "+0Hz"
            })
        });
        
        const result = await response.json();
        
        // Jouer l'audio de la réponse
        if (result.response_audio) {
            const audioBlob = base64ToBlob(result.response_audio, 'audio/mpeg');
            const audio = new Audio(URL.createObjectURL(audioBlob));
            audio.play();
        }
        
        return {
            texte: result.response,
            audio: result.response_audio,
            temps: result.processing_time
        };
        
    } catch (error) {
        console.error('Erreur IA:', error);
        return null;
    }
}

// Fonction utilitaire pour convertir base64 en blob
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], {type: mimeType});
}

// Exemples d'utilisation
demanderConseilIA("Comment aborder une fille dans un café ?")
    .then(conseil => console.log("Conseil:", conseil));

demanderConseilIAAvecAudio("Comment faire un compliment sincère ?")
    .then(result => {
        console.log("Conseil:", result.texte);
        console.log("Temps de traitement:", result.temps + "s");
    });
