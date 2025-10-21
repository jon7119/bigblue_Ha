# Changelog

All notable changes to the Big Blue integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-21

### Added
- 🎉 **Première version** de l'intégration Big Blue
- 📊 **25 capteurs** pour monitoring complet des batteries
- 🔢 **Entité numérique** pour le seuil de décharge
- 🔘 **3 switches** pour les modes de fonctionnement
- 🌍 **Support multilingue** (Français, Anglais, Allemand, Espagnol)
- 🔄 **Synchronisation automatique** des switches avec l'API
- 🔧 **Support multi-appareils** pour plusieurs batteries
- 🔒 **Sécurité** : Communication HTTPS sécurisée
- 📱 **Interface utilisateur** intuitive et responsive

### Capteurs ajoutés
- **État de charge** (SOC) - Pourcentage de charge
- **État de santé** (SOH) - Santé de la batterie
- **Puissance totale** - Puissance instantanée
- **Tension totale** - Tension de sortie
- **Courant total** - Courant de sortie
- **Puissance PV** - Puissance des panneaux (PV1, PV2, totale)
- **Tension PV** - Tension des panneaux
- **Courant PV** - Courant des panneaux
- **Génération** - Énergie générée quotidienne et totale
- **Énergie de sortie** - Énergie fournie quotidienne et totale
- **Température** - Température maximale et minimale
- **Temps de fonctionnement** - Durée quotidienne et totale
- **Mode actuel** - Mode de fonctionnement

### Contrôles ajoutés
- **Seuil de décharge** - Configuration numérique (5-50%)
- **Mode 1** - Priorité batterie
- **Mode 2** - Priorité micro-onduleur
- **Mode 3** - Mode personnalisé

### Fonctionnalités techniques
- **API Powafree** - Intégration complète avec l'API
- **Authentification JWT** - Gestion automatique des tokens
- **Renouvellement automatique** - Tokens renouvelés automatiquement
- **Gestion d'erreurs** - Gestion robuste des erreurs de connexion
- **Logs détaillés** - Logging complet pour le débogage
- **Conversion d'unités** - Conversion automatique des unités
- **Détection multi-appareils** - Support automatique de plusieurs batteries

### Traductions
- 🇫🇷 **Français** - Traduction complète
- 🇬🇧 **Anglais** - Traduction complète
- 🇩🇪 **Allemand** - Traduction complète
- 🇪🇸 **Espagnol** - Traduction complète

### Compatibilité
- **Home Assistant** : 2023.1.0+
- **HACS** : Compatible
- **Python** : 3.9+
- **Architecture** : Toutes les architectures supportées

### Documentation
- **README.md** - Documentation complète
- **info.md** - Informations pour HACS
- **CHANGELOG.md** - Historique des versions
- **LICENSE** - Licence MIT

### Tests
- **Tests unitaires** - Tests complets de l'intégration
- **Tests de traduction** - Validation des traductions
- **Tests d'API** - Tests de connexion et de données
- **Tests de synchronisation** - Tests des switches

---

## [0.9.0] - 2024-10-20

### Added
- 🔧 **Développement initial** de l'intégration
- 📊 **Capteurs de base** pour les données de batterie
- 🔘 **Switches de mode** pour le contrôle
- 🌍 **Fichiers de traduction** multilingues
- 🔒 **Authentification** avec l'API Powafree

### Technical
- **Structure de base** - Architecture de l'intégration
- **API Client** - Client pour l'API Powafree
- **Coordinator** - Gestionnaire de données
- **Entités** - Capteurs, switches, entités numériques
- **Traductions** - Support multilingue

---

**Note** : Cette intégration est développée pour la communauté Big Blue et est maintenue activement.
