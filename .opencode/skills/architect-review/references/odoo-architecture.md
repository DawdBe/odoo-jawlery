# Odoo Architecture Reference

## Module Structure
```
my_module/
  __init__.py
  __manifest__.py
  models/
  views/
  security/
  data/
  reports/
  controllers/
  static/
  i18n/
  tests/
```

## Key Architectural Patterns

### Module Dependencies
- Use `depends` in manifest for explicit dependencies
- Keep dependency chains shallow
- Avoid circular dependencies between custom modules

### Model Inheritance
- `_inherit` for extending existing models (no new table)
- `_name` + `_inherit` for class inheritance (new table)
- `_inherits` for delegation inheritance (shared table)
- Use `fields.Inverse` for computed relationships

### Security Architecture
- ir.model.access.csv: Model-level CRUD per group
- ir.rule: Record-level filtering
- ir.ui.menu: Menu visibility by group
- ir.actions.*: Action visibility

### Multi-Company
- `company_id` Many2one on models
- `company_ids` for shared records
- Record rules with `[('company_id','in',company_ids)]`
- `check_company` decorator for company consistency

### Performance Patterns
- `index=True` on filtered fields
- `_auto_join` for m2o fields in frequent queries
- Prefetching via `read_group` for aggregated data
- Use `search_read` over manual browse+read
- Batch operations: `create()`, `write()`, `unlink()` on recordset

### API Layer
- `@api.model` for model-level methods
- `@api.depends` for computed field dependencies
- `@api.onchange` for UI interactions
- `@api.constrains` for validation
- `@api.autovacuum` for cleanup jobs
