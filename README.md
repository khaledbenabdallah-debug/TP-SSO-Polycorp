TP : Portail SSO adossé à un annuaire (Polycorp)

1. Contexte et Architecture
Polycorp souhaitait mettre en place un SSO (Single Sign-On) pour ses deux applications web (Portail RH et Portail Notes) en s'appuyant sur son annuaire OpenLDAP existant. 
L'architecture repose sur Keycloak en tant que fournisseur d'identité (IdP) :
- **OpenLDAP** est connecté à Keycloak via un compte de service (bind LDAP).
- **Portail RH** utilise le protocole **SAML 2.0**.
- **Portail Notes** utilise le protocole **OIDC (OpenID Connect)**.

2. Réalisation technique
2.1 Annuaire LDAP
- Création du DIT (`dc=polycorp,dc=local`) avec les unités `ou=people` et `ou=groups`.
- Ajout des utilisateurs (Alice, Emma) et des groupes `rh` (Alice) et `employes` (Alice, Emma).
- Création du compte de service `cn=svc-keycloak` en lecture seule (ACL par défaut).

2.2 Configuration Keycloak
- **User Federation** : Connexion au LDAP en mode `READ_ONLY` via le compte de service. Les utilisateurs et les groupes sont importés.
- **Mapping des attributs** : Correction des attributs SAML pour que le portail RH reçoive les noms corrects (`givenName`, `surname`, `email`) au lieu des noms techniques (`urn:oid...`).
- **Rôle** : Création du rôle `acces-rh` et association au groupe LDAP `rh`.
- **Clients** : 
  - `portail-notes` (OIDC) configuré avec le mapper `realm-roles` pour envoyer les rôles dans le token.
  - `portail-rh` (SAML) configuré avec le mapper `roles-single` pour envoyer les rôles dans l'assertion SAML.

2.3 Les Portails (Python/Flask)
- Le portail RH (`rh.py`) écoute sur le port 5002 et gère l'assertion SAML.
- Le portail Notes (`notes.py`) écoute sur le port 5001 et gère les jetons OIDC.

3. Démonstrations et Preuves
- **SSO** : Alice se connecte une seule fois à Keycloak et accède aux deux portails sans ressaisir son mot de passe.
- **Contrôle d'accès** : Alice accède à l'espace RH car elle possède le rôle `acces-rh` (hérité du groupe LDAP `rh`). Emma, authentifiée, est refusée sur cet espace car elle n'a pas ce rôle.
- **Attributs** : Le nom et l'email d'Alice sont correctement remontés dans le portail RH.

4. Points de vigilance (Sécurité)
- Les mots de passe des utilisateurs sont faibles.
- Le mot de passe du compte de service `svc-keycloak` est stocké en clair.
- Le trafic LDAP (`ldap://`) n'est pas chiffré (pas de TLS/StartTLS)
