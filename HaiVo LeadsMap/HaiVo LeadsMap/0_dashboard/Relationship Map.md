---
tags: [dashboard, moc]
---

# Ma tran Quan he

## Cach doc

```
Contact --> Company --> Project --> Client (Chu dau tu)
                           |
                           +-- thi cong boi --> MC (Tong thau)
                           +-- tu van boi --> Consultant
```

## Tim nhanh

### Contacts theo Cong ty

```dataview
TABLE WITHOUT ID
  file.link AS "Contact",
  Company AS "Cong ty",
  Role AS "Vai tro"
FROM "1_contacts"
WHERE contains(tags, "contacts") AND Company != null
SORT Company ASC
```

### Du an va Stakeholders

```dataview
TABLE WITHOUT ID
  file.link AS "Du an",
  length(file.outlinks) AS "So lien ket"
FROM "_project"
WHERE contains(tags, "project")
SORT file.name ASC
```

## Workflow them contact moi

1. Chup namecard, bo vao `2_namecards/`
2. Chay `python sync_contacts.py` (tu tao .md + JSON + Excel)
3. Mo file .md moi, dien `## Project` va `## Link`
4. Mo project file, them contact vao `key_contacts:`
