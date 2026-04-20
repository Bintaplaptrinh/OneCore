---
tags: [dashboard, moc]
---

# Contacts theo Cong ty

```dataview
TABLE WITHOUT ID
  file.link AS "Ten",
  Company AS "Cong ty",
  Role AS "Chuc danh"
FROM "1_contacts"
WHERE contains(tags, "contacts")
SORT Company ASC, file.name ASC
```

## Thong ke

```dataview
TABLE WITHOUT ID
  Company AS "Cong ty",
  length(rows) AS "So nguoi"
FROM "1_contacts"
WHERE contains(tags, "contacts") AND Company != null
GROUP BY Company
SORT length(rows) DESC
```
