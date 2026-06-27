# Système de Gestion de Bijouterie — Design Odoo

> **Projet**: Bijouterie — Odoo 17.0  
> **Acteurs**: Admin (Propriétaire), Cassier, Employé de Poste (Vendeur)  
> **Sources**: `les_bosione.txt` + `Caisse magasin 2024-2025.xlsx` + `Bilan magasin 2023-2024.xlsx`  
> **Date**: 2026-06-23 (Mise à jour avec vocabulaire métier réel)

---

## Table des Matières

1. [Vocabulaire Métier Extrait des Excel](#1-vocabulaire-métier-extrait-des-excel)
2. [Résumé des Besoins](#2-résumé-des-besoins)
3. [Architecture Générale](#3-architecture-générale)
4. [Modules Odoo : Création vs Customisation](#4-modules-odoo--création-vs-customisation)
5. [Modules Créés de Zéro (Custom)](#5-modules-créés-de-zéro-custom)
6. [Modules Odoo Standard Customisés](#6-modules-odoo-standard-customisés)
7. [Structure détaillée des Fichiers](#7-structure-détaillée-des-fichiers)
8. [Diagrammes](#8-diagrammes)
9. [Workflow Détaillé par Acteur](#9-workflow-détaillé-par-acteur)
10. [Double Comptabilité — Pas dans le scope](#10-double-comptabilité--pas-dans-le-scope)
11. [Fasonage et Suivi de Poids](#11-fasonage-et-suivi-de-poids)
12. [Système de Caisse (Cash Register)](#12-système-de-caisse-cash-register)
13. [Bon Multi-Opérations](#13-bon-multi-opérations)
14. [Caisse de Voyage](#14-caisse-de-voyage)
15. [Vulnérabilités et Solutions](#15-vulnérabilités-et-solutions)
16. [Idées Supplémentaires](#16-idées-supplémentaires)
17. [Structure des Fichiers du Design](#17-structure-des-fichiers-du-design)

---

## 1. Vocabulaire Métier Extrait des Excel

### Types d'Or (Casse) — Système de Classification

Le vocabulaire réel du magasin utilise le terme **"Casse"** (or de récupération) pour classer l'or par pureté :

| Terme Excel | Karat | Pureté | Utilisation |
|-------------|-------|--------|-------------|
| **Casse18** | 18k / 750 | 75.0% | Or 750, le plus courant pour bijoux |
| **Casse21** | 21k | 87.5% | Or 875, très utilisé en Algérie |
| **Casse22** | 22k | 91.67% | Or 916, haute pureté |
| **Casse14** | 14k | 58.5% | Or 585, moins courant |
| **Or 750** | 18k | 75.0% | Variante de Casse18 |
| **Or Article** | mixte | variable | Or pour articles variés |
| **Or Article-21** | 21k | 87.5% | Variante 21k pour articles |
| **Or fin** | 24k | 99.9% | Or pur, rare en bijouterie |
| **Argent casse** | — | — | Argent de récupération |
| **Argent Mar.** | — | — | Argent marchandise |
| **Plaqué or** | — | — | Bijoux plaqués, sans poids or |
| **Perles / Djouhar** | — | — | Pierres précieuses / perles |
| **Devise** | — | — | Devises étrangères (Euro, USD) |

### Types de Transactions (Relevé Excel)

| Type Excel | Description | Sens |
|------------|-------------|------|
| **Achat** | Achat d'or/client (rachat) | Sortie d'argent |
| **Vente** | Vente de produit fini | Entrée d'argent |
| **Transfert** | Mouvement d'or (casse→casse) | Neutre (poids) |
| **Solde** | Règlement / paiement client/fournisseur | Variable |
| **Service** | Prestation (faconnage, réparation, etc.) | Entrée d'argent |
| **Frais** | Dépenses (loyer, énergie, transport) | Sortie d'argent |
| **Associés** | Transactions avec les associés | Variable |
| **Personnel** | Salaires / avances personnel | Sortie d'argent |
| **Verser** | Acompte / dépôt (paiement partiel) | Entrée d'argent |
| **Remise** | Réduction / remise commerciale | Moins-value |
| **Invest** | Investissements (matériel, équipement) | Sortie d'argent |
| **Décalage** | Écart de caisse / différence | Ajustement |

### Types de Services

| Service | Description |
|---------|-------------|
| **Faconnage** | Transformation or brut → produit fini |
| **Reparation** | Réparation de bijoux |
| **Dorure** | Dorure / plaquage or |
| **Argenture** | Plaquage argent |
| **Graver** | Gravure personnalisée |
| **Goupelle** | Soudure / assemblage |

### Types de Dépenses (Frais)

| Frais | Description |
|-------|-------------|
| **Loyer** | Loyer magasin + atelier |
| **Déjeuner** | Repas du personnel |
| **Mazot / Gasoil** | Carburant |
| **Voyage** | Frais de déplacement |
| **Énergie** | Électricité, gaz |
| **Emballage** | Boîtes, sachets |
| **Transport** | Transport marchandises |
| **Publicité** | Marketing, pubs |
| **Impôt** | Taxes, impôts |
| **Bureautique** | Fournitures bureau |
| **Entretien** | Maintenance locaux |
| **Communication** | Téléphone, internet |

### Styles de Produits (d'après les marges de vente)

| Style | Description | Coût façon typique |
|-------|-------------|-------------------|
| **Massif** | Bijou massif standard | 200-650 DZD/g |
| **Massif lux** | Massif haute qualité | 550 DZD/g |
| **Bataille** | Bijou à facettes | 500 DZD/g |
| **Massif controlé** | Massif avec contrôle qualité | 1100 DZD/g |
| **Mesaise** | Bijou simple / léger | 340 DZD/g |
| **Or 750** | Or 18k | Variable |

### Dénominations de Caisse (Billets)

| Billet | Utilisation |
|--------|-------------|
| 2000 DZD | Comptage caisse |
| 1000 DZD | Comptage caisse |
| 500 DZD | Comptage caisse |
| 200 DZD | Comptage caisse |
| 100 DZD | Comptage caisse |
| 50 DZD | Comptage caisse |
| 20 DZD | Comptage caisse |
| 10 DZD | Comptage caisse |

### Types de Partenaires

| Code Excel | Type Odoo | Description |
|------------|-----------|-------------|
| **C/F** | Client/Fournisseur | Client qui vend aussi |
| **FRS** | Fournisseur | Fournisseur d'or/produits |
| **AT** | Atelier | Façonneur / artisan |
| **Associés** | Partenaire | Associé dans le magasin |
| **Personnel** | Employé | Employé du magasin |

---

## 2. Résumé des Besoins

Basé sur `les_bosione.txt` + données réelles des fichiers Excel :

| Besoin | Description | Présent dans Excel |
|--------|-------------|-------------------|
| **Bilan global** | Générer un bilan facile | ✅ Bilan magasin 2023-2024 |
| **Dashboard 360°** | Voir caisse + poids par type de casse (18k/21k/22k/14k/Argent) | ✅ Inventaire casse |
| **Inventaire** | Suivi poids + pièces, coût de revient, marge par style | ✅ Marge vente sheet |
| **Cours de l'or** | API Bourse → conversion DZD parallèle, mise à jour manuelle | ✅ Prix argent 2014-2025 |
| **Code-barres** | Chaque produit a un barcode unique | À créer |
| **Double logiciel** | Légal/fisc + réel | ✅ Bilan double |
| **Fasonage** | Table des coûts de façon par style (massif, mesaise, etc.) | ✅ Marge sheet |
| **Historique client** | Toutes transactions, rapports imprimables | ✅ 26000+ lignes |
| **Prix statique** | Produits sans poids = prix fixe | Mentionné |
| **Bon multi-opérations** | 1 bon = vente + achat + solde | ✅ Double opération |
| **Paiement partiel** | Versé maintenant, solde plus tard | ✅ Verser / Solde |
| **Caisse de voyage** | Caisse séparée pour achats en déplacement | ✅ Caisse voyage sheet |
| **Comptage caisse** | Décompte par billet (2000→10 DZD) | ✅ Caisse sheet |

---

## 3. Architecture Générale

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Web / POS Mobile                        │
│              (Desktop, Tablet, Smartphone)                            │
├─────────────────────────────────────────────────────────────────────┤
│                         Odoo 17.0 Server                              │
│                     (Python 3.10+, PostgreSQL 16+)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   MODULES CUSTOM (4)                    MODULES ODOO (Customisés)     │
│   ┌────────────────────────┐        ┌────────────────────────┐       │
│   │ jewelry_core           │        │ product.template       │       │
│   │ (base + pricing        │        │ stock.quant / move     │       │
│   │  + inventory)          │        │ account.move           │       │
│   ├────────────────────────┤        │ res.partner            │       │
│   │ jewelry_transactions   │        │ purchase.order         │       │
│   │ (ticket + sales        │        └────────────────────────┘       │
│   │  + purchase + service  │                                          │
│   │  + cash_register)      │                                          │
│   ├────────────────────────┤                                          │
│   │ jewelry_accounting     │                                          │
│   │ (rapports + vues SQL)  │                                          │
│   ├────────────────────────┤                                          │
│   │ jewelry_dashboard      │                                          │
│   │ (UI séparée)           │                                          │
│   └────────────────────────┘                                          │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                      PostgreSQL 16+ Database                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Modules Odoo : Création vs Customisation

### Légende

| Symbole | Signification |
|---------|---------------|
| 🆕 | Créé de zéro (nouveau module Odoo) |
| 🔧 | Héritage / Extension d'un module Odoo existant |
| ✅ | Utilisé tel quel |

### Tableau Récapitulatif

| Module | Type | Description | Dépendances Odoo |
|--------|------|-------------|-------------------|
| `jewelry_core` | 🆕 | Socle unique: métaux, casse, karats, cours or, inventaire, pricing, marges, code-barres | `product`, `stock`, `uom` |
| `jewelry_transactions` | 🆕 | Tout le métier: ticket unifié, ventes, achats, services, fasonage, caisse, voyage | `jewelry_core`, `account`, `purchase` |
| `jewelry_accounting` | 🆕 | Rapports, bilans, vues SQL (comptabilité simple uniquement) | `jewelry_core`, `account` |
| `jewelry_dashboard` | 🆕 | Dashboard 360°: UI séparée, lectures seules | `jewelry_core`, `jewelry_accounting` |
| `product` | 🔧 | Extension `product.template`: métal, poids, karat, casse, style | — |
| `stock` | 🔧 | Extension: stock.move avec poids, inventaire poids par casse | — |
| `account` | 🔧 | Extension: écritures avec poids | — |
| `purchase` | 🔧 | Extension: achat au poids, suivi crédit FRS/AT | — |
| `res.partner` | 🔧 | Extension: code client, type (C/F/FRS/AT/Associé), solde | — |
| `uom` | ✅ | Unités: gramme, once, carat, pièce | — |
| `base` | ✅ | Utilisateurs, droits, modules de base | — |

---

## 5. Modules Créés de Zéro (Custom)

### 5.1 `jewelry_core` — Socle Fondation

**Rôle**: Module socle unique. Fédère les données de référence, le pricing et l'inventaire.
Fusionne les anciens modules `jewelry_base` + `jewelry_pricing` + `jewelry_inventory`.

**Modèles créés**:
- `metal.type` — Types: Casse18, Casse21, Casse22, Casse14, Or 750, Or Article, Or fin, Argent casse, Argent Mar., Plaqué or, Perles
- `gold.rate.history` — Historique des cours (bursa + market) avec date d'effet + spread configurable
- `stock.inventory.weight` — Inventaire physique avec pesée par type de métal
- `stock.inventory.weight.line` — Ligne d'inventaire: produit, type métal, poids avant/après

**Héritages Odoo**:
- `product.template`: `metal_type_id`, `jewelry_category`, `gross_weight`, `stone_weight`, `net_weight` [compute], `barcode`, `style`
- `stock.quant`: `weight_total`, `metal_type_id`, `estimated_value` [compute]
- `stock.move`: `weight_total`, `metal_type_id`, `move_type`

**Formule de prix**:
```
Prix vente = Poids net × Cours Marché du métal (au moment de la vente)
Prix achat = Évaluation visuelle (saisi manuellement)
Pas de prix stocké sur product.template — snapshot sur ticket.line.price_unit
```

### 5.2 `jewelry_transactions` — Cœur Métier

**Rôle**: Gère TOUTES les opérations du magasin via un bon unifié.
Fusionne les anciens modules `jewelry_sales` + `jewelry_purchase` + `jewelry_service` + `jewelry_cash_register`.

#### 5.2.1 Bon Unifié (`jewelry.ticket`)

L'employé crée un bon, puis ajoute des lignes en choisissant l'action pour chaque ligne :
vente, achat, service, fasonage, versé, solde, remise. Pas de modèles séparés par type d'opération.

**Modèles créés**:
- `jewelry.ticket` — Bon unifié pour TOUTES les opérations
- `jewelry.ticket.line` — Ligne de bon avec `line_type` (vente/achat/service/fasonage/versé/solde/remise)
- `product.promotion` — Règles de remise (percentage/fixed_price) par produit, style, catégorie ou métal
- Pas de modèle `double.operation` ni `client.history` — le ticket lui-même sert d'historique

**Statuts**:
- `product_status`: en_stock → en_fasonage → termine → donne_au_client
- `payment_status`: impaye → partiel → paye

#### 5.2.2 Fournisseurs & Dual Credit

- `supplier.account` — Compte fournisseur/atelier: `weight_balance` [compute store] (poids dû) + `cash_balance` [compute store] (argent dû)
  - Soldes auto-recalculés depuis `purchase.order` + `cash.register.line` via `@api.depends`

#### 5.2.3 Services & Fasonage

- `service.order` — Ordre de service (fasonage, réparation, dorure, argenture, gravure)
- `atelier.price.table` — Table des prix par atelier et style (remplace `fasonage.cost`)

#### 5.2.4 Caisse

- `daily.cash.register` — Registre de caisse journalier avec décompte billets intégré
- `cash.register.line` — Ligne de caisse (transaction liée à un ticket)
- Caisse de voyage: via champ `is_travel_cash` sur `cash.register.line` + `account.journal` dédié
  (pas de modèle `travel.cash` séparé — trop de complexité pour un besoin niche)

#### 5.2.5 Fonte de Casse (`casse.melting`)

- `casse.melting` — Opération de fonte: `weight_before`, `weight_after`, `wastage_weight` [compute store], `refined_value`, `profit`
- `casse.melting.line` — Lignes de fonte liées aux `jewelry.ticket.line`

#### 5.2.6 Comptes Associés

- `associate.account` — Compte par associé: `capital_balance` [compute store], `advance_balance` [compute store]
- `associate.transaction` — Lignes de transaction: capital, avance, distribution profit, zakat

### 5.3 `jewelry_accounting` — Comptabilité & Rapports

**Rôle**: Rapports financiers et bilans. Comptabilité simple uniquement.

**Héritages Odoo**:
- `account.move`: `jewelry_operation_type`, `weight_total`, `partner_id`
- `account.move.line`: `weight`, `metal_type_id`

**Particularités**:
- Pas de module audit dédié — les logs natifs Odoo + `jewelry.ticket` suffisent
- Pas de double comptabilité — le design reste en comptabilité simple
- Les rapports (bilan global, marges, poids) sont construits via des vues Odoo standard, pas des modèles SQL dédiés

### 5.4 `jewelry_dashboard` — Dashboard 360°

**Rôle**: UI séparée pour la vue d'ensemble en temps réel.

**Modèle**: `dashboard.360` (`TransientModel` — pas de données persistées, tous les champs sont `[compute]`)

**Indicateurs clés** (lectures seules depuis les autres modules):
- 💰 Trésorerie: Caisse actuelle, créances
- ⚖️ Poids par casse: Casse18, Casse21, Casse22, Casse14, Argent
- 📈 Profit du jour/mois par style
- 🏆 Top produits
- 🔄 Cours or actuel
- ⚠️ Alertes: Stock bas, paiements en retard, fasonage en attente

---

## 6. Modules Odoo Standard Customisés

### 6.1 `product` 🔧

Étendu depuis `jewelry_core`:
- `product.template`: `metal_type_id`, `jewelry_category`, `gross_weight`, `stone_weight`, `net_weight` [compute], `barcode`, `style`
- `product.product`: `serial_number`, `certificate_number`, `weight`, `location_id`
- `product.category`: `has_weight`, `is_jewelry`

### 6.2 `stock` 🔧

- `stock.move`: suivi en poids + quantité + type casse
- `stock.quant`: valorisation au poids par casse
- Pas d'extension de `stock.inventory` — géré par `stock.inventory.weight` dans `jewelry_core`

### 6.3 `account` 🔧

- `account.move`: type d'opération bijouterie, poids, casse
- Rapports: bilan global avec ventilation par casse

### 6.4 `purchase` 🔧

- `purchase.order`: achats au poids, consignation, échange or
- Lien avec `supplier.account` dans `jewelry_transactions`

### 6.5 `res.partner` 🔧

- Types: Client, FRS (Fournisseur), AT (Atelier), Associé
- Champs: `client_code`, `is_supplier`, `is_atelier`, `balance`

---

## 7. Structure détaillée des Fichiers

```
docs/
├── jewelry-system-design-odoo.md              ← Ce fichier
├── les_bosione.txt                             ← Besoins initiaux
├── Caisse magasin 2024-2025-2.xlsx            ← Données réelles caisse
├── Bilan magasin 2023-2024.xlsx               ← Bilan réel du magasin
├── diagrams/
│   ├── architecture_overview.puml              ← Architecture 4 modules
│   ├── use_case.puml                           ← Cas d'utilisation
│   ├── class_diagram.puml                      ← Classes (modèles Odoo)
│   ├── component_diagram.puml                  ← Dépendances entre modules
│   ├── er_diagram.puml                         ← Entité-Relation (tables + clés)
│   ├── sequence_diagram.puml                   ← 8 séquences combinées
│   ├── seq_double_operation.puml               ← S1: Double opération
│   ├── seq_fasonage.puml                       ← S2: Fasonage
│   ├── seq_paiement_partiel.puml               ← S3: Paiement échelonné
│   ├── seq_cours_or.puml                       ← S4: Cours de l'or
│   ├── seq_bilan_global.puml                   ← S5: Bilan global
│   ├── seq_cash_register.puml                  ← S6: Cycle de caisse
│   ├── seq_supplier_dual_credit.puml           ← S7: Crédit fournisseur
│   ├── seq_travel_cash.puml                    ← S8: Caisse voyage
│   ├── activity_cloture_caisse.puml            ← Activité: clôture caisse
│   ├── state_bon_lifecycle.puml                ← État: cycle de vie bon
│   ├── deployment_diagram.puml                 ← Déploiement Odoo

addons/
├── jewelry_core/                               ← 🆕 Socle (base + pricing + inventaire)
├── jewelry_transactions/                       ← 🆕 Transactions (ticket + vente + achat + service + caisse)
├── jewelry_accounting/                         ← 🆕 Comptabilité & rapports
└── jewelry_dashboard/                          ← 🆕 Dashboard (UI séparée)
```

---

## 8. Diagrammes

### Fichiers PlantUML

| Fichier | Diagramme | Description |
|---------|-----------|-------------|
| `use_case.puml` | Use Case | Tous les cas d'utilisation par acteur avec vocabulaire métier |
| `class_diagram.puml` | Classes | Tous les modèles Odoo avec champs réels |
| `component_diagram.puml` | Composants | Dépendances entre modules custom, Odoo et services externes |
| `er_diagram.puml` | Entité-Relation | Tables PostgreSQL avec PK/FK et cardinalités |
| `sequence_diagram.puml` | Séquence (×8) | Tous les scénarios combinés |
| `seq_double_operation.puml` | Séquence 1 | Double opération (vente+achat) |
| `seq_fasonage.puml` | Séquence 2 | Fasonage avec déchets |
| `seq_paiement_partiel.puml` | Séquence 3 | Paiement échelonné |
| `seq_cours_or.puml` | Séquence 4 | Mise à jour cours or |
| `seq_bilan_global.puml` | Séquence 5 | Bilan global |
| `seq_cash_register.puml` | Séquence 6 | Cycle de caisse quotidien (ouverture → clôture) |
| `seq_supplier_dual_credit.puml` | Séquence 7 | Crédit double (poids + cash) FRS/AT |
| `seq_travel_cash.puml` | Séquence 8 | Caisse de voyage via `is_travel_cash` |
| `activity_cloture_caisse.puml` | Activité | Clôture de caisse |
| `state_bon_lifecycle.puml` | État | Cycle de vie d'un bon (product + payment) |
| `deployment_diagram.puml` | Déploiement | Architecture Odoo Docker |

### Génération

```bash
# Installer PlantUML
sudo apt install plantuml  # ou: pip install plantuml

# Générer tous les diagrammes en PNG
plantuml docs/diagrams/*.puml

# En SVG
plantuml -tsvg docs/diagrams/*.puml
```

---

## 9. Workflow Détaillé par Acteur

### 9.1 Admin (Propriétaire)

```
1. Connexion → Dashboard 360°
2. Vérifie: caisse, poids par casse (Casse18/21/22/14/Argent), profit du jour
3. Met à jour le cours de l'or (via API Bourse ou manuel depuis ChangeDZ)
4. → Recalcul automatique des prix (tous produits impactés)
5. Consulte les rapports: bilan global, marges par style
6. Gère les utilisateurs (création cassier, vendeur)
7. Consulte les logs d'audit
8. Inventaire physique: compare poids attendu vs pesé
9. Valide les écarts de caisse
```

### 9.2 Cassier

```
1. Connexion → Caisse du jour
2. Encaissement:
   a. Reçoit paiement client (espèces avec décompte billets)
   b. Enregistre le versement dans le bon
   c. Gère les paiements partiels (versé + solde)
   d. Gère la caisse de voyage
3. Clôture de caisse:
   a. Compte la caisse physique (2000×N + 1000×N + 500×N + ...)
   b. Compare avec le total attendu
   c. Signe la clôture (différence = 0 ou écart justifié)
4. Imprime les reçus, factures, bons
```

### 9.3 Employé de Poste (Vendeur)

```
1. Accueil client → Recherche client par nom/code
2. Vente simple:
   a. Scanne produit → affiche prix, poids, type casse, style
   b. Ajoute au panier → encaissement → reçu
3. Achat client (rachat):
   a. Pèse l'or/bijou → saisit poids + type casse + karat
   b. Évalue le prix selon cours + état
   c. Enregistre l'achat → bon d'achat
4. Double opération (le plus fréquent dans les données Excel):
   a. Crée un bon multi-opérations
   b. Ajoute l'achat client (vieux bijou: Casse18, 8.5g)
   c. Ajoute la vente (nouveau bijou: massif, 12g)
   d. Calcule la différence
   e. Enregistre le paiement (total ou partiel: versé)
   f. Imprime le bon unique avec les 2 opérations + solde
5. Fasonage:
   a. Crée un ordre de fasonage
   b. Enregistre l'or brut reçu (poids, type casse, karat)
   c. Saisit le style (massif/mesaise/bataille) et produit
   d. Envoie à l'atelier (AT)
   e. À réception: pèse, calcule déchet, facture le fasonage
6. Service: réparation, dorure, argenture, gravure
7. Consultation historique client (toutes transactions)
```

---

## 10. Double Comptabilité — Pas dans le scope

> La double comptabilité (légal + réel) n'existe pas dans ce design.
> Le système actuel est en comptabilité simple uniquement.

---

## 11. Fasonage et Suivi de Poids

### Table des Prix Atelier (`atelier.price.table`)

Basée sur les données réelles de la feuille "Marge vente":

| Style | Coût façon (DZD/g) | Prix vente typique | Marge |
|-------|-------------------|-------------------|-------|
| **Massif** | 200-650 | 5800 | ~36% |
| **Massif lux** | 550 | 6500 | ~39% |
| **Bataille** | 500 | 6000 | ~36% |
| **Massif controlé** | 1100 | 7500 | ~44% |
| **Mesaise** | 340 | 5600 | ~34% |
| **Or 750** | Variable | 7700 | Variable |

### Workflow Fasonage (données réelles)

```
Or brut reçu (20g, Casse21, 21k)
→ Envoi à l'atelier (AT b1/AT b2 dans les données)
→ Produit fini (18.5g) + Déchet (1.5g = 7.5%)
→ Coût façon = poids_fini × coût_par_gramme (ex: 18.5 × 600 = 11,100 DZD)
→ Client paie le fasonage
→ Le déchet (1.5g) reste dans notre stock → profit lors de la refonte
```

---

## 12. Système de Caisse (Cash Register)

### Registre de Caisse Quotidien

Structure basée sur la feuille "caisse" de l'Excel:

```
Date: _______________
Décompte:
  2000 DZD × ___ = _______
  1000 DZD × ___ = _______
   500 DZD × ___ = _______
   200 DZD × ___ = _______
   100 DZD × ___ = _______
    50 DZD × ___ = _______
    20 DZD × ___ = _______
    10 DZD × ___ = _______
  TOTAL: ______________
```

### Clôture de Caisse

1. Solde d'ouverture
2. + Toutes les entrées du jour (ventes, services, versés)
3. - Toutes les sorties du jour (achats, frais, remises)
4. = Solde attendu
5. Comparaison avec le comptage physique
6. Si écart ≠ 0: justification ou escalade à l'Admin

### Caisse de Voyage

Caisse séparée pour les achats en déplacement (fournisseurs, ateliers):
- Alimentée depuis la caisse principale
- Utilisée pour payer les FRS/AT en déplacement
- Suivi des entrées/sorties avec référence

---

## 13. Bon Multi-Opérations

### Structure d'un Bon (d'après les données Excel)

```
BON #B-2024-001
Date: 15/06/2024
Client: Ahmed Benali (C/F)

LIGNE 1 — Achat (Rachat)
  Produit: Bague or 21k, Casse18
  Poids: 8.5g, Karat: 21k
  Prix: 25,000 DZD

LIGNE 2 — Vente
  Produit: Chaîne or 21k, Style massif
  Poids: 12g, Karat: 21k
  Prix: 85,000 DZD

SOLDE: Client doit 60,000 DZD
  Versé aujourd'hui: 20,000 DZD (versé)
  Reste à payer: 40,000 DZD (solde)
  Échéance: 15/07/2024
────────────────────────────────────────
Signature client: _________
Signature vendeur: _________
```

---

## 14. Caisse de Voyage — Simplifiée

Pas de modèle dédié `travel.cash`. La caisse de voyage est gérée via:
- Un `account.journal` dédié de type "caisse voyage"
- Le champ `is_travel_cash` sur `cash.register.line`
- Les opérations (alimentation, dépense, rapatriement) sont des `cash.register.line` normales

Basée sur la feuille "caisse de voyage" de l'Excel:

| Champ Excel | Mapping Odoo |
|-------------|-------------|
| Date | `cash.register.line.date` |
| Fournisseur | `partner_id` (FRS/AT) |
| Réf | `reference` |
| Désignation | `description` |
| P. Entrée/Sortie | `weight` |
| Entrée/Sortie (DZD) | `amount` + type entrée/sortie |

Utilisation typique:
- Paiement aux ateliers (AT b1, AT b2)
- Achat d'or chez les fournisseurs (FRS)
- Frais de déplacement (mazot, hôtel, repas)
- Rapatriement des fonds vers le magasin

---

## 15. Vulnérabilités et Solutions

| Vulnérabilité | Risque | Solution |
|---------------|--------|----------|
| **Poids erroné** | Perte sur le prix | Double validation, audits aléatoires, logs |
| **Cours non mis à jour** | Vente à perte | Notification si pas de mise à jour > 3 jours |
| **Paiement partiel non suivi** | Oubli du solde | Relances auto, dashboard créances |
| **Double comptabilité** | (reporté) | Sera géré dans un projet séparé |
| **Vol stock (casse)** | Disparition d'or | Suivi par lot + poids, inventaire hebdo |
| **Déchet fasonage non tracé** | Profit caché non compté | Enregistrement obligatoire déchet |
| **Mélange types casse** | Erreur de prix | Typage strict métal+karat+casse |
| **Accès non autorisé** | Fuite données réelles | Groupes de droits stricts |
| **Écart de caisse** | Perte financière | Clôture quotidienne avec décompte |
| **Caisse de voyage** | Mauvais suivi | Comptabilité séparée avec rapprochement |

---

## 16. Idées Supplémentaires

### 16.1 Webhook Cours Or Manuel
- Interface pour coller le cours depuis ChangeDZ / Gold Price Live
- Auto-conversion USD → DZD parallèle
- Historique graphique par type de casse

### 16.2 Gestion des Déchets d'Or
- Suivi du bassin de déchets (poussière, chutes)
- Valorisation automatique au seuil
- Refonte → or réutilisable

### 16.3 Mode "Marchandage" avec Plancher
- Bouton "Négocier" au POS
- Plancher configurable par style
- Log de chaque négociation

### 16.4 Fidélité Poids
- Points par gramme vendu/apporté
- Réduction sur fasonage après X grammes

### 16.5 Cachet Numérique QR
- Reçus avec QR code d'authentification
- Client scanne pour vérifier l'authenticité

### 16.6 Notifications WhatsApp/SMS
- Rappel fasonage prêt
- Relance solde impayé

---

## 17. Structure des Fichiers du Design

```
docs/
├── jewelry-system-design-odoo.md          ← Ce fichier (français, design actif)
├── les_bosione.txt                         ← Besoins initiaux
├── Caisse magasin 2024-2025-2.xlsx        ← Données caisse 2024-2025 (19280 lignes)
├── Bilan magasin 2023-2024.xlsx           ← Bilan 2023-2024 (26000+ lignes)
└── diagrams/
    ├── architecture_overview.puml          ← Architecture 4 modules
    ├── use_case.puml                       ← Cas d'utilisation
    ├── class_diagram.puml                  ← Modèles Odoo (classes détaillées)
    ├── component_diagram.puml              ← Dépendances entre modules
    ├── er_diagram.puml                     ← Entité-Relation (tables + clés)
    ├── sequence_diagram.puml               ← 8 séquences combinées
    ├── seq_double_operation.puml           ← S1: Double opération
    ├── seq_fasonage.puml                   ← S2: Fasonage
    ├── seq_paiement_partiel.puml           ← S3: Paiement échelonné
    ├── seq_cours_or.puml                   ← S4: Cours de l'or
    ├── seq_bilan_global.puml               ← S5: Bilan global
    ├── seq_cash_register.puml              ← S6: Cycle caisse
    ├── seq_supplier_dual_credit.puml       ← S7: Crédit fournisseur
    ├── seq_travel_cash.puml                ← S8: Caisse voyage
    ├── activity_cloture_caisse.puml        ← Clôture caisse
    ├── state_bon_lifecycle.puml            ← Cycle de vie bon
    └── deployment_diagram.puml             ← Déploiement Docker
```

---

*Document généré le 2026-06-27 — Mise à jour: synced with diagrams, removed deleted models, added missing models*
*Pour Odoo 17.0 — Modules: 4 (jewelry_core, jewelry_transactions, jewelry_accounting, jewelry_dashboard) + extensions Odoo*
