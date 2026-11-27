---
layout: default
title: "Horizon Summary: 2026-11-27 (EN)"
date: 2026-11-27
lang: en
---

> From 95 items, 2 important content pieces were selected

---

**Technology News**
1. [Report: Google Workspace MCP Servers for AI Agents Omit Gmail Sending](#item-tech-news-1) ⭐️ 7.0/10
2. [First at-home user tests bionic hand that restores pressure sensation](#item-tech-news-2) ⭐️ 7.0/10

---

## Technology News

<a id="item-tech-news-1"></a>
### [Report: Google Workspace MCP Servers for AI Agents Omit Gmail Sending](https://techstackups.com/articles/google-workspace-ai-agents-mcp/) ⭐️ 7.0/10

According to a techstackups.com report, Google is preparing MCP servers that let AI agents operate Google Workspace services, with the Gmail server reportedly unable to send email. The supplied item gives no version numbers, release dates, or Google confirmation, so it is unclear whether these servers are shipped, in preview, or merely planned. The reported Gmail limitation is the concrete condition for developers: an agent can apparently work with Gmail through MCP, but the server&\#x27;s toolset excludes dispatching messages.

hackernews · ritzaco · Nov 26, 09:44 · [Discussion](https://news.ycombinator.com/item?id=50653477)

**「Background」** Google&\#x27;s Workspace MCP servers are documented as a standardized way for AI agents to read Workspace data, take actions such as creating draft emails and scheduling meetings, and inherit the user&\#x27;s permissions and data-governance controls. Google&\#x27;s Gmail MCP guidance says sensitive actions are protected by server-driven human-in-the-loop approvals delivered through MCP form elicitation. The Next Web reports that, from February 2027, agents will have to reach Workspace through these MCP servers or the CLI, with human sign-off for key actions and no training on user data.

**「Impact」** Developers building agents that need to send mail through Google Workspace&\#x27;s MCP servers will have to route around the Gmail server — pairing it with the Gmail API directly or obtaining partner access — since the server reportedly exposes no send-email tool. MCP already defines elicitation, a synchronous mechanism that pauses an active tool call to request human input and then lets the harness continue, revise, cancel, or fail per policy, which is the existing primitive commenters cite as a way to gate a send action rather than omit it.

**「Community Discussion」** Commenters focused on the send-email gap: Schnitz argued that developers will simply have agents drive a browser instead, calling that approach &quot;unnecessarily messy and wasteful,&quot; while perdy said MCP&\#x27;s elicitation primitive already lets a server pause a tool call and ask the user to confirm, so a partner-only send tool looks more like a business decision than a safety measure. physicsguy described a broader shift toward usage-based API pricing and terms-of-service enforcement, warning that extracting data through a client can get accounts suspended.

<details><summary>References</summary>
<ul>
<li><a href="https://developers.google.com/workspace/gmail/api/guides/configure-mcp-server">Configure the Gmail MCP server | Google for Developers</a></li>
<li><a href="https://developers.google.com/workspace/guides/configure-mcp-servers">Configure the Google Workspace MCP servers</a></li>
<li><a href="https://thenextweb.com/news/google-workspace-ai-agents-mcp-servers-rules">Google will make AI agents use new gateways to reach Gmail ...</a></li>
<li><a href="https://dev.to/kachurun/mcp-elicitation-human-in-the-loop-for-mcp-servers-m6a">MCP Elicitation : Human -in-the-Loop for MCP ... - DEV Community</a></li>
<li><a href="https://www.rifty.ai/glossary/mcp-elicitation">MCP elicitation</a></li>

</ul>
</details>

**Tags**: `#MCP`, `#Google Workspace`, `#AI agents`, `#Gmail`, `#API policy`

---

<a id="item-tech-news-2"></a>
### [First at-home user tests bionic hand that restores pressure sensation](https://www.technologyreview.com/2026/11/26/1149923/the-next-generation-of-bionic-hands-is-here-and-they-can-feel/) ⭐️ 7.0/10

A 33-year-old trauma therapist named Avi Davidson has become the first person to use an experimental sensory-enabled bionic hand at home as part of a University of Utah clinical trial. Davidson, the ninth participant to receive the implant, had electrode arrays containing 100 needles apiece implanted into three forearm nerves and 24 electrodes inserted into surrounding muscles, allowing him to control the LUKE arm and feel pressure. He has used the hand since July 10, and researchers say the trial is meant to determine how useful the device is in daily life, where it fails, and how it affects his nervous system and well-being. The device remains experimental: participants do not keep it and must undergo surgery both to implant and remove the hardware.

rss · MIT Technology Review · Nov 26, 09:59

**「Background」** The LUKE arm itself dates to the 2000s: it was first trialed and cleared by the FDA in 2014 as a prosthetic arm. The University of Utah trial Davidson joined, running since 2013, instead tests a nerve-interface system that connects the existing arm to the residual limb’s nerves for movement control and pressure feedback.

**「Impact」** For Davidson, the practical benefit is being able to handle delicate objects such as eggs and grapes and to cook at home, but the hand weighs about five pounds and requires battery changes once or twice a day. Because the trial requires two surgeries and participants do not keep the device, at-home sensory feedback remains a research capability rather than an available treatment.

**Tags**: `#neuroprosthetics`, `#bionic limbs`, `#assistive technology`, `#clinical trials`, `#hardware`

---