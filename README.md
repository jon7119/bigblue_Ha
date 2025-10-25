![](/custom_components/bigblue_Ha/icons/bigblue_Ha.jpg)
# Big Blue Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintenance](https://img.shields.io/badge/maintained%20by-Big%20Blue%20Community-blue.svg)](https://github.com/bigblue-community)

Une intégration Home Assistant pour les batteries Big Blue avec support multilingue (Français, Anglais, Allemand, Espagnol).

## 🌟 Fonctionnalités

### 📊 Capteurs
- **État de charge** (SOC) - Pourcentage de charge de la batterie
- **État de santé** (SOH) - Santé générale de la batterie
- **Puissance totale** - Puissance instantanée de la batterie
- **Tension totale** - Tension de sortie de la batterie
- **Courant total** - Courant de sortie de la batterie
- **Puissance PV** - Puissance des panneaux solaires (PV1, PV2, totale)
- **Tension PV** - Tension des panneaux solaires
- **Courant PV** - Courant des panneaux solaires
- **Génération** - Énergie générée quotidienne et totale
- **Énergie de sortie** - Énergie fournie quotidienne et totale
- **Température** - Température maximale et minimale
- **Temps de fonctionnement** - Durée de fonctionnement quotidienne et totale
- **Mode actuel** - Mode de fonctionnement de la batterie

### 🔢 Entités numériques
- **Seuil de décharge** - Configuration du seuil de décharge (5-50%)

### 🔘 Switches
- **Mode 1** - Priorité batterie
- **Mode 2** - Priorité micro-onduleur
- **Mode 3** - Mode personnalisé

## 🚀 Installation

### Via HACS (Recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur "..." puis "Dépôts personnalisés"
4. Ajoutez ce dépôt : `https://github.com/votre-username/bigblue-ha`
5. Recherchez "Big Blue" et installez
6. Redémarrez Home Assistant

### Installation manuelle

1. Téléchargez le dossier `custom_components/bigblue/`
2. Copiez-le dans votre dossier `custom_components/` de Home Assistant
3. Redémarrez Home Assistant

## ⚙️ Configuration

1. Allez dans **Configuration** > **Intégrations**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **Big Blue**
4. Entrez vos identifiants :
   - **Email** : Votre email Powafree
   - **Mot de passe** : Votre mot de passe Powafree
5. Cliquez sur **Soumettre**

## 🌍 Support multilingue

L'intégration supporte automatiquement :
- 🇫🇷 **Français** (par défaut)
- 🇬🇧 **Anglais**
- 🇩🇪 **Allemand**
- 🇪🇸 **Espagnol**

Les noms des entités s'adaptent automatiquement à la langue de votre Home Assistant.

## 📱 Interface utilisateur

### Capteurs principaux
- **État de charge** : Pourcentage de charge avec icône batterie
- **Puissance totale** : Puissance instantanée en watts
- **Tension totale** : Tension de sortie en volts
- **Mode actuel** : Mode de fonctionnement (1, 2, ou 3)

### Contrôles
- **Switches de mode** : Basculement entre les modes de fonctionnement
- **Seuil de décharge** : Réglage du seuil de décharge (5-50%)

## 🔧 Configuration avancée

### Intervalle de mise à jour
Par défaut, les données sont mises à jour toutes les 30 secondes. Vous pouvez modifier cet intervalle dans les options de l'intégration.

### Support multi-appareils
L'intégration supporte automatiquement plusieurs batteries Big Blue. Chaque batterie aura ses propres entités.

## 🐛 Dépannage

### Problèmes de connexion
- Vérifiez vos identifiants Powafree
- Assurez-vous que votre connexion internet est stable
- Vérifiez les logs Home Assistant pour plus de détails

### Entités manquantes
- Redémarrez Home Assistant après l'installation
- Vérifiez que l'intégration est bien configurée
- Consultez les logs pour les erreurs

### Problèmes de synchronisation
- Les switches se synchronisent automatiquement avec l'API
- En cas de problème, redémarrez l'intégration

## 📊 Données supportées

### Données de batterie
- État de charge (SOC)
- État de santé (SOH)
- Puissance, tension, courant
- Température
- Temps de fonctionnement

### Données solaires
- Puissance PV (PV1, PV2, totale)
- Tension PV
- Courant PV
- Génération quotidienne et totale

### Données de sortie
- Énergie de sortie quotidienne et totale
- Puissance de sortie
- Mode de fonctionnement

## 🔒 Sécurité

- Les identifiants sont stockés de manière sécurisée
- Communication HTTPS avec l'API Powafree
- Aucune donnée sensible n'est exposée

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités
- Améliorer les traductions

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :
- Consultez la documentation
- Vérifiez les logs Home Assistant
- Ouvrez une issue sur GitHub
- Rejoignez la communauté Big Blue

## 📈 Roadmap

- [ ] Support des alertes de batterie
- [ ] Historique des données
- [ ] Notifications personnalisées
- [ ] Intégration avec d'autres systèmes
- [ ] Support de nouvelles langues

---


**Développé avec ❤️ pour la communauté Big Blue**
