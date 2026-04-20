---
aliases:
date_created: <% tp.file.creation_date() %>
start_date: <% tp.date.now("YYYY-MM-DD HH:mm") %>
end_date:
tags:
  - meeting
title: Meeting Note
---
<%*
const meetingTitle = await tp.system.prompt("Meeting Title");
const title = meetingTitle || tp.file.title;
const sanitizedTitle = title.replace(/[\/\\:|\&]/g, "-");
const newFileName = tp.date.now("YYYY-MM-DD") + "-" + sanitizedTitle;
await tp.file.rename(newFileName);
-%>

# <% meetingTitle || tp.file.title %>

Account:: <% tp.file.cursor(1) %>
Opportunity::
Attendees::
- name

```crm
```

## Agenda
1.

## Discussion Notes
*

## Action Items
- [ ]

## Follow-up
*

<% await tp.file.move("/CRM/Interactions/" + tp.file.title) %>
