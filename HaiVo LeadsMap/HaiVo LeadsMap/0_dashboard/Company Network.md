---
tags: [dashboard, moc]
---

# Mang luoi Cong ty

## Chu dau tu (Developers)

```dataview
LIST WITHOUT ID file.link
FROM "3_company/clients"
SORT file.name ASC
```

## Tong thau (Main Contractors)

```dataview
LIST WITHOUT ID file.link
FROM "3_company/mc"
SORT file.name ASC
```

## Tu van (Consultants)

```dataview
LIST WITHOUT ID file.link
FROM "3_company/design"
SORT file.name ASC
```
