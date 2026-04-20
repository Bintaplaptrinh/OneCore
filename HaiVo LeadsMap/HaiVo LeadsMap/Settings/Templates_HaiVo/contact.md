<%*
const name = await tp.system.prompt("Contact name");
if (!name) { 
  new Notice("Cancelled"); 
  return; 
}

await tp.file.rename(name);

const created = tp.date.now("YYYY-MM-DD HH:mm");
const folderTitle = tp.file.folder().split("/").pop();

tR += `---
title: "${folderTitle}"
created: "${created}"
tags: []
contact_name: "${name}"
company_name: 
roles: 
---
> [!contact] Contact Name: ${name}

🛜 Link:
 - project: 
 - client: 

***
ℹ️ Thông tin chi tiết
🏢 Công ty: 
[Tên công ty/Tổ chức]
💼 Vai trò & Chức danh: 
[Vị trí công việc]
[Phòng ban]
📞 Thông tin liên hệ: 
- Số điện thoại: [Nhập SĐT]
- Email: [Nhập Email]
- Địa chỉ: [Văn phòng/Nhà riêng]
- Website/Social: [Link liên kết]
***
ℹ️ Contact Notes:

***

`;
%>
