---
tags: [dashboard, graph]
---
# Graph - Ma tran Quan he

## Huong dan su dung Juggl

Mo file nay trong Obsidian, sau do:
1. Click chuot phai > **Open Juggl graph**
2. Hoac su dung command palette > **Juggl: Open local graph**

### Juggl Code Block (auto-render)

```juggl
layout: force-directed
limit: 100
```

## Color Legend

| Mau | Loai | Shape |
|-----|------|-------|
| Xanh duong (#4A90D9) | Contact | Ellipse |
| Cam (#E67E22) | Company | Rectangle |
| Xanh la (#27AE60) | Project | Diamond |
| Tim (#8E44AD) | Developer/Client | Rectangle |
| Do (#C0392B) | Main Contractor | Hexagon |
| Vang (#F39C12) | Consultant | Triangle |
| Xam (#95A5A6) | Meeting | Octagon |

## Quick Graph Views

### Tat ca Stakeholders cua du an
Mo bat ky file trong `_project/` > Click phai > Open Juggl > Expand nodes

### Network cua 1 contact
Mo bat ky file trong `_contacts/` > Click phai > Open Juggl > Expand

### Company relationships
Mo bat ky file trong `clients/`, `MCs/`, `consultants/` > Open Juggl
