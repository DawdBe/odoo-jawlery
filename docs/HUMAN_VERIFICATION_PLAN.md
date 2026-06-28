# Human Verification Plan — Odoo Gold Store Implementation

## Purpose

This plan guides a human reviewer through checking the AI-generated Odoo modules against the design documents, session decisions, and Odoo best practices.

---

## Phase 0 — Environment Setup (Docker)

### Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- Git
- Port 8069 free (Odoo web interface)
- Port 5432 free (PostgreSQL — internal to Docker, no conflict needed)

### Project Structure

```
odoo-project/
├── addons/                    # Custom modules (mounted into container)
│   ├── jewelry_core/
│   ├── jewelry_transactions/
│   ├── jewelry_accounting/
│   └── jewelry_dashboard/
├── config/
│   └── odoo.conf              # Odoo configuration
├── docker-compose.yml         # Service definitions
├── Dockerfile                 # Custom Odoo image
├── Makefile                   # Command shortcuts
├── data/                      # PostgreSQL data (gitignored, named volume)
├── backups/                   # DB dumps (gitignored)
└── odoo-core/                 # Not mounted (empty dir — core stays in image)
```

### Step 0.1 — First Launch

```bash
# Build the custom Odoo image (installs dependencies, copies addons)
make build

# Start all services (Odoo + PostgreSQL)
make up

# Wait ~30s for first-time DB init. Check logs:
make logs

# Access Odoo at http://localhost:8069
# Create database:
#   - Database Name: bijouterie
#   - Master Password: admin
#   - Default Language: French / English
#   - Load Demonstration Data: NO (start clean)
```

### Step 0.2 — Stop / Restart

```bash
make down        # Stop all containers (data persists in named volumes)
make restart     # Restart services
make logs        # Tail Odoo logs
```

### Step 0.3 — Install Modules (in dependency order)

```bash
# 1. Core socle — must be first
make install module=jewelry_core
make upgrade module=jewelry_core

# 2. Business logic — depends on jewelry_core + account + purchase
make install module=jewelry_transactions
make upgrade module=jewelry_transactions

# 3. Accounting — depends on jewelry_transactions
make install module=jewelry_accounting
make upgrade module=jewelry_accounting

# 4. Dashboard — depends on jewelry_accounting
make install module=jewelry_dashboard
make upgrade module=jewelry_dashboard

# Check all installed without errors:
make logs | grep ERROR
```

### Step 0.4 — Useful Commands During Testing

```bash
make upgrade module=jewelry_core          # Re-apply code changes
make test module=jewelry_transactions      # Run automated tests
make backup                                # Dump database to ./backups/
make db-drop                               # Reset database (start fresh)
make db-shell                              # Open psql console on the DB

# After code edits, faster iteration:
make upgrade module=jewelry_core && make logs | tail -20
```

### Step 0.5 — Creating Test Data

After all modules are installed, create some base data via UI or data files:

```bash
# Install demo data for the jewelry modules (if any):
# Or manually via UI: Settings > Technical > Sequences
```

### Troubleshooting Docker

| Symptom | Fix |
|---------|-----|
| `port already allocated` | Change port in `docker-compose.yml` or stop other containers |
| `permission denied` on addons | `chown -R 101:101 addons/` (Odoo runs as uid 101) |
| Module not found after install | `docker exec -it odoo-project-odoo-1 bash -c "ls /mnt/extra-addons/"` to verify mount |
| DB connection refused | `docker compose restart db` then wait 10s |
| Changes not reflected | `make upgrade module=xyz` — XML views need module upgrade to reload |

---

## Phase 1 — Structural Verification (no data)

### Step 1: Module Loading

Check each module installs without errors. Look for these common issues:

| Symptom | Likely Cause |
|---------|-------------|
| `ModuleNotFoundError` | Missing `__init__.py` import or wrong dependency |
| `AccessError` on menus | Missing `ir.model.access.csv` entry |
| `FieldNotFound` | Wrong field name in view XML |
| `ConstraintError` | Data XML violates SQL constraint |
| View renders blank | Mismatched `model` attribute in XML view record |

### Step 2: Models Checklist

Open **Settings > Technical > Models** and verify each model exists with correct fields:

