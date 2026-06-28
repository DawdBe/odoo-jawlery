# Guide d'Implémentation Odoo — Projet Bijouterie

> **Odoo 17.0** — Python 3.10+, PostgreSQL 16+

---

## 1. Comment fonctionne Odoo

### Architecture Modulaire

Odoo est un framework Python qui suit une architecture **modulaire** : chaque fonctionnalité est un module (un dossier) contenant sa propre logique, ses données, et son interface.

Un module Odoo = un dossier avec des fichiers organisés :

```
mon_module/
├── __init__.py              # Initialise les fichiers Python du module
├── __manifest__.py           # Métadonnées (nom, version, dépendances, etc.)
├── models/                   # Modèles de données (classes Python → tables PostgreSQL)
├── views/                    # Vues XML (formulaires, listes, recherches, menus)
├── security/                 # Droits d'accès (CSV : groupes + règles)
├── data/                     # Données initiales / démo (XML)
├── i18n/                     # Traductions
├── static/                   # Assets (CSS, JS, images)
├── controllers/              # Routes HTTP (portails, API)
├── reports/                  # Rapports PDF (QWeb)
└── wizards/                  # Assistants (modèles temporaires + vues)
```

### ORM (Object-Relational Mapping)

Chaque classe Python héritant de `models.Model` crée automatiquement une table PostgreSQL. Pas besoin de SQL.

```python
from odoo import models, fields, api

class GoldRateHistory(models.Model):
    _name = 'gold.rate.history'          # Nom technique → table gold_rate_history
    _description = 'Gold Rate History'

    metal_type_id = fields.Many2one('metal.type', required=True)
    bursa_rate = fields.Monetary()
    market_rate = fields.Monetary()
    is_active = fields.Boolean(default=True)
```

**Types de champs** : Char, Text, Boolean, Integer, Float, Monetary, Date, Datetime, Selection, Many2one, One2many, Many2many, Binary, Html, Image, etc.

**Types de modèles** :
- `models.Model` → table persistante (la plupart des modèles)
- `models.TransientModel` → table temporaire (wizards, dashboard)
- `models.AbstractModel` → classe mixin (pas de table)

### Héritage

Odoo propose 3 mécanismes d'héritage :

| Type | Usage | Exemple |
|------|-------|---------|
| **Héritage classique** `_inherit` | Ajouter des champs à un modèle existant | `_inherit = 'product.template'` → ajoute `metal_type_id` |
| **Héritage par prototype** `_inherit` + `_name` | Créer un nouveau modèle à partir d'un existant | Rare, réservé aux experts |
| **Délégation** `_inherits` | Copier les champs d'un modèle parent | `_inherits = {'product.template': 'product_tmpl_id'}` |

### Vues XML

Les vues définissent l'interface utilisateur :

```xml
<record id="view_gold_rate_form" model="ir.ui.view">
    <field name="name">gold.rate.history.form</field>
    <field name="model">gold.rate.history</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <group>
                    <field name="metal_type_id"/>
                    <field name="bursa_rate"/>
                    <field name="market_rate"/>
                    <field name="is_active"/>
                </group>
            </sheet>
        </form>
    </field>
</record>
```

Types de vues : `form` (formulaire), `tree` (liste), `search` (recherche), `kanban`, `graph`, `pivot`, `calendar`, `cohort`, `activity`, `map`.

### Actions et Menus

```xml
<!-- Action (ouvre une vue) -->
<record id="action_gold_rate" model="ir.actions.act_window">
    <field name="name">Cours de l'Or</field>
    <field name="res_model">gold.rate.history</field>
    <field name="view_mode">tree,form</field>
</record>

<!-- Menu -->
<menuitem id="menu_gold_rate" name="Cours"
          parent="menu_jewelry_core"
          action="action_gold_rate"/>
```

### Sécurité

Trois niveaux :

1. **Groupes** (`security/groups.xml`) : catégories d'utilisateurs
2. **Droits d'accès** (`security/ir.model.access.csv`) : qui peut créer/lire/modifier/supprimer quoi
3. **Règles d'enregistrement** (`security/record_rules.xml`) : filtres par enregistrement

### Cycle de vie d'un développement

```
1. Créer le module (dossier + __manifest__.py)
2. Définir les modèles (models/*.py)
3. Créer les vues (views/*.xml)
4. Ajouter les droits d'accès (security/ir.model.access.csv)
5. Mettre à jour le module dans Odoo (make upgrade)
6. Tester dans l'interface → Itérer
```

---

## 2. Structure de nos 4 Modules

