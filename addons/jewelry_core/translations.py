ALL_TRANSLATIONS = {
    # Centralized French/Arabic translations for all modules.
    # Applied at module install via post_init_hook.
    # Covers model names, field labels, menu items, actions, views, and sequences.
    # Key: Odoo XML ID (technical), Value: French translation.
    'ir.model': {
        'jewelry_core.model_gold_rate_history': "Cours de l'Or",
        'jewelry_core.model_gold_price_api_config': "Configuration API Or",
        'jewelry_core.model_gold_price_api_log': "Journal API Or",
        'jewelry_core.model_gold_price_overview': "Aperçu des Prix Or",
        'jewelry_core.model_metal_type': 'Type de Métal / Casse',
        'jewelry_core.model_stock_inventory_weight': 'Inventaire Physique des Poids',
        'jewelry_core.model_stock_inventory_weight_line': "Ligne d'Inventaire Poids",
        'jewelry_core.model_stock_move': 'Mouvement de Stock',
        'jewelry_core.model_stock_quant': 'Quantité en Stock',
        'jewelry_transactions.model_jewelry_ticket': 'Ticket de Bijouterie',
        'jewelry_transactions.model_jewelry_ticket_line': 'Ligne de Ticket',
        'jewelry_transactions.model_casse_melting': 'Fonte de Casse',
        'jewelry_transactions.model_supplier_account': 'Compte Fournisseur',
        'jewelry_transactions.model_associate_account': 'Compte Associé',
        'jewelry_transactions.model_service_order': 'Bon de Service',
        'jewelry_transactions.model_daily_cash_register': 'Caisse Journalière',
        'jewelry_transactions.model_cash_register_line': 'Ligne de Caisse',

        'jewelry_dashboard.model_dashboard_360': "Tableau de Bord 360°",
    },
    'ir.model.fields': {
        'jewelry_core.field_gold_price_overview__base_24k_usd_oz': '24k (USD/oz)',
        'jewelry_core.field_gold_price_overview__dzd_parallel_rate': 'Taux Parallèle DZD',
        'jewelry_core.field_gold_price_overview__bursa_24k_dzd': 'Bourse 24k (DZD/g)',
        'jewelry_core.field_gold_price_overview__bursa_21k_dzd': 'Bourse 21k (DZD/g)',
        'jewelry_core.field_gold_price_overview__bursa_18k_dzd': 'Bourse 18k (DZD/g)',
        'jewelry_core.field_gold_price_overview__spread_24k': 'Écart 24k',
        'jewelry_core.field_gold_price_overview__spread_21k': 'Écart 21k',
        'jewelry_core.field_gold_price_overview__spread_18k': 'Écart 18k',
        'jewelry_core.field_gold_price_overview__market_24k_dzd': 'Marché 24k (DZD/g)',
        'jewelry_core.field_gold_price_overview__market_21k_dzd': 'Marché 21k (DZD/g)',
        'jewelry_core.field_gold_price_overview__market_18k_dzd': 'Marché 18k (DZD/g)',
        'jewelry_core.field_gold_price_overview__last_update': 'Dernière MAJ',
        'jewelry_core.field_gold_rate_history__base_24k_usd': 'Base 24k (USD/oz)',
        'jewelry_core.field_gold_rate_history__base_24k_dzd': 'Base 24k (DZD/g)',
        'jewelry_core.field_gold_rate_history__bursa_rate': 'Cours Bourse (Référence)',
        'jewelry_core.field_gold_rate_history__create_uid': 'Créé par',
        'jewelry_core.field_gold_rate_history__currency_id': 'Devise',
        'jewelry_core.field_gold_rate_history__dzd_parallel_rate': 'Taux Parallèle DZD',
        'jewelry_core.field_gold_rate_history__effective_date': "Date d'Effet",
        'jewelry_core.field_gold_rate_history__market_rate': 'Cours Marché (Utilisé)',
        'jewelry_core.field_gold_rate_history__market_spread': 'Écart Bourse→Marché',
        'jewelry_core.field_gold_rate_history__metal_type_id': 'Type de Métal',
        'jewelry_core.field_gold_rate_history__notes': 'Remarques',
        'jewelry_core.field_metal_type__category': 'Catégorie',
        'jewelry_core.field_metal_type__code': 'Code',
        'jewelry_core.field_metal_type__name': 'Nom',
        'jewelry_core.field_stock_inventory_weight__actual_weight': 'Poids Réel (g)',
        'jewelry_core.field_stock_inventory_weight__difference_weight': 'Différence (g)',
        'jewelry_core.field_stock_inventory_weight__expected_weight': 'Poids Attendu (g)',
        'jewelry_core.field_stock_inventory_weight__line_ids': 'Lignes',
        'jewelry_core.field_stock_inventory_weight__state': 'État',
        'jewelry_core.field_stock_inventory_weight_line__inventory_id': 'Inventaire',
        'jewelry_core.field_stock_inventory_weight_line__product_id': 'Article',
        'jewelry_core.field_stock_inventory_weight_line__weight_after': 'Poids Après (g)',
        'jewelry_core.field_stock_inventory_weight_line__weight_before': 'Poids Avant (g)',
        'jewelry_transactions.field_jewelry_ticket__barcode': 'Code-barres',
        'jewelry_transactions.field_jewelry_ticket__cash_or_metal': 'Espèces/Métal',
        'jewelry_transactions.field_jewelry_ticket__company_id': 'Société',
        'jewelry_transactions.field_jewelry_ticket__currency_id': 'Devise',
        'jewelry_transactions.field_jewelry_ticket__customer_id': 'Client',
        'jewelry_transactions.field_jewelry_ticket__date': 'Date',
        'jewelry_transactions.field_jewelry_ticket__line_ids': 'Lignes',
        'jewelry_transactions.field_jewelry_ticket__name': 'Numéro',
        'jewelry_transactions.field_jewelry_ticket__notes': 'Remarques',
        'jewelry_transactions.field_jewelry_ticket__partner_id': 'Partenaire',
        'jewelry_transactions.field_jewelry_ticket__state': 'État',
        'jewelry_transactions.field_jewelry_ticket__total_versement': 'Total Versé',
        'jewelry_transactions.field_jewelry_ticket__total_verse': 'Total Versé',
        'jewelry_transactions.field_jewelry_ticket__total_net': 'Total Net',
        'jewelry_transactions.field_jewelry_ticket__type': 'Type',
        'jewelry_transactions.field_jewelry_ticket__user_id': 'Utilisateur',
        'jewelry_transactions.field_jewelry_ticket_line__price_subtotal': 'Sous-total',
        'jewelry_transactions.field_jewelry_ticket_line__price_unit': 'Prix Unitaire',
        'jewelry_transactions.field_jewelry_ticket_line__product_id': 'Article',
        'jewelry_transactions.field_jewelry_ticket_line__quantity': 'Quantité',
        'jewelry_transactions.field_jewelry_ticket_line__ticket_id': 'Ticket',
        'jewelry_transactions.field_jewelry_ticket_line__weight': 'Poids (g)',
        'jewelry_transactions.field_casse_melting__date': 'Date',
        'jewelry_transactions.field_casse_melting__line_ids': 'Lignes',
        'jewelry_transactions.field_casse_melting__metal_type_id': 'Type de Métal',
        'jewelry_transactions.field_casse_melting__name': 'Numéro',
        'jewelry_transactions.field_casse_melting__state': 'État',
        'jewelry_transactions.field_casse_melting__total_weight': 'Poids Total (g)',
        'jewelry_transactions.field_casse_melting_line__ticket_line_id': 'Ligne Ticket source',
        'jewelry_transactions.field_casse_melting_line__cost': 'Coût',
        'jewelry_transactions.field_supplier_account__cash_balance': 'Solde Espèces',
        'jewelry_transactions.field_supplier_account__weight_balance': 'Solde Poids (g)',
        'jewelry_transactions.field_supplier_account__partner_id': 'Fournisseur',

        'jewelry_transactions.field_associate_account__capital_balance': 'Solde Capital',
        'jewelry_transactions.field_associate_account__advance_balance': 'Avance sur Profit',
        'jewelry_transactions.field_associate_account__partner_id': 'Associé',

        'jewelry_transactions.field_service_order__date': 'Date',
        'jewelry_transactions.field_service_order__line_ids': 'Lignes',
        'jewelry_transactions.field_service_order__name': 'Numéro',
        'jewelry_transactions.field_service_order__partner_id': 'Client',
        'jewelry_transactions.field_service_order__state': 'État',
        'jewelry_transactions.field_service_order__total': 'Total',

        'jewelry_transactions.field_daily_cash_register__closing_balance': 'Solde de Clôture',
        'jewelry_transactions.field_daily_cash_register__date': 'Date',
        'jewelry_transactions.field_daily_cash_register__difference': 'Décalage',
        'jewelry_transactions.field_daily_cash_register__line_ids': 'Lignes',
        'jewelry_transactions.field_daily_cash_register__name': 'Numéro',
        'jewelry_transactions.field_daily_cash_register__opening_balance': "Solde d'Ouverture",
        'jewelry_transactions.field_daily_cash_register__state': 'État',
        'jewelry_transactions.field_cash_register_line__amount': 'Montant',
        'jewelry_transactions.field_cash_register_line__description': 'Description',
        'jewelry_transactions.field_cash_register_line__register_id': 'Registre',
        'jewelry_transactions.field_cash_register_line__type': 'Type',

        'jewelry_dashboard.field_dashboard_360__company_id': 'Société',
        'jewelry_dashboard.field_dashboard_360__currency_id': 'Devise',
        'jewelry_dashboard.field_dashboard_360__date_from': 'Date Début',
        'jewelry_dashboard.field_dashboard_360__date_to': 'Date Fin',
        'jewelry_dashboard.field_dashboard_360__total_gross_weight': 'Poids Brut Total',
        'jewelry_dashboard.field_dashboard_360__total_net_weight': 'Poids Net Total',
        'jewelry_dashboard.field_dashboard_360__total_purchases': 'Total Achats',
        'jewelry_dashboard.field_dashboard_360__total_sales': 'Total Ventes',
    },
    'ir.model.fields.help': {
        'jewelry_core.field_metal_type__code': 'Ex: OR18, CS21, ARG',
        'jewelry_core.field_product_category__has_weight': 'Oui = vendu au poids, Non = prix fixe',
        'jewelry_core.field_product_template__barcode': "Encode les attributs de l'article (casse, carat, poids, style)",
    },
    'ir.actions.act_window': {
        'jewelry_core.action_gold_rate': "Cours de l'Or",
        'jewelry_core.action_metal_type': 'Types de Métal',
        'jewelry_core.action_stock_inventory_weight': 'Inventaires des Poids',
        'jewelry_transactions.action_jewelry_ticket': 'Tickets de Bijouterie',
        'jewelry_transactions.action_casse_melting': 'Fontes de Casse',
        'jewelry_transactions.action_supplier_account': 'Comptes Fournisseurs',
        'jewelry_transactions.action_associate_account': 'Comptes Associés',
        'jewelry_transactions.action_service_order': 'Bons de Service',
        'jewelry_transactions.action_daily_cash_register': 'Caisse Journalière',
        'jewelry_dashboard.action_dashboard_360': "Tableau de Bord 360°",
    },
    'ir.ui.menu': {
        'jewelry_core.menu_jewelry_core': 'Base',
        'jewelry_core.menu_metal_type': 'Types de Métal',
        'jewelry_core.menu_gold_rate': "Cours de l'Or",
        'jewelry_core.menu_weight_inventory': 'Inventaires des Poids',
        'jewelry_transactions.menu_jewelry_transactions': 'Transactions',
        'jewelry_transactions.menu_jewelry_ticket': 'Tickets',
        'jewelry_transactions.menu_casse_melting': 'Fontes',
        'jewelry_transactions.menu_supplier_account': 'Fournisseurs',
        'jewelry_transactions.menu_associate_account': 'Associés',
        'jewelry_transactions.menu_service_order': 'Bons de Service',
        'jewelry_transactions.menu_daily_cash_register': 'Caisse',
        'jewelry_accounting.menu_jewelry_accounting': 'Comptabilité',
        'jewelry_dashboard.menu_jewelry_dashboard': 'Tableau de Bord',
        'jewelry_dashboard.menu_dashboard_360': "Vue d'Ensemble",
    },
    'ir.sequence': {
        'jewelry_core.seq_stock_inventory_weight': "Inventaire des Poids",
        'jewelry_core.seq_product_barcode': "Code-barres Article",
        'jewelry_transactions.seq_jewelry_ticket': 'Ticket de Bijouterie',
        'jewelry_transactions.seq_casse_melting': 'Fonte de Casse',
        'jewelry_transactions.seq_service_order': 'Bon de Service',
        'jewelry_transactions.seq_daily_cash_register': 'Caisse Journalière',
        'jewelry_transactions.seq_jewelry_ticket_barcode': 'Code-barres Ticket',
    },
    'ir.ui.view_arch_db': {
        'jewelry_core.view_metal_type_form': [
            ('Gold Rates', "Cours de l'Or"),
            ('Active', 'Actif'),
        ],
        'jewelry_core.view_metal_type_search': [
            ('Active', 'Actif'),
        ],
        'jewelry_core.view_product_product_jewelry_form': [
            ('Jewelry', 'Bijouterie'),
        ],
        'jewelry_core.view_product_template_jewelry_form': [
            ('Jewelry', 'Bijouterie'),
        ],
        'jewelry_core.view_stock_inventory_weight_form': [
            ('Reconcile', 'Rapprocher'),
        ],
        'jewelry_core.view_stock_inventory_weight_search': [
            ('Draft', 'Brouillon'),
        ],
        'jewelry_transactions.view_jewelry_ticket_form': [
            ('Generate Barcode', 'Générer Code-barres'),
            ('Register Payment', 'Enregistrer Paiement'),
            ('Payment', 'Paiement'),
            ('Ticket Lines', 'Lignes du Ticket'),
            ('Print', 'Imprimer'),
            ('Created', 'Créé'),
            ('Done', 'Terminé'),
            ('Cancelled', 'Annulé'),
        ],
        'jewelry_transactions.view_jewelry_ticket_tree': [
            ('Number', 'Numéro'),
            ('Customer', 'Client'),
            ('Date', 'Date'),
            ('Total', 'Total'),
        ],
        'jewelry_transactions.view_casse_melting_form': [
            ('Melting Lines', 'Lignes de Fonte'),
            ('Print', 'Imprimer'),
        ],
        'jewelry_transactions.view_supplier_account_form': [
            ('Lines', 'Lignes'),
        ],
        'jewelry_transactions.view_associate_account_form': [
            ('Lines', 'Lignes'),
        ],
        'jewelry_transactions.view_service_order_form': [
            ('Service Lines', 'Lignes de Service'),
            ('Print', 'Imprimer'),
        ],
        'jewelry_transactions.view_daily_cash_register_form': [
            ('Cash Lines', 'Lignes de Caisse'),
        ],
    },
}


