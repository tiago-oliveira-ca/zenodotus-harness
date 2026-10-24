# Angular UI Design System — Component SCSS Patterns

Extracted from `../SKILL.md` — the canonical component SCSS catalog. Reuse these
blocks verbatim for new components; the "Quick Reference: Which class to use"
table in `SKILL.md` indexes into the patterns below.

---

## Component SCSS Patterns

These are the canonical patterns extracted from the existing component files. Reuse
them verbatim for new components — don't invent variations.

### Panel (primary glass card)

Used by every admin panel (org-users, org-roles, org-permissions, org-applications).

```scss
.panel {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 14px 30px rgba(32, 49, 91, 0.14);
  padding: 12px 12px 10px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
}

.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  h2 {
    margin: 0;
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
}
```

### List Row (interactive item)

Used for any list of selectable or clickable items.

```scss
.panel-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow: auto;
  padding-right: 2px;

  &.loading {
    align-items: center;
    justify-content: center;
    min-height: 200px;
  }
}

.list-row {
  border-radius: 12px;
  border: 1px solid rgba(134, 154, 211, 0.2);
  background: rgba(255, 255, 255, 0.55);
  color: #2e3961;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
  min-height: 46px;
  display: grid;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;

  &:hover {
    background: rgba(189, 206, 248, 0.34);
    border-color: rgba(109, 134, 205, 0.4);
    transform: translateY(-1px);
  }

  &.active {
    background: rgba(143, 166, 233, 0.36);
    border-color: rgba(86, 112, 185, 0.5);
  }
}

// When list-row is a <button>
button.list-row {
  width: 100%;
  text-align: left;
  font: inherit;
  border: 0;
}

// Row layout helpers
.row-main {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  font-size: 15px;
  font-weight: 500;

  span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
}

.row-meta {
  font-size: 13px;
  color: #57658f;
  white-space: nowrap;
}

.row-controls {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
}
```

### Embedded Form (inline create/edit form inside a panel)

```scss
.embedded-form {
  border: 1px solid rgba(150, 169, 220, 0.35);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.5);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.embedded-form-title {
  font-size: 13px;
  font-weight: 600;
  color: #34426d;
}

.embedded-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;

  input,
  select {
    min-height: 34px;
    border-radius: 8px;
    border: 1px solid rgba(150, 169, 220, 0.35);
    background: rgba(255, 255, 255, 0.82);
    padding: 0 10px;
    font: inherit;
    color: #2a365e;
  }
}

.embedded-form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
```

### Inline Search Bar

```scss
.inline-search {
  border-radius: 10px;
  border: 1px solid rgba(150, 169, 220, 0.35);
  background: rgba(255, 255, 255, 0.5);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 8px;

  input {
    border: 0;
    outline: 0;
    background: transparent;
    color: #2a365e;
    font-size: 14px;
    font-family: inherit;
    width: 100%;
  }
}
```

### Avatar (user initial badge)

```scss
.avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #39508f;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(121, 144, 206, 0.35);
  text-transform: uppercase;
}
```

### Empty State

```scss
.empty {
  color: #5f6d94;
  border-radius: 10px;
  border: 1px dashed rgba(126, 145, 198, 0.4);
  background: rgba(255, 255, 255, 0.46);
  text-align: center;
  padding: 12px;
  font-size: 13px;
}
```

### Status Badge

```scss
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;

  &.active   { background: rgba(52, 199, 89, 0.15);   color: #34c759; }
  &.inactive { background: rgba(142, 142, 147, 0.15); color: #8e8e93; }
  &.pending  { background: rgba(255, 149, 0, 0.15);   color: #ff9500; }
  &.error    { background: rgba(255, 59, 48, 0.15);   color: #ff3b30; }
}
```

### Alert Banner

```scss
.alert {
  padding: 11px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 10px;
  font-size: 13px;

  &.alert-danger {
    color: #b42318;
    border: 1px solid rgba(255, 59, 48, 0.24);
    background: rgba(255, 59, 48, 0.08);
  }
}
```

### Glass Container (generic utility)

```scss
.glass-container {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
```

### Detail Strip (info cards in a row)

```scss
.detail-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(220px, 1fr));

  @media (max-width: 980px) { grid-template-columns: 1fr; }
}

.detail-card {
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  background: rgba(255, 255, 255, 0.56);
  padding: 12px;
  box-shadow: 0 10px 22px rgba(30, 44, 80, 0.12);

  h3 { margin: 0 0 8px; font-size: 16px; font-weight: 600; }
}

.label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6a749b;
  margin-bottom: 2px;
}
```