```
addons/
├── jewelry_core/                     # Socle
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── metal_type.py             # metal.type
│   │   ├── gold_rate_history.py      # gold.rate.history
│   │   ├── product_template.py       # product.template (héritage)
│   │   ├── product_category.py       # product.category (héritage)
│   │   ├── stock_quant.py            # stock.quant (héritage)
│   │   ├── stock_move.py             # stock.move (héritage)
│   │   ├── stock_inventory_weight.py # stock.inventory.weight
│   │   └── res_partner.py            # res.partner (héritage)
│   ├── views/
│   │   ├── metal_type_views.xml
│   │   ├── gold_rate_views.xml
│   │   ├── product_views.xml         # Vues étendues des produits
│   │   ├── stock_inventory_views.xml
│   │   └── menus.xml                 # Menu principal bijouterie
│   ├── security/
│   │   └── ir.model.access.csv
│   └── data/
│       └── metal_type_data.xml       # Types de métaux par défaut
│
├── jewelry_transactions/             # Cœur métier
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── jewelry_ticket.py         # jewelry.ticket
│   │   ├── jewelry_ticket_line.py    # jewelry.ticket.line
│   │   ├── product_promotion.py      # product.promotion
│   │   ├── associate_account.py      # associate.account
│   │   ├── associate_transaction.py  # associate.transaction
│   │   ├── purchase_order.py         # purchase.order (héritage)
│   │   ├── supplier_account.py       # supplier.account
│   │   ├── casse_melting.py          # casse.melting + .line
│   │   ├── service_order.py          # service.order
│   │   ├── atelier_price_table.py    # atelier.price.table
│   │   ├── daily_cash_register.py    # daily.cash.register
│   │   └── cash_register_line.py     # cash.register.line
│   ├── views/
│   │   ├── ticket_views.xml
│   │   ├── promotion_views.xml
│   │   ├── purchase_views.xml
│   │   ├── supplier_account_views.xml
│   │   ├── casse_melting_views.xml
│   │   ├── service_views.xml
│   │   ├── cash_register_views.xml
│   │   └── menus.xml
│   ├── security/
│   │   └── ir.model.access.csv
│   └── data/
│       └── atelier_price_data.xml    # Prix par défaut
│
├── jewelry_accounting/               # Rapports & Comptabilité
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── account_move.py          # account.move (héritage)
│   ├── views/
│   │   ├── account_move_views.xml
│   │   └── menus.xml
│   ├── security/
│   │   └── ir.model.access.csv
│   └── reports/
│       └── bilan_global_report.xml
│
└── jewelry_dashboard/                # Dashboard 360°
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   └── dashboard_360.py          # dashboard.360 (TransientModel)
    ├── views/
    │   └── dashboard_views.xml
    ├── security/
    │   └── ir.model.access.csv
    └── static/
        └── src/
            └── dashboard.js

```

---

## 3. Ordre d'Implémentation Recommandé

### Phase 1 — jewelry_core
Créer les modèles fondamentaux dont tout dépend :
1. `metal.type` (données)
2. `gold.rate.history`
3. Extension `product.template` + `product.category`
4. Extension `stock.quant` + `stock.move`
5. `stock.inventory.weight` + ligne
6. Extension `res.partner`
7. Vues XML pour chaque modèle
8. Données initiales (types de métaux)
9. Droits d'accès

### Phase 2 — jewelry_transactions
Toute la logique métier :
1. `jewelry.ticket` + `jewelry.ticket.line`
2. `product.promotion`
3. `purchase.order` étendu + ligne
4. `supplier.account`
5. `associate.account` + `associate.transaction`
6. `service.order` + `atelier.price.table`
7. `casse.melting` + ligne
8. `daily.cash.register` + `cash.register.line`
9. Vues XML pour chaque modèle
10. Droits d'accès

> **Note — Store strategy for computed fields:** The following computed fields use `store=True` to avoid expensive re-aggregations on every read. Odoo auto-recomputes them in DB only when their `@api.depends` trigger:
> - `supplier.account.weight_balance`, `cash_balance` → depends on `purchase.order` + `cash.register.line`
> - `associate.account.capital_balance`, `advance_balance` → depends on `associate.transaction`
> - `daily.cash.register.expected_balance`, `difference` → depends on `cash.register.line` (frozen once closed)
> - `jewelry.ticket.total_cash_in`, `total_cash_out`, `balance`, `total_remise` → depends on `jewelry.ticket.line`
> - `casse.melting.wastage_weight`, `refined_value`, `profit` → depends on lines + rates (frozen once done)
> 
> Lightweight single-record computations (`net_weight`, `estimated_value`, line-level differences) remain transient — they compute instantly from fields on the same record.

### Phase 3 — jewelry_accounting
Rapports et écritures :
1. Extension `account.move` + ligne
2. Vues XML

### Phase 4 — jewelry_dashboard
Interface temps réel :
1. `dashboard.360` (TransientModel)
2. Vue dashboard (peut utiliser du JavaScript)

---

## 4. Dépendances entre Modules

```
jewelry_dashboard     → jewelry_accounting, jewelry_transactions, jewelry_core
jewelry_accounting    → jewelry_transactions, jewelry_core, account
jewelry_transactions  → jewelry_core, account, purchase
jewelry_core          → product, stock, uom
```

Chaque `__manifest__.py` déclare ses dépendances :

```python
# jewelry_transactions/__manifest__.py
{
    'name': 'Jewelry Transactions',
    'depends': ['jewelry_core', 'account', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/ticket_views.xml',
        # ...
    ],
}
```

---

## 5. Commandes de Développement

```bash
# Créer un nouveau module
make module name=jewelry_core

# Après modification du code → mettre à jour
make upgrade module=jewelry_core

# Voir les logs
make logs

# Lancer les tests
make test module=jewelry_core

# Backup BDD
make backup
```

---

## 6. Bonnes Pratiques

| Règle | Pourquoi |
|-------|----------|
| Un fichier par modèle | Lisibilité, maintenabilité |
| Noms de champs en snake_case | Convention Odoo |
| `_description` sur chaque modèle | Obligatoire Odoo 17 |
| `string` sur chaque champ | Interface compréhensible |
| `required=True` sur les champs obligatoires | Intégrité des données |
| Groupes de droits stricts | Sécurité (client/FRS/atelier/associé n'ont pas accès aux mêmes données) |
| Tests pour chaque modèle | Vérification automatique |
| Ne jamais modifier un module Odoo standard | Toujours hériter (`_inherit`) |
