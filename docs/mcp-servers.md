# Connecting your GTM tools (official MCP servers)

The gtm-outbound and gtm-content skills work from CSV files on their own. Connect a tool's MCP server when you want Claude to read from it (search Apollo, pull a HubSpot pipeline) or, after you approve, write to it.

Checked against each vendor's own page on 2026-11-25. Vendors change these often: if a command fails, the linked page wins.

## Before you connect anything

1. **Install gtm-guard first.** It makes Claude ask before any call that sends, launches, spends credits, changes records or deletes, even for tools you allowed earlier. [gtm-guard README](../plugins/gtm-guard/README.md).
2. **Prefer OAuth.** Where a vendor offers it, you sign in through the browser and no key is stored in your project.
3. **Never put keys in `CLAUDE.md`, skill files or a committed `.mcp.json`.** A server added with `--scope project` is written to `.mcp.json` in your project, which you usually commit. Keep keyed servers at the default local scope, or `--scope user` for all your projects.
4. **Use the vendor's own limits too.** Several vendors let you set tools to "approval required", narrow the key's scopes, or cap credits per user. Use them.

After adding a server, run `/mcp` inside Claude Code to sign in (OAuth) and to see its tools.

## The tools

### Apollo
- `claude mcp add --transport http apollo https://mcp.apollo.io/mcp`, then `/mcp` to sign in (OAuth).
- Apollo prohibits AI model training with its MCP integration. If your AI client uses your conversations for model training, turn that off before you use Apollo MCP.
- People search is free; company search and enrichment spend credits. With an API key instead of OAuth (`X-Api-Key` header, master keys only), every call spends workspace credits. Apollo advises setting credit-using actions to "Approval required". Free accounts on a personal email cannot use search or enrichment.
- Source: https://docs.apollo.io/docs/apollo-mcp

### HubSpot
- Remote server `https://mcp.hubspot.com`, generally available since 2026-04-13. OAuth 2.1 with PKCE through an app you create in HubSpot under Development, MCP Auth Apps, which gives a client ID and secret.
- Simplest route: connect HubSpot from Claude's connector directory on claude.ai. When Claude Code is signed in with the same Claude account, the connector's tools show up in Claude Code too (named `mcp__claude_ai_HubSpot__...`; gtm-guard recognises them).
- Claude Code with your own auth app (not tested by us): register `http://localhost:PORT/callback` in the app, then `claude mcp add --transport http --client-id YOUR_CLIENT_ID --client-secret --callback-port PORT hubspot https://mcp.hubspot.com`.
- There is no global read-only mode; scopes are set on the auth app.
- Sources: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/integrate-with-the-remote-hubspot-mcp-server, https://developers.hubspot.com/changelog/remote-hubspot-mcp-server-is-now-generally-available

### Attio
- `https://mcp.attio.com/mcp`, OAuth only (no API keys). Reads are auto-approved, writes ask first. The page gives no Claude Code command; the general form is `claude mcp add --transport http attio https://mcp.attio.com/mcp`, then `/mcp`.
- Source: https://docs.attio.com/mcp/overview

### Salesforce
- Hosted MCP servers at `https://api.salesforce.com/platform/mcp/v1/{servername}` (Salesforce recommends the My Domain form `/d/{mydomain}/{servername}`). Auth through an External Client App with the `mcp_api` and `refresh_token` scopes and PKCE. Salesforce's Claude guide sets it up as a custom connector in Claude.ai or Claude Desktop (Customize, Connectors, Add custom connector, then the server URL) and says Claude Code inherits that connection. Set up the External Client App with your Salesforce admin first.
- Sources: https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/claude.html and https://github.com/forcedotcom/mcp-hosted/wiki/Connecting-Your-MCP-Client (both read 2026-11-25)

