def migrate(cr, version):
    # Merge obsolete metal types into canonical ones
    merges = [
        ('jewelry_core', 'metal_casse18', 'jewelry_core', 'metal_or_18k'),
        ('jewelry_core', 'metal_casse21', 'jewelry_core', 'metal_or_21k'),
        ('jewelry_core', 'metal_or750', 'jewelry_core', 'metal_or_18k'),
    ]
    delete_xml_ids = [
        ('jewelry_core', 'metal_casse_18k'),
        ('jewelry_core', 'metal_casse22'),
        ('jewelry_core', 'metal_casse14'),
    ]

    def _resolve_id(module, name):
        cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'metal.type'",
            (module, name)
        )
        row = cr.fetchone()
        return row[0] if row else None

    for obs_m, obs_n, can_m, can_n in merges:
        obs_id = _resolve_id(obs_m, obs_n)
        can_id = _resolve_id(can_m, can_n)
        if obs_id is None or can_id is None or obs_id == can_id:
            continue
        cr.execute('UPDATE gold_rate_history SET metal_type_id = %s WHERE metal_type_id = %s', (can_id, obs_id))
        cr.execute('UPDATE product_template SET metal_type_id = %s WHERE metal_type_id = %s', (can_id, obs_id))

    for mod, name in delete_xml_ids:
        type_id = _resolve_id(mod, name)
        if type_id is None:
            continue
        cr.execute('DELETE FROM gold_rate_history WHERE metal_type_id = %s', (type_id,))
        cr.execute('UPDATE product_template SET metal_type_id = NULL WHERE metal_type_id = %s', (type_id,))

    cr.execute("""
        DELETE FROM gold_rate_history
        WHERE metal_type_id IN (
            SELECT m.id FROM metal_type m
            LEFT JOIN ir_model_data imd ON imd.model = 'metal.type' AND imd.res_id = m.id
            WHERE imd.id IS NULL
        )
    """)
    cr.execute("""
        UPDATE product_template
        SET metal_type_id = NULL
        WHERE metal_type_id IN (
            SELECT m.id FROM metal_type m
            LEFT JOIN ir_model_data imd ON imd.model = 'metal.type' AND imd.res_id = m.id
            WHERE imd.id IS NULL
        )
    """)
