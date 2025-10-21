# Big Blue Integration

## Description

Intégration Home Assistant pour les batteries Big Blue avec support multilingue complet.

## Fonctionnalités

- 📊 **25 capteurs** : SOC, puissance, tension, température, etc.
- 🔢 **Entité numérique** : Seuil de décharge configurable
- 🔘 **3 switches** : Modes de fonctionnement (1, 2, 3)
- 🌍 **4 langues** : Français, Anglais, Allemand, Espagnol
- 🔄 **Synchronisation** : Switches synchronisés avec l'API
- 🔧 **Multi-appareils** : Support de plusieurs batteries

## Capteurs principaux

- **État de charge** : Pourcentage de charge de la batterie
- **Puissance totale** : Puissance instantanée en watts
- **Tension totale** : Tension de sortie en volts
- **Mode actuel** : Mode de fonctionnement (1, 2, ou 3)
- **Température** : Température maximale et minimale
- **Génération PV** : Puissance des panneaux solaires
- **Énergie de sortie** : Énergie fournie quotidienne et totale

## Contrôles

- **Switches de mode** : Basculement entre les modes
- **Seuil de décharge** : Réglage du seuil (5-50%)

## Installation

1. Via HACS (recommandé)
2. Installation manuelle dans `custom_components/`

## Configuration

1. Ajoutez l'intégration dans Home Assistant
2. Entrez vos identifiants Powafree
3. L'intégration détecte automatiquement vos batteries

## Support multilingue

- 🇫🇷 Français (par défaut)
- 🇬🇧 Anglais
- 🇩🇪 Allemand
- 🇪🇸 Espagnol

## Sécurité

- Communication HTTPS sécurisée
- Identifiants stockés de manière sécurisée
- Aucune donnée sensible exposée

---

**Développé pour la communauté Big Blue**
