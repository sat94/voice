// Intégration Vue.js pour l'API Description Attractive
// À utiliser dans votre frontend Vue.js existant

const DescriptionAttractiveAPI = {
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://aaaazealmmmma.duckdns.org:8011' 
    : 'http://localhost:8011',
  
  // Générer une description attractive
  async genererDescription(data) {
    try {
      const response = await fetch(`${this.baseURL}/description/generer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ Erreur génération description:', error);
      throw error;
    }
  },
  
  // Obtenir des exemples
  async obtenirExemples() {
    try {
      const response = await fetch(`${this.baseURL}/description/exemples`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('❌ Erreur récupération exemples:', error);
      throw error;
    }
  },
  
  // Obtenir les statistiques
  async obtenirStats() {
    try {
      const response = await fetch(`${this.baseURL}/description/stats`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('❌ Erreur récupération stats:', error);
      throw error;
    }
  }
};

// Composant Vue.js exemple
const DescriptionAttractiveComponent = {
  template: `
    <div class="description-attractive-container">
      <h2>🎯 Créer une Description Attractive</h2>
      
      <form @submit.prevent="genererDescription" class="description-form">
        <div class="form-group">
          <label>👤 Prénom :</label>
          <input 
            v-model="formData.prenom" 
            type="text" 
            placeholder="Votre prénom"
            required
          />
        </div>
        
        <div class="form-group">
          <label>💪 Description physique :</label>
          <textarea 
            v-model="formData.physique"
            placeholder="Ex: Grande, sportive, cheveux bruns, yeux verts..."
            required
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>❤️ Goûts et centres d'intérêt :</label>
          <textarea 
            v-model="formData.gouts"
            placeholder="Ex: Voyage, cuisine, sport, cinéma, lecture..."
            required
          ></textarea>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>🎯 Type de relation :</label>
            <select v-model="formData.recherche" required>
              <option value="">Choisissez...</option>
              <option value="amical">👫 Amical</option>
              <option value="amoureuse">💕 Amoureuse</option>
              <option value="libertin">🔥 Libertin</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>📏 Longueur :</label>
            <select v-model="formData.longueur">
              <option value="courte">Courte</option>
              <option value="moyenne">Moyenne</option>
              <option value="longue">Longue</option>
            </select>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>🎨 Style :</label>
            <select v-model="formData.style_description">
              <option value="authentique">Authentique</option>
              <option value="elegant">Élégant</option>
              <option value="decontracte">Décontracté</option>
              <option value="seducteur">Séducteur</option>
            </select>
          </div>
        </div>
        
        <button 
          type="submit" 
          :disabled="isLoading"
          class="generate-btn"
        >
          <span v-if="isLoading">🔄 Génération...</span>
          <span v-else>✨ Générer ma description</span>
        </button>
      </form>
      
      <!-- Résultat -->
      <div v-if="result" class="result-container">
        <h3>🎉 Votre description attractive :</h3>
        
        <div class="description-text">
          {{ result.description }}
        </div>
        
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ result.score_attractivite }}/100</div>
            <div class="stat-label">Score d'attractivité</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ result.processing_time.toFixed(2) }}s</div>
            <div class="stat-label">Temps de génération</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ result.style_utilise }}</div>
            <div class="stat-label">Style utilisé</div>
          </div>
        </div>
        
        <div class="conseils-section">
          <h4>💡 Conseils d'amélioration :</h4>
          <ul>
            <li v-for="conseil in result.conseils_amelioration" :key="conseil">
              {{ conseil }}
            </li>
          </ul>
        </div>
        
        <div class="mots-cles-section">
          <h4>🏷️ Mots-clés attractifs :</h4>
          <div class="mots-cles">
            <span 
              v-for="mot in result.mots_cles_attractifs" 
              :key="mot"
              class="mot-cle"
            >
              {{ mot }}
            </span>
          </div>
        </div>
        
        <!-- Actions -->
        <div class="actions">
          <button @click="copierDescription" class="action-btn">
            📋 Copier la description
          </button>
          <button @click="regenererDescription" class="action-btn">
            🔄 Régénérer
          </button>
          <button @click="sauvegarderDescription" class="action-btn">
            💾 Sauvegarder
          </button>
        </div>
      </div>
      
      <!-- Erreur -->
      <div v-if="error" class="error-message">
        ❌ {{ error }}
      </div>
      
      <!-- Exemples -->
      <div class="exemples-section">
        <button @click="chargerExemples" class="exemples-btn">
          📋 Voir des exemples
        </button>
        <button @click="remplirExemple" class="exemples-btn">
          🎲 Remplir un exemple
        </button>
      </div>
    </div>
  `,
  
  data() {
    return {
      formData: {
        prenom: '',
        physique: '',
        gouts: '',
        recherche: '',
        longueur: 'moyenne',
        style_description: 'authentique',
        user_id: 'vue_user_' + Date.now()
      },
      result: null,
      error: null,
      isLoading: false,
      exemples: null
    }
  },
  
  methods: {
    async genererDescription() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isLoading = true;
      this.error = null;
      this.result = null;
      
      try {
        console.log('🚀 Génération description:', this.formData);
        
        const result = await DescriptionAttractiveAPI.genererDescription(this.formData);
        
        console.log('✅ Description générée:', result);
        this.result = result;
        
        // Émettre un événement pour le parent
        this.$emit('description-generated', {
          formData: this.formData,
          result: result
        });
        
      } catch (error) {
        console.error('❌ Erreur:', error);
        this.error = error.message;
      } finally {
        this.isLoading = false;
      }
    },
    
    async regenererDescription() {
      await this.genererDescription();
    },
    
    validateForm() {
      if (!this.formData.prenom.trim()) {
        this.error = 'Le prénom est requis';
        return false;
      }
      
      if (!this.formData.physique.trim()) {
        this.error = 'La description physique est requise';
        return false;
      }
      
      if (!this.formData.gouts.trim()) {
        this.error = 'Les goûts sont requis';
        return false;
      }
      
      if (!this.formData.recherche) {
        this.error = 'Le type de relation est requis';
        return false;
      }
      
      this.error = null;
      return true;
    },
    
    async chargerExemples() {
      try {
        if (!this.exemples) {
          this.exemples = await DescriptionAttractiveAPI.obtenirExemples();
        }
        
        // Afficher les exemples (vous pouvez adapter selon votre UI)
        let exemplesText = 'EXEMPLES DE DESCRIPTIONS :\\n\\n';
        
        Object.entries(this.exemples.exemples).forEach(([type, exemple]) => {
          exemplesText += \`\${type.toUpperCase()} (Score: \${exemple.score}/100):\\n\`;
          exemplesText += \`"\${exemple.description}"\\n\\n\`;
        });
        
        alert(exemplesText);
        
      } catch (error) {
        this.error = 'Erreur lors du chargement des exemples';
      }
    },
    
    remplirExemple() {
      const exemples = [
        {
          prenom: 'Sophie',
          physique: 'Grande, sportive, cheveux châtains, yeux verts, sourire éclatant',
          gouts: 'Yoga, cuisine healthy, voyages, photographie, randonnée, lecture',
          recherche: 'amoureuse'
        },
        {
          prenom: 'Alex',
          physique: 'Taille moyenne, athlétique, cheveux bruns, style décontracté',
          gouts: 'Sport, cinéma, sorties entre amis, musique live, découvertes culinaires',
          recherche: 'amical'
        },
        {
          prenom: 'Morgan',
          physique: 'Élégant, charme naturel, regard intense, style soigné',
          gouts: 'Art, vin, voyages, expériences sensorielles, gastronomie',
          recherche: 'libertin'
        }
      ];
      
      const exemple = exemples[Math.floor(Math.random() * exemples.length)];
      
      Object.assign(this.formData, exemple);
    },
    
    copierDescription() {
      if (this.result && this.result.description) {
        navigator.clipboard.writeText(this.result.description).then(() => {
          alert('✅ Description copiée dans le presse-papiers !');
        }).catch(() => {
          // Fallback pour les navigateurs plus anciens
          const textArea = document.createElement('textarea');
          textArea.value = this.result.description;
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand('copy');
          document.body.removeChild(textArea);
          alert('✅ Description copiée !');
        });
      }
    },
    
    sauvegarderDescription() {
      if (this.result) {
        // Émettre un événement pour que le parent puisse sauvegarder
        this.$emit('save-description', {
          formData: this.formData,
          result: this.result,
          timestamp: new Date().toISOString()
        });
        
        alert('✅ Description sauvegardée !');
      }
    }
  },
  
  async mounted() {
    // Test de connectivité
    try {
      await DescriptionAttractiveAPI.obtenirStats();
      console.log('✅ API Description Attractive connectée');
    } catch (error) {
      console.warn('⚠️ API Description Attractive non accessible:', error);
    }
  }
};

// Export pour utilisation
export { DescriptionAttractiveAPI, DescriptionAttractiveComponent };

// Utilisation dans votre app Vue.js :
/*
import { DescriptionAttractiveComponent } from './vue_description_integration.js';

export default {
  components: {
    DescriptionAttractive: DescriptionAttractiveComponent
  },
  
  methods: {
    onDescriptionGenerated(data) {
      console.log('Description générée:', data);
      // Traiter la description générée
    },
    
    onSaveDescription(data) {
      console.log('Sauvegarder description:', data);
      // Sauvegarder dans votre système
    }
  },
  
  template: \`
    <div>
      <DescriptionAttractive 
        @description-generated="onDescriptionGenerated"
        @save-description="onSaveDescription"
      />
    </div>
  \`
}
*/