| Module | Expected Models |
|--------|----------------|
| jewelry_core | `metal.type`, `gold.rate.history`, `stock.inventory.weight`, `stock.inventory.weight.line` |
| jewelry_core (inherit) | `product.template`, `product.product`, `product.category`, `stock.quant`, `stock.move`, `res.partner` |
| jewelry_transactions | `jewelry.ticket`, `jewelry.ticket.line`, `product.promotion`, `associate.account`, `associate.transaction`, `supplier.account`, `casse.melting`, `casse.melting.line`, `service.order`, `atelier.price.table`, `daily.cash.register`, `cash.register.line` |
| jewelry_accounting (inherit) | `account.move`, `account.move.line` |
| jewelry_dashboard | `dashboard.360` (TransientModel — won't create a table) |

### Step 3: Computed Fields Check

Verify `[compute store]` fields actually trigger correctly. Navigate to each form and check the computed values:

- **jewelry.ticket**: Create ticket → add lines → check `total_cash_in/out/balance/total_remise` auto-calculate
- **supplier.account**: Create purchase order → check `weight_balance`/`cash_balance` update
- **associate.account**: Create associate transaction → check `capital_balance`/`advance_balance` update
- **daily.cash.register**: Open register → add lines → check `expected_balance` updates; close → check `difference`
- **casse.melting**: Create melting with weight_before/after → check `wastage_weight`, `refined_value`, `profit`

### Step 4: Install Sequence & Dependencies

Verify:
- `jewelry_core` depends on: `product`, `stock`, `uom`
- `jewelry_transactions` depends on: `jewelry_core`, `account`, `purchase`
- `jewelry_accounting` depends on: `jewelry_transactions`, `account`
- `jewelry_dashboard` depends on: `jewelry_accounting`

Check in **Settings > Technical > Modules > [Module] > Dependencies**.

---

## Phase 2 — Functional Verification (with test data)

### Step 5: Metal Types

1. Go to **Bijouterie > Core > Configuration > Metal Types**
2. ✅ Menu visible and loads correctly
3. ✅ Default data loaded: Casse18, Casse21, Casse22, Casse14, Or 750, Argent casse, Argent Mar.
4. ✅ Create a new metal type, save, edit
5. ✅ Delete a metal type → confirm it works or is blocked by FK

### Step 6: Gold Rates

1. Go to **Bijouterie > Core > Configuration > Gold Rates**
2. ✅ Create a rate for Casse18: bursa=8000, market_spread=200, market_rate=8200
3. ✅ Create another rate, set `is_active` to see filtering
4. ✅ Check `effective_date` defaults to today

### Step 7: Products

1. Go to **Products** (Odoo native)
2. ✅ Product form shows "Jewelry" tab with metal_type, category, style, weights
3. ✅ Create product with metal_type=Casse18, gross_weight=50, stone_weight=5 → net_weight=45
4. ✅ Check `net_weight` auto-computes

### Step 8: Partners

1. Go to **Contacts**
2. ✅ Create a partner with `partner_type = Atelier (AT)`, check `is_atelier` auto-set
3. ✅ Create a supplier with `partner_type = Fournisseur (FRS)`
4. ✅ Create a client

### Step 9: Tickets (Core Transaction)

1. Go to **Bijouterie > Transactions > Tickets**
2. ✅ Create a new ticket with a partner
3. ✅ Add a line: type=Vente, product=your_product, weight=10, price_unit=82000
4. ✅ Add another line: type=Versé, amount=50000
5. ✅ Check totals compute: total_cash_in, total_cash_out, balance
6. ✅ Try `payment_status` transitions: impaye → partiel → paye
7. ✅ Try `product_status` transitions
8. ✅ Create a ticket with a Remise line → verify `total_remise` updates

### Step 10: Supplier Accounts

1. Go to **Bijouterie > Transactions > Supplier Accounts**
2. ✅ Create an account for a supplier partner
3. ✅ Create a purchase order for the supplier with gold_weight_in=100
4. ✅ Create a cash register line linked to the supplier (type=entree, amount=50000)
5. ✅ Check supplier account: weight_balance and cash_balance should reflect the data

### Step 11: Service Orders

1. Go to **Bijouterie > Transactions > Service Orders**
2. ✅ Create a service order for fasonage
3. ✅ Set raw_gold_weight=50, finished_weight=48 → wastage=2
4. ✅ Set up atelier price for the atelier partner (Casse18, massif, cost=500/g)
5. ✅ Set style=massif on the service → check `price_from_table` computes (48 × 500 = 24,000)
6. ✅ Set min_profit_percentage=30 → `validate_selling_price(30000)` should pass

### Step 12: Casse Melting

1. Go to **Bijouterie > Transactions > Casse Melting**
2. ✅ Create a melting with weight_before=100, weight_after=95
3. ✅ Set metal_type_result=Casse18, ensure a market_rate exists
4. ✅ Set total_cost=700,000 → profit should compute

### Step 13: Cash Register

1. Go to **Bijouterie > Transactions > Cash Registers**
2. ✅ Open a new register with opening_balance=100,000
3. ✅ Add a line: type=entree, amount=200,000, is_travel_cash=true
4. ✅ Add another line: type=sortie, amount=50,000
5. ✅ Check expected_balance: 100,000 + 200,000 - 50,000 = 250,000
6. ✅ Close the register, set closing_balance=250,000 → difference=0
7. ✅ Set closing_balance=249,500 → difference=-500
8. ✅ Fill in bill breakdown fields

### Step 14: Associate Accounts

1. Go to **Contacts** → find an associate partner
2. ✅ Create an associate.account for them
3. ✅ Create a capital_deposit transaction for 1,000,000 DZD
4. ✅ Create an advance_profit transaction for 50,000 DZD
5. ✅ Check capital_balance=1,000,000, advance_balance=50,000

### Step 15: Price at weight sale

1. ✅ Create a ticket with a product. Verify the price is entered manually (no auto-pricing on product).
2. ✅ This confirms: price = weight × market_rate at time of sale → stored as snapshot on ticket line.

### Step 16: Dashboard 360°

1. Go to **Bijouterie > Dashboard 360°**
2. ✅ Dashboard loads and shows computed values
3. ✅ Gold rates display correctly
4. ✅ Click Refresh to recompute

---

## Phase 3 — Edge Cases & Negative Tests

### Step 17: Security

1. ✅ Create a new user with no jewelry module rights → should see no menu items
2. ✅ Create a "Vendeur" user with only base.group_user → can read tickets, cannot unlink
3. ✅ Try to delete a ticket with lines → should be blocked (active=False only)
4. ✅ Verify access.csv doesn't grant `perm_unlink` to regular users on critical models

### Step 18: Edge Cases

1. ✅ **Empty state**: Create ticket with no lines → totals should be 0, not crash
2. ✅ **Zero weight**: product with weight=0 → estimated_value=0
3. ✅ **Negative numbers**: Try negative weight on ticket line → should not crash (business logic allows returns)
4. ✅ **Missing gold rate**: supplier account with no rate → get_current_rate returns 0.0, no crash
5. ✅ **Delete cascade**: Delete a ticket → all its lines should be deleted
6. ✅ **Concurrent edits**: Two users edit same ticket → Odoo's last-write-wins

### Step 19: Data Integrity

Verify SQL constraints:
1. `atelier.price.table`: try duplicate (same atelier + style + metal_type) → should raise error
2. `jewelry.ticket`: delete a ticket with confirmed state → should archive (active=False), not delete

---

## Phase 4 — Cross-Reference with Design

### Step 20: Compare Against Class Diagram

- ✅ Every model in `class_diagram.puml` exists in the code
- ✅ Every field annotated `[compute]` or `[compute store]` has the corresponding `@api.depends`
- ✅ Every field type matches (Many2one vs Many2many, Monetary vs Float, etc.)
- ✅ Every class method exists in the Python code

### Step 21: Compare Against ER Diagram

- ✅ Every entity in `er_diagram.puml` has a matching model
- ✅ FK relationships match Many2one fields
- ✅ Field types match (varchar ↔ Char, numeric ↔ Monetary/Float)

### Step 22: Session Decisions Checklist

| Decision | Status |
|----------|--------|
| 4 modules (not 9) | ✅ |
| Unified `jewelry.ticket` (not multiple bon types) | ✅ |
| Dual gold rate (bursa + market with spread) | ✅ |
| Supplier dual balance (weight + cash) `[compute store]` | ✅ |
| Travel cash = `is_travel_cash` on `cash.register.line` | ✅ |
| No stored pricing fields on `product.template` | ✅ |
| Price = weight × market_rate at time of sale | ✅ |
| Associate accounts with capital/advance balances | ✅ |
| Dashboard 360° as TransientModel | ✅ |
| Bon deletion = archived (active=False), not deleted | ✅ |
| No dual accounting (legal/real) | ✅ |
| No CRM/marketing | ✅ |
| No audit module | ✅ |

---

## Phase 5 — Odoo Best Practices Audit

### Step 23: Code Quality

Check a few random Python files for:

1. ✅ `_description` present on every model
2. ✅ `_inherit` used instead of modifying core files
3. ✅ `@api.depends` annotations on all computed fields
4. ✅ `super().create()` / `super().write()` called in overridden CRUD methods
5. ✅ `self.ensure_one()` before computing single-record values
6. ✅ No raw SQL unless absolutely necessary
7. ✅ No N+1 queries (no `search()` inside loops)

### Step 24: XML Quality

1. ✅ All views have unique `id` and `name`
2. ✅ All `res_model` attributes match actual model names
3. ✅ `ir.actions.act_window` have correct `view_mode`
4. ✅ Menuitems have valid `parent` and `action`
5. ✅ Inherited views use correct `ref` in `inherit_id`

---

## Scoring

Count issues found:

| Severity | Count | Action |
|----------|-------|--------|
| 🔴 Critical (module can't install) | — | Must fix before proceeding |
| 🟠 Major (feature broken) | — | Fix before moving to next phase |
| 🟡 Minor (UI/UX issue, non-blocking) | — | Log for later |
| 🔵 Suggestion (improvement) | — | Consider for v2 |

---

## After Verification

Once all checks pass:

1. Commit the code:
   ```bash
   git add addons/jewelry_*
   git commit -m "[ADD] 4 custom jewelry modules — core, transactions, accounting, dashboard"
   ```

2. Tag the design milestone:
   ```bash
   git tag v0.1-design-final
   ```
