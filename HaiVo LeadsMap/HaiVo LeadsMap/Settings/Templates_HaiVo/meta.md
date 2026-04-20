<%*
const name = await tp.system.prompt("Nhập tên file");
if (!name) {
  new Notice("Cancelled");
  return;
}

// đổi tên file
await tp.file.rename(name);

// thời gian tạo
const created = tp.date.now("YYYY-MM-DD HH:mm");

// render toàn bộ frontmatter
tR += `---
title: "${name}"
created: "${created}"
tags: []
---`;
%>