def apply_module_translations(env, module_prefix=None):
    Lang = env['res.lang']
    fr_lang = Lang.search([('code', '=', 'fr_FR')], limit=1)
    if not fr_lang:
        Lang.create({'code': 'fr_FR', 'name': 'French / Français', 'active': True})

    def _matches(xml_id):
        if module_prefix is None:
            return True
        return xml_id.startswith(module_prefix + '.')

    for xml_id, value in ALL_TRANSLATIONS.get('ir.model', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'name': value})
        except Exception:
            pass

    for xml_id, value in ALL_TRANSLATIONS.get('ir.model.fields', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'field_description': value})
        except Exception:
            pass

    for xml_id, value in ALL_TRANSLATIONS.get('ir.model.fields.help', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'help': value})
        except Exception:
            pass

    for xml_id, value in ALL_TRANSLATIONS.get('ir.actions.act_window', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'name': value})
        except Exception:
            pass

    for xml_id, value in ALL_TRANSLATIONS.get('ir.ui.menu', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'name': value})
        except Exception:
            pass

    for xml_id, value in ALL_TRANSLATIONS.get('ir.sequence', {}).items():
        if not _matches(xml_id):
            continue
        try:
            rec = env.ref(xml_id, raise_if_not_found=False)
            if rec:
                rec.with_context(lang='fr_FR').write({'name': value})
        except Exception:
            pass

    for view_xml_id, replacements in ALL_TRANSLATIONS.get('ir.ui.view_arch_db', {}).items():
        if not _matches(view_xml_id):
            continue
        try:
            view = env.ref(view_xml_id, raise_if_not_found=False)
            if view and view.arch_db:
                arch = view.arch_db
                for old_str, new_str in replacements:
                    arch = arch.replace(old_str, new_str)
                if arch != view.arch_db:
                    view.with_context(lang='fr_FR').write({'arch_db': arch})
        except Exception:
            pass

    env.cr.commit()
