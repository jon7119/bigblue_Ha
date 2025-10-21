# Big Blue Battery Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/bigblue)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Une intégration Home Assistant pour les batteries Big Blue via l'API Powafree.

## Fonctionnalités

- 🔋 **Surveillance de la batterie** : SOC, SOH, tension, courant, puissance
- ☀️ **Panneaux solaires** : Production PV1 et PV2 en temps réel
- ⚡ **Production d'énergie** : Production journalière et totale
- 🌱 **Environnement** : Économies CO2 calculées
- 🌡️ **Température** : Surveillance des températures du système
- ⏱️ **Temps de fonctionnement** : Historique des performances

## Capteurs disponibles

### Batterie (7 capteurs)
- État de charge total (SOC)
- État de santé (SOH)
- Tension batterie
- Courant batterie
- Puissance batterie
- Capacité restante
- Capacité nominale

### Panneaux solaires (7 capteurs)
- Tension PV1
- Courant PV1
- Puissance PV1
- Tension PV2
- Courant PV2
- Puissance PV2
- Puissance PV totale

### Production d'énergie (4 capteurs)
- Production journalière
- Production totale
- Énergie sortie journalière
- Énergie sortie totale

### Système (5 capteurs)
- Température maximale
- Température minimale
- Économies CO2 journalières
- Temps de fonctionnement journalier
- Temps de fonctionnement total

## Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite
4. Sélectionnez "Intégrations personnalisées"
5. Ajoutez ce repository : `https://github.com/yourusername/bigblue`
6. Recherchez "Big Blue Battery" et installez
7. Redémarrez Home Assistant

### Installation manuelle

1. Téléchargez le dossier `bigblue` depuis ce repository
2. Copiez-le dans `custom_components/` de votre Home Assistant
3. Redémarrez Home Assistant

## Configuration

1. Allez dans **Configuration** > **Intégrations**
2. Cliquez sur **Ajouter une intégration**
3. Recherchez **Big Blue Battery**
4. Entrez vos identifiants Powafree :
   - **Email** : Votre email Powafree
   - **Mot de passe** : Votre mot de passe Powafree
5. Cliquez sur **Soumettre**

## Prérequis

- Compte Powafree actif
- Appareil Big Blue connecté à votre compte
- Connexion internet stable

## Support

- **Issues** : [GitHub Issues](https://github.com/yourusername/bigblue/issues)
- **Discussions** : [GitHub Discussions](https://github.com/yourusername/bigblue/discussions)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur

Développé pour la communauté Home Assistant avec ❤️

---

**Note** : Cette intégration utilise l'API Powafree pour récupérer les données de vos batteries Big Blue. Assurez-vous d'avoir un compte Powafree valide et un appareil connecté.