### lemlist
- OAuth: `claude mcp add --transport http lm https://app.lemlist.com/mcp`. The developer page explains the name: many clients build their app name from the server name, and lemlist refuses an app name that contains "lemlist" (`client_name must not contain the reserved name "lemlist"`), so it suggests `lm`. API key setups are not affected.
- The two lemlist pages disagree: the help center article uses `claude mcp add --transport http lemlist https://app.lemlist.com/mcp` for OAuth. If that name fails with the error above, use `lm`. gtm-guard catches both names.
- API key: `claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key: YOUR_KEY"`.
- Email finding, verification and phone enrichment spend credits. The `?bucket=` option narrows the tools listed but does not restrict access: scope the key itself.
- lemlist always exposes a generic `call_api` tool, and anything outside your bucket stays reachable through it. gtm-guard judges `call_api` by the HTTP method in the call: GET passes, a write, send or delete asks, and a call with no method it can read asks.
- Sources: https://developer.lemlist.com/mcp/setup and https://help.lemlist.com/en/articles/13728466 (both read 2026-11-25)

### Instantly
- `https://mcp.instantly.ai/mcp` with your API v2 key in the header `Authorization: YOUR_API_KEY` (the page shows no "Bearer"). The page gives no Claude Code command; the general form is `claude mcp add --transport http instantly https://mcp.instantly.ai/mcp --header "Authorization: YOUR_API_KEY"`.
- The page also allows the key in the URL path. Avoid that: URLs end up in logs.
- Access control is the scopes you pick when you create the key.
- Source: https://developer.instantly.ai/mcp/quickstart

### Smartlead
- SSE only, with the key in the URL: `https://mcp.smartlead.ai/sse?user_api_key=YOUR_KEY`. Smartlead documents Claude Desktop only (through `npx -y mcp-remote`). Claude Code supports SSE servers (`claude mcp add --transport sse smartlead "https://mcp.smartlead.ai/sse?user_api_key=YOUR_KEY"`) but we have not tested it with Smartlead, and the key sits in your local config in plain text.
- Source: https://helpcenter.smartlead.ai/en/articles/300-smartlead-mcp-server

### Clay
- Hosted server `https://api.clay.com/v3/mcp`, OAuth 2.0 with PKCE. Workspace admins choose which MCP clients may connect and can cap credits per user. Tools spend credits at the normal rate. The page gives no Claude Code command; the general form is `claude mcp add --transport http clay https://api.clay.com/v3/mcp`, then `/mcp`.
- Source: https://university.clay.com/docs/connect-to-clay-mcp

### Slack
- Official server `https://mcp.slack.com/mcp`. Slack's own route for Claude Code is its plugin: `/plugin marketplace add slackapi/slack-skills-plugin`, then `/plugin install slack@slack`. A workspace admin must approve the app.
- For simple "Claude is done" pings to a channel you do not need this: use the gtm-notify plugin with an incoming webhook.
- Sources: https://docs.slack.dev/ai/slack-mcp-server/, https://docs.slack.dev/ai/slack-mcp-server/connect-to-harnesses/

### Notion
- `claude mcp add --transport http notion https://mcp.notion.com/mcp`, then `/mcp`. The old `/sse` endpoint retires on 2027-02-23.
- Source: https://developers.notion.com/guides/mcp/common-mcp-clients

### Linear
- `claude mcp add --transport http linear-server https://mcp.linear.app/mcp`. A read-only endpoint exists: `https://mcp.linear.app/mcp/readonly`.
- Source: https://linear.app/docs/mcp

### Typefully
- `claude mcp add --transport http typefully https://mcp.typefully.com/mcp` (OAuth recommended; an `Authorization: Bearer YOUR_KEY` header also works). Typefully can publish posts; the gtm-content skill only drafts, so keep publishing in your own hands.
- Source: https://support.typefully.com/en/articles/13128440-typefully-mcp-server

## Claude Code basics

- Add a remote server: `claude mcp add --transport http <name> <url>`, with `--header "Name: value"` for a key.
- Scopes: local (default, only you, this project), `--scope user` (you, all projects), `--scope project` (written to `.mcp.json`, shared with everyone who clones the project; each person approves it the first time).
- SSE is deprecated in Claude Code; use `--transport http` wherever the vendor supports it.
- Source: https://code.claude.com/docs/en/mcp
