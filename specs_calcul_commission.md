# Système de Gestion des Commissions

## Contexte
Gérer les commissions des agents et des managers selon des règles spécifiques.

## Structure des Commissions

### Commission des Agents
- **Taux** : 3% du montant du travail
- **Plafond** : 1 500 NAIRA maximum par travail
- **Formule** : `Commission = MIN(Montant × 0.03, 1500)`
- **Règle** : 
  - Si montant ≤ 50 000 NAIRA → Commission = Montant × 3%
  - Si montant > 50 000 NAIRA → Commission = 1 500 NAIRA (plafonné)

**Exemples** :
- 30 000 NAIRA → 900 NAIRA de commission
- 50 000 NAIRA → 1 500 NAIRA de commission
- 60 000 NAIRA → 1 500 NAIRA de commission (plafonné)
- 100 000 NAIRA → 1 500 NAIRA de commission (plafonné)

### Commission des Managers
- **Montant fixe** : 150 NAIRA par travail d'agent
- **Condition** : Le travail doit être ≥ 20 000 NAIRA
- **Formule** : `Commission = (Montant ≥ 20000) ? 150 : 0`

**Exemples** :
- Travail de 25 000 NAIRA → 150 NAIRA
- Travail de 15 000 NAIRA → 0 NAIRA
- 3 travaux (30 000, 18 000, 45 000) → 300 NAIRA total (150 + 0 + 150)

###  Calcul des Commissions
- Calculer automatiquement la commission agent pour chaque travail
- Calculer automatiquement la commission manager pour chaque travail
- Afficher le total des commissions par agent (somme de tous ses travaux)
- Afficher le total des commissions par manager (somme de tous les travaux de ses agents)

