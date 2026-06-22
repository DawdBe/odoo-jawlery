#!/bin/bash
set -e

MODULE_NAME=$1

if [ -z "$MODULE_NAME" ]; then
    echo "Usage: $0 <module_name>"
    exit 1
fi

BASE_DIR="addons/$MODULE_NAME"

if [ -d "$BASE_DIR" ]; then
    echo "Error: Module '$MODULE_NAME' already exists in $BASE_DIR"
    exit 1
fi

mkdir -p "$BASE_DIR/models"
mkdir -p "$BASE_DIR/views"
mkdir -p "$BASE_DIR/security"
mkdir -p "$BASE_DIR/data"
mkdir -p "$BASE_DIR/static/description"
mkdir -p "$BASE_DIR/static/src/js"
mkdir -p "$BASE_DIR/static/src/scss"
mkdir -p "$BASE_DIR/i18n"

cat > "$BASE_DIR/__init__.py" << 'PYEOF'
from . import models
PYEOF

cat > "$BASE_DIR/models/__init__.py" << 'PYEOF'
from . import example_model
PYEOF

cat > "$BASE_DIR/models/example_model.py" << PYEOF
from odoo import models, fields, api


class ${MODULE_NAME^}Example(models.Model):
    _name = '${MODULE_NAME}.example'
    _description = '${MODULE_NAME^} Example'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string='State', default='draft')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
PYEOF

cat > "$BASE_DIR/views/example_model_views.xml" << XMLEOF
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_${MODULE_NAME}_example_tree" model="ir.ui.view">
        <field name="name">${MODULE_NAME}.example.tree</field>
        <field name="model">${MODULE_NAME}.example</field>
        <field name="arch" type="xml">
            <tree>
                <field name="name"/>
                <field name="state"/>
                <field name="active"/>
            </tree>
        </field>
    </record>

    <record id="view_${MODULE_NAME}_example_form" model="ir.ui.view">
        <field name="name">${MODULE_NAME}.example.form</field>
        <field name="model">${MODULE_NAME}.example</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="state"/>
                            <field name="active"/>
                        </group>
                        <group>
                            <field name="company_id"/>
                        </group>
                    </group>
                    <group>
                        <field name="description"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="view_${MODULE_NAME}_example_search" model="ir.ui.view">
        <field name="name">${MODULE_NAME}.example.search</field>
        <field name="model">${MODULE_NAME}.example</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
                <field name="state"/>
                <separator/>
                <filter name="active" string="Active" domain="[('active','=',True)]"/>
                <filter name="inactive" string="Inactive" domain="[('active','=',False)]"/>
            </search>
        </field>
    </record>

    <record id="action_${MODULE_NAME}_example" model="ir.actions.act_window">
        <field name="name">${MODULE_NAME^} Examples</field>
        <field name="res_model">${MODULE_NAME}.example</field>
        <field name="view_mode">tree,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Create your first ${MODULE_NAME} example!
            </p>
        </field>
    </record>

    <menuitem id="menu_${MODULE_NAME}_root" name="${MODULE_NAME^}" sequence="100"/>
    <menuitem id="menu_${MODULE_NAME}_example" name="Examples" parent="menu_${MODULE_NAME}_root" action="action_${MODULE_NAME}_example"/>
</odoo>
XMLEOF

cat > "$BASE_DIR/security/ir.model.access.csv" << CSVEOF
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_${MODULE_NAME}_example_user,${MODULE_NAME}.example.user,model_${MODULE_NAME}_example,base.group_user,1,1,1,1
access_${MODULE_NAME}_example_manager,${MODULE_NAME}.example.manager,model_${MODULE_NAME}_example,base.group_system,1,1,1,1
CSVEOF

cat > "$BASE_DIR/__manifest__.py" << PYEOF
{
    'name': '${MODULE_NAME^}',
    'version': '1.0.0',
    'category': 'Custom',
    'summary': 'Custom ${MODULE_NAME^} module',
    'description': """
        ${MODULE_NAME^} - Custom Odoo Module
        =====================================
        This is a scaffold module for ${MODULE_NAME^}.
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/example_model_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
PYEOF

cat > "$BASE_DIR/static/description/index.html" << HTMLEOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>${MODULE_NAME^}</title>
</head>
<body>
    <h1>${MODULE_NAME^}</h1>
    <p>Custom Odoo module for ${MODULE_NAME^}.</p>
</body>
</html>
HTMLEOF

echo "✓ Module '$MODULE_NAME' created at $BASE_DIR"
echo ""
echo "Next steps:"
echo "  1. make build     # Rebuild the Docker image"
echo "  2. make up        # Start containers"
echo "  3. make upgrade module=$MODULE_NAME   # Install/upgrade the module"
