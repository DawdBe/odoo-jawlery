give me some youtube vedios for individul that try the house made trape for dobab in arabic# Verification Plan — Jewelry System Design

## How to verify all diagrams are correct

### Step 1 — Generate & read all diagrams

Generate each `.puml` as PNG (PlantUML extension or CLI), then read in this order:

| #   | File                            | What to check                                                                                     |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| 1   | `class_diagram.puml`            | Every model makes sense. No orphan fields. All `[compute]` / `[compute store]` annotations correct. |
| 2   | `er_diagram.puml`               | Matches `class_diagram.puml`. No missing tables/fields. FK relationships correct.                 |
| 3   | `architecture_overview.puml`    | 4 packages with correct models. No dangling references.                                           |
| 4   | `component_diagram.puml`        | Module dependencies reflect the 4-package split.                                                  |
| 5   | `deployment_diagram.puml`       | Physical deployment correct (no MRP, no sale/pos).                                                |
| 6   | `use_case.puml`                 | All expected UC present: gold rate, ticket, fasonage, cash register, etc.                         |
| 7   | `seq_cours_or.puml`             | Single `market_rate` per metal type. Bursa + spread → market. No per-casse rates.                 |
| 8   | `seq_double_operation.puml`     | Price = weight × market_rate. No `main d'oeuvre`. `price_unit` stored as snapshot.                |
| 9   | `seq_fasonage.puml`             | `min_profit_percentage` set → `validate_selling_price()` → alert if below threshold.              |
| 10  | `seq_supplier_dual_credit.puml` | `weight_balance`/`cash_balance` are `[compute store]` — triggered by purchase orders / cash lines. |
| 11  | `seq_travel_cash.puml`          | `is_travel_cash` on `cash.register.line`. Balances are `[compute store]`. Field names use `_id` suffix. |
| 12  | `seq_cash_register.puml`        | Daily closure flow. `closing_balance` = physical count (stored, not computed).                    |
| 13  | `seq_paiement_partiel.puml`     | Payment status flow (impaye → partiel → paye).                                                    |
| 14  | `seq_bilan_global.puml`         | Single global bilan (no dual legal/real accounting).                                              |
| 15  | `state_bon_lifecycle.puml`      | Ticket states: en_stock → en_fasonage → termine → donne_au_client.                                |
| 16  | `activity_cloture_caisse.puml`  | Cash closure steps complete with travel cash reconciliation.                                      |
| 17  | `sequence_diagram.puml`         | Combined file — spot-check sections match their individual diagrams.                              |

### Step 2 — Logic validations

| Concept               | Question                                                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Gold rate**         | One `market_rate` per `metal.type`. API récupère le bursa (référence). L'admin fixe le spread ou saisit le market_rate directement. |
| **Product price**     | Every sale computes `weight × market_rate` at that moment. Snapshot stored on `ticket.line.price_unit` for accounting.              |
| **Fasonage profit**   | If atelier cost = 11,100 DZD and min_profit = 30%, minimum sale = 14,430 DZD. Alert if below.                                       |
| **Supplier balance**  | Both `purchase.order` and `cash.register.line` carry all data needed to compute both balances.                                      |
| **Travel cash**       | `is_travel_cash` boolean + dedicated `account.journal` covers all travel scenarios.                                                 |
| **Dashboard 360°**    | `TransientModel` with all `[compute]` fields — no data persisted.                                                                   |
| **Non-stored prices** | `product.template` stores only static attributes (weight, metal, style). No pricing fields.                                         |

### Step 3 — Cross-reference with design doc

1. Open `docs/jewelry-system-design-odoo.md`
2. Search for every model name — verify it exists in the diagrams
3. If something is in the doc but not in any diagram → it's undocumented (gap)

### Step 4 — Quick grep

```bash
# Should return NOTHING (removed models / old pricing terms):
grep -rn "pricing.rule\|barcode.generate.wizard\|report.global.balance\|report.profit.margin\|report.weights.summary\|main d.oeuvre\|Coût main\|Déchet%\|Marge configurée\|static_price\|profit_percentage\|margin.category\|current_weight" docs/diagrams/

# Should only appear as [compute store] or explanatory notes:
grep -rn "weight_balance\|cash_balance" docs/diagrams/ --include="*.puml"

# Should only appear as _id suffix:
grep -rn "partner=FRS\|partner=AT\|partner = \|journal =" docs/diagrams/ --include="*.puml"
```

### Step 5 — Read the combined sequence diagram

`sequence_diagram.puml` is the master file merging all 8 sequences. Open it and spot-check 2-3 random sections against the individual files to ensure they stayed in sync.

---

## Pass/Fail

If all 5 steps pass without surprises → the design is consistent and ready for development.
If any step finds an issue → fix the diagram, then re-run Steps 4-5.
