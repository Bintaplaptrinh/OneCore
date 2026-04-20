---
aliases:
tags:
  - company
title: Company
---

# <% tp.file.title %>

Parent::
Products::
Type::
Segment::

```crm
```

## Projects
*

## Key Contacts
```dataview
TABLE WITHOUT ID
  file.link AS "Name",
  Role AS "Role",
  Phone AS "Phone"
FROM "1_contacts"
WHERE contains(string(Company), this.file.name)
SORT Role ASC
```

## Notes
*
