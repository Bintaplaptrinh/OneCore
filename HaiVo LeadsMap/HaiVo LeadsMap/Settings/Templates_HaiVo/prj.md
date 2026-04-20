<%*
const prj = await tp.system.prompt("Project name");
if (!prj) {
  new Notice("Cancelled");
  return;
}

await tp.file.rename(prj);

const created = tp.date.now("YYYY-MM-DD HH:mm");
const folderTitle = tp.file.folder().split("/").pop();

tR += `---
title: "${folderTitle}"
created: "${created}"
tags: []
prj_name: "${prj}"
prj_client: 
---
> [!project] Prj Name: ${prj} 

🛜 Link:
 - contact:
 - client: 


***
ℹ️ Prj Notes:

***
`;
%>
