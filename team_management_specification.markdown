# Spécification des fonctionnalités pour la gestion des équipes
l'application doit etre en anglais
## Contraintes globales
- **Rôles des utilisateurs** :
  - **Manager** : utilisateur avec le rôle "manager", ne peut être responsable que d'une seule équipe.
  - **Agent** : utilisateur avec le rôle "agent", ne peut être membre que d'une seule équipe.
- Validation systématique pour empêcher l'ajout d'un manager ou d'un agent à plusieurs équipes.
- Les dates (création, modification) doivent être enregistrées automatiquement avec un format standard (ex. : ISO 8601).

## 1. Onglet "Ajouter" : Création d'une équipe
- **Fonctionnalité** : Permettre la création d'une nouvelle équipe avec la disposition entete (pour la creation de l'equipe) et lignes (ajout des membres).
- **Champs** :
  - **Nom de l'équipe** : champ texte obligatoire, unique (vérification en temps réel pour éviter les doublons).
  - **Responsable (manager)** : sélection via une liste déroulante ou un champ de recherche parmi les utilisateurs ayant le rôle "manager". Vérifier que le manager choisi n'est pas déjà assigné à une autre équipe (afficher un message d'erreur si c'est le cas).
  - **Membres (agents)** : sélection multiple d'utilisateurs ayant le rôle "agent" via une interface de recherche/ ajout dynamique. Vérifier que chaque agent n'est membre d'aucune autre équipe (afficher un message d'erreur si c'est le cas).
- **Options supplémentaires** :
  - Description optionnelle de l'équipe (champ texte).
  - Statut par défaut : actif.
  - Enregistrement automatique de la date de création.
- **Validation** : Bouton de confirmation avec message de succès ou d'erreur (ex. : "Équipe créée avec succès" ou "Erreur : manager déjà assigné").

## 2. Onglet "Liste" : Affichage des équipes
- **Fonctionnalité** : Afficher une liste paginée et triable de toutes les équipes.
- **Colonnes affichées** :
  - Nom de l'équipe (avec lien vers les détails de l'équipe).
  - Code de l'équipe .
  - Manager (nom, avec lien vers son profil).
  - Membre (nom de l'agent, avec lien vers son profil).
  - Date de création (format lisible, ex. : JJ/MM/AAAA).
- **Filtres** :
  - Recherche par nom d'équipe (saisie texte).
  - Filtre par manager (liste déroulante des managers).
  - Filtre par membre (recherche par nom d'agent).
  - Filtre par date de création (plage de dates).
- **Fonctionnalités avancées** :
  - Tri par colonne (nom, manager, date).
  - Export des données au format CSV ou PDF.
  - Option de rafraîchissement manuel ou automatique en cas de mise à jour.

## 3. Onglet "Supprimer" : Suppression d'équipes ou de membres
- **Suppression d'une équipe** :
  - Possible uniquement si l'équipe n'a aucun membre (agents). Afficher un message d'erreur si des membres sont encore présents.
  - Requiert une confirmation via une pop-up pour éviter les suppressions accidentelles.
  - Archiver les données supprimées (optionnel, pour audit).
- **Suppression de membres** :
  - Permettre la suppression individuelle ou multiple d'agents d'une équipe.
  - Mettre à jour automatiquement la liste des membres après suppression.
  - Notifier l'agent concerné (ex. : via un message système).
  - Si le manager est supprimé (en cas d'erreur ou de changement de rôle), proposer de désigner un nouveau manager ou de désactiver l'équipe.
- **Validation** : Afficher un message de confirmation ou d'erreur après chaque action.

## 4. Onglet "Statistiques" : Visualisation et analyse
- **Graphiques** :
  - Diagrammes en barres : nombre d'équipes par manager.
  - Diagrammes en camembert : répartition des agents par équipe.
  - Graphique en ligne : évolution du nombre d'équipes ou d'agents dans le temps.
- **Liste des équipes** :
  - Similaire à l'onglet "Liste", mais enrichie avec des métriques (ex. : nombre total d'agents, date de dernière modification).
- **Filtres** :
  - Par équipe (nom ou ID).
  - Par manager (liste déroulante).
  - Par membre (recherche par nom d'agent).
  - Par date de création (plage de dates).
  - Par date de modification (plage de dates).
  - Par statut (actif, inactif).
- **Fonctionnalités avancées** :
  - Tri des résultats par métrique.
  - Export des données filtrées (CSV/PDF).
  - Mise à jour en temps réel des graphiques et listes en cas de modification.

## 5. Onglet "Modifier" : Mise à jour des équipes
- **Fonctionnalité** : Permettre la modification des informations d'une équipe existante avec la disposition entete  et lignes ..
- **Actions possibles** :
  - **Changer le responsable (manager)** :
    - Sélectionner un nouveau manager parmi les utilisateurs ayant le rôle "manager" et non assignés à une autre équipe.
    - Vérifier que le nouveau manager est éligible (afficher un message d'erreur sinon).
  - **Ajouter un membre (agent)** :
    - Sélection multiple d'agents non assignés à une autre équipe.
    - Vérification en temps réel pour éviter les doublons ou les agents déjà assignés.
  - **Supprimer un membre (agent)** :
    - Retirer un ou plusieurs agents de l'équipe.
    - Mettre à jour la liste des membres et notifier les agents concernés.
  - **Modifier le nom ou la description** :
    - Permettre la mise à jour du nom de l'équipe (vérifier l'unicité).
    - Permettre la modification ou l'ajout d'une description.
- **Validation** :
  - Enregistrement automatique de la date de modification.
  - Afficher un message de confirmation ou d'erreur après chaque action (ex. : "Équipe modifiée avec succès" ou "Erreur : agent déjà membre d'une autre équipe").