# Odoo Project

Custom Odoo 17.0 project with Docker containerization for easy deployment and development.

## Project Structure

```
├── addons/                  # Custom modules (your business logic)
│   └── my_custom_module/    # Sample module
│       ├── __init__.py
│       ├── __manifest__.py
│       ├── models/          # Python model definitions
│       ├── views/           # XML views (form, tree, search)
│       ├── security/        # Access rights (CSV)
│       ├── data/            # Demo/data XML files
│       ├── i18n/            # Translations
│       └── static/          # Static assets (JS, SCSS, images)
├── config/
│   └── odoo.conf            # Odoo configuration
├── scripts/
│   └── create-module.sh     # Module scaffold generator
├── backups/                 # Database backups (gitignored)
├── Dockerfile               # Custom Odoo image build
├── docker-compose.yml       # Service definitions
├── Makefile                 # Common command shortcuts
└── .gitignore
```

## Quick Start

### First Time Setup

```bash
# 1. Build and start containers
make build
make up

# 2. Access Odoo at http://localhost:8069
#    - Database: postgres
#    - User: admin
#    - Password: admin

# 3. Install your custom module
make install module=my_custom_module
```

### Common Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | View Odoo logs |
| `make build` | Rebuild Docker image |
| `make restart` | Restart all services |

## Development Workflow

### 1. Creating a New Module

```bash
make module name=my_new_module
```

This scaffolds the full module structure under `addons/my_new_module/`.

### 2. Making Code Changes

**Where to put code:**

- **New models** → `addons/<module>/models/<model_name>.py`
- **New views** → `addons/<module>/views/<view_name>.xml`
- **New controllers** → `addons/<module>/controllers/`
- **New reports** → `addons/<module>/reports/`
- **New wizards** → `addons/<module>/wizards/`
- **Security rules** → `addons/<module>/security/ir.model.access.csv`
- **Static assets** → `addons/<module>/static/`

**Editing core Odoo models (inheritance):**

```python
# addons/my_module/models/res_partner.py
from odoo import models, fields

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    custom_field = fields.Char(string="Custom Field")
```

### 3. Making Changes Effective

After editing Python/XML files, upgrade your module:

```bash
make upgrade module=my_module_name
```

For quick iteration during development (no container restart needed):

```bash
make upgrade module=my_module_name
```

The `--dev=all` mode auto-reloads Python changes — but XML/view changes still need a module upgrade.

### 4. Full Upgrade Cycle

```bash
make upgrade module=my_module    # Apply code changes
# Check in Odoo UI
# Repeat
```

### 5. Testing

```bash
# Run tests for a specific module
make test module=my_module

# Run all tests
make test-all

# Check Odoo logs
make logs
```

**To write tests:**

```python
# addons/my_module/tests/test_example.py
from odoo.tests import common

class TestExample(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env['my_module.example']

    def test_create_record(self):
        record = self.model.create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')
```

### 6. Database Management

```bash
make backup           # Backup database to ./backups/
make db-drop          # Reset database
make db-shell         # Open psql console
```

## Git Workflow

### Initial Setup

```bash
git init
git add .
git commit -m "Initial project setup"
git remote add origin <your-repo-url>
git push -u origin main
```

### Development Flow

```bash
git checkout -b feature/my-new-feature
# ... make code changes ...
make upgrade module=my_module    # Test changes
git add addons/my_module/
git commit -m "[FIX/ADD/REF] description of changes"
git push origin feature/my-new-feature
# Create PR on GitHub → merge to main
```

### Best Practices

1. **Never commit** `data/` directory (DB data, filestore, sessions)
2. **Never commit** `__pycache__/` or `.pyc` files
3. **Module versions** in `__manifest__.py` — bump on significant changes
4. **Commit messages** should be clear: `[ADD] sale_custom: add discount field to sale.order`
5. **Branch naming**: `feature/<name>`, `fix/<name>`, `chore/<name>`
6. **Tag releases**: `git tag v1.0.0 && git push origin v1.0.0`

## Deployment

To deploy on a server:

```bash
git clone <repo-url>
cd odoo-project
make build
make up
```

For production, set proper environment variables and use a reverse proxy (nginx/traefik).

## Fixes Applied

| Issue | Before | After |
|-------|--------|-------|
| Empty `odoo-core` mount over core files | `./odoo-core:/usr/lib/python3/dist-packages/odoo` — hid all Odoo core files | Removed; core customization done via inheritance in custom modules |
| No custom Docker image | Used raw `odoo:17.0` image | `Dockerfile` for custom builds |
| Data in bind mount | `./data/db:/var/lib/postgresql/data` | Named volumes (`odoo-db-data`, `odoo-data`) |
| No health checks | DB dependency without condition | `healthcheck` + `condition: service_healthy` |
| Hashed admin password | `$pbkdf2-sha512$...` | Plain text `admin` |
| No `.gitignore` | Absent — risk of committing DB data | Proper `.gitignore` |
| No Makefile | Manual docker commands | Shortcuts for common tasks |
| No module scaffold | Empty `addons/` | `create-module.sh` + sample `my_custom_module` |
