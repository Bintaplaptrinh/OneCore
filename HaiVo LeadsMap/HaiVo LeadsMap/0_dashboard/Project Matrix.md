---
tags: [dashboard, moc]
---

# Ma tran Du an

| Du an | Chu dau tu | Tong thau | Tu van | Dia diem | Ban giao |
|-------|-----------|-----------|--------|----------|----------|
| [[prj-CT1-CT2-TimeSquareDanang]] | [[client-KimLongNam]] | [[mc-Newtecons]] |  | Danang | 2026-2027 |
| [[prj-EatonPark]] | [[client-GamudaLand]] | [[mc-CTD]], [[mc-HBC]] | [[consultant-AGINOGO]], [[consultant-TWAsia]] | HCM | 2026-2027 |
| [[prj-GarryaDanang]] | [[client-ABankGroup]] |  | [[consultant-Astra]] | Danang |  |
| [[prj-HH01-TrungVan]] | [[client-TasecoLand]] | [[mc-ICON4]] | [[consultant-VNCC]], [[consultant-GroupGSA]] | Hanoi | 2027 |
| [[prj-LancasterLegacy]] | [[client-TTGHolding]] | [[mc-Central]] | [[consultant-Aedas]] | HCM | 2026 |
| [[prj-Lumi Hanoi]] | [[client-CapitaLand]] | [[mc-Newtecons]] | [[consultant-Studio Milou]], [[consultant-INNO]] | Hanoi |  |
| [[prj-NguyenVietHongApartment]] | [[client-ThienQuan]] |  |  | CanTho | 2026-2027 |
| [[prj-OneEra]] | [[client-KimOanhGroup]], [[client-SumitomoForestry]], [[client-KumagaiGumi]], [[client-NTTUrbanDevelopment]] | [[mc-CTD]] | [[consultant-Savills]] | BinhDuong |  |
| [[prj-TasecoLongBien]] | [[client-TasecoLand]] |  |  | Hanoi | 2027 |
| [[prj-TheGlobalCity]] | [[client-MasteriseHomes]] | [[mc-Newtecons]], [[mc-Central]] | [[consultant-FosterPartners]] | HCM | 2026 |

## Thong ke

```dataview
TABLE WITHOUT ID
  file.link AS "Du an",
  length(file.outlinks) AS "So lien ket"
FROM "_project"
WHERE contains(tags, "project")
SORT file.name ASC
```
