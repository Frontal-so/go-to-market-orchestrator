#!/usr/bin/env python3
"""gtm-guard: ask before Claude sends, spends credits, changes or deletes GTM data.

PreToolUse hook. Reads the hook JSON from stdin and, when the call is risky,
prints a PreToolUse decision:

    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                            "permissionDecision": "ask" | "deny",
                            "permissionDecisionReason": "..."}}

Two kinds of calls are checked:
  1. MCP tools of sales tools (tool names like mcp__apollo__people_enrichment,
     mcp__claude_ai_HubSpot__create_contact, mcp__plugin_x_lemlist__send_email).
  2. Bash and PowerShell commands that call a sales tool's REST API with a
     write method (curl -X POST https://api.instantly.ai/..., and similar).

Read-only calls (get, list, search, ...) and anything that is not a sales tool
get no decision, so Claude Code's normal permission rules apply to them.

Standard library only. Never crashes the session: on any internal error it
writes a one-line note to stderr, prints no decision and exits 0.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
import time
from typing import Optional

# Server-name tokens of CRMs, sequencers, enrichment and social posting tools.
# "lm" is the server name lemlist's developer docs use for its OAuth setup
# (https://developer.lemlist.com/mcp/setup); "lemlist" is covered too.
SEQUENCERS = {
    "instantly", "lemlist", "lm", "smartlead", "heyreach", "outreach", "salesloft",
    "amplemarket", "lagrowthmachine", "waalaxy", "expandi", "woodpecker",
}
GTM_SERVERS = SEQUENCERS | {
    "apollo", "attio", "hubspot", "salesforce", "pipedrive", "close", "folk", "zoho", "copper",
    "clay", "lusha", "zoominfo", "fullenrich", "dropcontact", "prospeo", "hunter",
    "typefully", "taplio",
}
# Social publishers: on these, scheduling or queueing a post is the go-live action.
PUBLISHERS = {"typefully", "taplio"}
# Words in an extra server's name that mark it as a sequencer.
_SEQUENCER_NAME_WORDS = {"sequencer", "sequence", "sequences", "campaign", "campaigns",
                         "cadence", "cadences", "outbound", "outreach"}

# Hosts of sales tools' REST APIs. Matched as a whole host name in a URL.
GTM_API_HOSTS = [
    "api.instantly.ai", "api.lemlist.com", "server.smartlead.ai", "api.smartlead.ai",
    "api.hubapi.com", "api.hubspot.com", "api.attio.com", "api.apollo.io", "api.clay.com",
    "api.pipedrive.com", "api.close.com", "api.heyreach.io", "api.typefully.com",
    "app.fullenrich.com", "api.fullenrich.com",
]
# API hosts of sequencers: a POST that adds leads into a campaign there is a send.
SEQUENCER_API_HOSTS = {"api.instantly.ai", "api.lemlist.com", "server.smartlead.ai", "api.smartlead.ai",
                       "api.heyreach.io"}
_SALESFORCE_HOST_RE = re.compile(r"https?://[a-z0-9.\-]+\.(?:my\.)?salesforce\.com(?=[/:'\"\s]|$)", re.IGNORECASE)

SEND = "send"
DELETE = "delete"
SPEND = "spend"
WRITE = "write"

WHAT = {
    SEND: "sends email or messages, or starts, resumes or feeds a sequence",
    DELETE: "deletes, removes or archives data",
    SPEND: "spends enrichment or verification credits",
    WRITE: "creates or changes records in a CRM or sales tool",
}

_DELETE_WORDS = {"delete", "remove", "archive", "purge", "destroy", "trash", "wipe", "erase"}
# Verbs that send or go live wherever they appear in a tool name.
_STRONG_SEND_WORDS = {"send", "forward", "launch", "activate", "publish", "enroll", "enrol",
                      "dispatch", "deliver"}
# "reply" sends unless a read verb leads the name (get_reply_status, list_reply_metrics).
_REPLY_WORDS = {"reply"}
# Verbs that send only in a verb position, first or after and/or/then (post_tweet,
# queue_post), so the nouns in get_post or add_to_queue_settings do not count.
_VERB_POSITION_SEND_WORDS = {"post", "queue", "reply"}
# Verbs that only send when the tool is about a campaign, sequence or message.
_SOFT_SEND_WORDS = {"start", "resume", "unpause", "schedule", "push", "enable", "turn_on"}
_CAMPAIGN_WORDS = {"campaign", "campaigns", "sequence", "sequences", "cadence", "cadences",
                   "email", "emails", "message", "messages", "outreach"}
_SEQUENCE_WORDS = {"campaign", "campaigns", "sequence", "sequences", "cadence", "cadences"}
_PUBLISH_WORDS = {"schedule", "queue", "post", "publish"}
_LEAD_WORDS = {"lead", "leads", "prospect", "prospects", "contact", "contacts", "recipient", "recipients"}
_ADD_WORDS = {"add", "import", "upload", "move", "push"}
# Verbs that put something into a sequence when followed by "to <sequence>".
_ATTACH_WORDS = _ADD_WORDS | {"assign", "attach", "subscribe", "insert", "put", "enroll", "enrol"}
_SPEND_WORDS = {"enrich", "enrichment", "reveal", "unlock", "waterfall"}
# Lookup verbs that spend credits when they look up a person's email or phone.
_LOOKUP_WORDS = {"finder", "lookup", "locate"}
_PERSON_DATA_WORDS = {"email", "emails", "phone", "phones", "mobile", "person", "people"}
_VERIFY_WORDS = {"verify", "verification", "validate", "validation"}
_CONTACT_DATA_WORDS = {"email", "emails", "phone", "phones", "mobile", "contact", "contacts", "person", "people"}
_NOT_CONTACT_DATA = {"template", "templates", "campaign", "campaigns", "thread", "threads", "inbox",
                     "domain", "domains", "folder", "folders"}
_WRITE_WORDS = {"create", "add", "update", "upsert", "edit", "set", "assign", "move", "merge",
                "import", "upload", "patch", "put", "tag", "append", "insert", "bulk", "batch",
                "write", "save", "modify", "change", "convert", "associate", "link", "attach",
                "mark", "pause", "stop", "duplicate", "clone", "schedule", "push", "unsubscribe",
                "enable", "disable", "turn_on", "queue"}
_STRONG_WRITE_WORDS = {"create", "update", "upsert", "merge", "import", "upload", "modify", "patch", "write"}
_READ_VERBS = {"get", "list", "search", "find", "read", "fetch", "query", "count", "describe",
               "retrieve", "view", "show", "check", "lookup", "preview", "export", "analyze"}
# A name that starts with a read verb and ends in one of these nouns reports on
# something (get_send_status, get_enrichment_status, list_archive_records).
_READ_NOUNS = {"status", "statuses", "stats", "statistics", "count", "counts", "history", "log",
               "logs", "report", "reports", "details", "detail", "info", "records", "metrics",
               "activity", "analytics", "summary"}
_CONJUNCTIONS = {"and", "or", "then"}


def tokens(name: str) -> list:
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return [t for t in re.split(r"[^a-zA-Z0-9]+", name.lower()) if t]


def _verb_positions(ordered: list) -> set:
    """Tokens in a verb position: the first one, and any right after and/or/then."""
    found = set(ordered[:1])
    for i in range(1, len(ordered)):
        if ordered[i - 1] in ("and", "or", "then"):
            found.add(ordered[i])
    return found


def classify_tool(tool: str, sequencer: bool = False, publisher: bool = False) -> Optional[str]:
    """Category of an MCP tool name, or None for reads and anything unknown.

    Dangerous verbs anywhere in the name win over a leading read verb, so
    get_or_create_contact and search_and_enrich_people are still caught. The one
    exception is a plain report name: a read verb first, a read noun last and no
    and/or/then (get_send_status, list_archive_records). Paid lookups of an email
    or phone still spend. It errs toward asking: a wrong "ask" costs a click, a
    missed send costs a campaign.
    """
    ordered = tokens(tool)
    words = set(ordered)
    if any(a == "turn" and b == "on" for a, b in zip(ordered, ordered[1:])):
        words.add("turn_on")
    read_leads = bool(ordered) and ordered[0] in _READ_VERBS
    verbs = _verb_positions(ordered)
    after_to = set(ordered[len(ordered) - ordered[::-1].index("to"):]) if "to" in ordered else set()
    contact_data = bool(words & _CONTACT_DATA_WORDS) and not words & _NOT_CONTACT_DATA
    finds_contact_data = "find" in words and contact_data and bool(words & {"email", "emails", "phone", "phones", "mobile"})
    looks_up_person = bool(words & _LOOKUP_WORDS) and bool(words & _PERSON_DATA_WORDS) and not words & _NOT_CONTACT_DATA
    verifies_contact_data = bool(words & _VERIFY_WORDS) and contact_data

    if (read_leads and ordered[-1] in _READ_NOUNS and not words & _CONJUNCTIONS
            and not (finds_contact_data or looks_up_person or verifies_contact_data)):
        return None  # get_send_status, get_enrichment_status, list_archive_records
    if words & _DELETE_WORDS:
        return DELETE
    if words & _STRONG_SEND_WORDS:
        return SEND
    if verbs & _VERB_POSITION_SEND_WORDS or (words & _REPLY_WORDS and not read_leads):
        return SEND  # post_tweet, queue_post, reply_to_thread; get_reply_status is a read
    if publisher and words & _PUBLISH_WORDS and not read_leads:
        return SEND  # on a social publisher, scheduling or queueing a post makes it go live
    if words & _ADD_WORDS and words & _LEAD_WORDS and (sequencer or words & _CAMPAIGN_WORDS):
        return SEND  # adding leads to a sequencer or campaign can start emails to them
    if words & _ATTACH_WORDS and after_to & _SEQUENCE_WORDS:
        return SEND  # add_to_sequence, assign_to_cadence: enrolment can start emails
    if words & _SPEND_WORDS or finds_contact_data or looks_up_person or verifies_contact_data:
        return SPEND
    if words & _STRONG_WRITE_WORDS:
        return WRITE
    if read_leads:
        return None  # get_campaign_schedule, list_tags, search_people
    if words & _SOFT_SEND_WORDS and words & _CAMPAIGN_WORDS:
        return SEND
    if words & _WRITE_WORDS:
        return WRITE
    return None


def split_mcp_name(tool_name: str):
    """mcp__<server>__<tool> -> (server, tool). Plugin servers keep their prefix."""
    parts = tool_name.split("__")
    if len(parts) < 3 or parts[0] != "mcp":
        return None, None
    return parts[1], "__".join(parts[2:])


def server_tokens(server: str) -> set:
    # No camelCase split here: "claude_ai_HubSpot" must give "hubspot", not "hub" + "spot".
    return {t for t in re.split(r"[^a-z0-9]+", server.lower()) if t}


def _normal(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def matches_extra(server: str, extra: set) -> bool:
    """True when an extra name is the server name or a whole part of it.

    plugin_x_acme-crm and claude_ai_Acme_CRM both match "acme-crm";
    notacme-crm does not.
    """
    normal = _normal(server)
    for name in extra:
        part = _normal(name)
        if part and re.search(r"(?:^|_)" + re.escape(part) + r"(?:_|$)", normal):
            return True
    return False


def server_is_gtm(server: str, extra: set) -> bool:
    return bool(server_tokens(server) & GTM_SERVERS) or matches_extra(server, extra)


def server_is_sequencer(server: str, extra: Optional[set] = None) -> bool:
    words = server_tokens(server)
    if words & SEQUENCERS:
        return True
    # an extra server named like a sequencer (acme-sequencer, outbound-prod) counts as one
    return bool(extra) and matches_extra(server, extra) and bool(words & _SEQUENCER_NAME_WORDS)


def server_is_publisher(server: str) -> bool:
    return bool(server_tokens(server) & PUBLISHERS)


_METHOD_RES = [
    re.compile(r"(?:^|\s)(?:-[A-Za-z]*X\s*|--request[=\s]+)['\"]?(POST|PUT|PATCH|DELETE)\b", re.IGNORECASE),  # curl, also -sXPOST
    re.compile(r"\b(?:requests|httpx|session|client|axios|got|ky|superagent|\$http)\.(post|put|patch|delete)\s*\(", re.IGNORECASE),
    re.compile(r"method['\"]?\s*[:=]\s*['\"](POST|PUT|PATCH|DELETE)['\"]", re.IGNORECASE),  # fetch, axios({...})
    re.compile(r"\bMethod\s*=\s*(POST|PUT|PATCH|DELETE)\b", re.IGNORECASE),  # PowerShell @{Method=Post}
    re.compile(r"-Method\s+['\"]?(POST|PUT|PATCH|DELETE)\b", re.IGNORECASE),  # PowerShell
    re.compile(r"(?:^|\s)(?:https?|xh)\s+(?:-\S+\s+)*(POST|PUT|PATCH|DELETE)\s", re.IGNORECASE),  # HTTPie, flags first allowed
    re.compile(r"--method[=\s]+['\"]?(POST|PUT|PATCH|DELETE)\b", re.IGNORECASE),  # wget
    re.compile(r"\bNet::HTTP\.(post_form|post|put|patch|delete)\b"),  # Ruby
    re.compile(r"\bNet::HTTP::(Post|Put|Patch|Delete)\.new\b"),  # Ruby
    # requests.request("POST", url), httpx.request(method="PUT", ...)
    re.compile(r"\.request\s*\(\s*(?:method\s*=\s*)?['\"](POST|PUT|PATCH|DELETE)['\"]", re.IGNORECASE),
]
# A method filled in at run time (-X "$METHOD", --method=$M, method: process.env.M,
# requests.request(m, url)) or options read from a curl config file (-K file)
# cannot be read here, so they count as a write.
_HIDDEN_METHOD_RES = [
    re.compile(r"(?:^|\s)(?:-[A-Za-z]*X\s*|--request[=\s]+)['\"]?\$"),  # curl
    re.compile(r"\bcurl\b.*(?:^|\s)(?:-K|--config)(?=[\s=])", re.DOTALL),
    re.compile(r"--method[=\s]+['\"]?\$"),  # wget
    re.compile(r"-Method\s+['\"]?\$", re.IGNORECASE),  # PowerShell
    re.compile(r"\bmethod['\"]?\s*:\s*(?!['\"`]|(?:GET|HEAD|OPTIONS)\b)[A-Za-z_$]"),  # fetch, axios
    re.compile(r"[{,]\s*method\s*[,}]"),  # fetch(url, {method}) shorthand
    re.compile(r"\bMethod\s*=\s*\$", re.IGNORECASE),  # PowerShell @{Method=$env:M} splatting
    re.compile(r"\.request\s*\(\s*(?!(?:method\s*=\s*)?['\"]|\))"),  # requests, httpx
]
# -d and -F count with or without a space (-dname=Maya, -Ffile=@leads.csv), and so does
# every --data* and --form* option.
_BODY_RE = re.compile(r"(?:^|\s)(?:-d|-F|--data[\w-]*|--form[\w-]*|--json|--post-data|--post-file)")
# curl short flags run together (-sd 'x', -sSF file=@x): a cluster of letters with d or F in it.
_CURL_CLUSTER_RE = re.compile(r"\bcurl\b[^|;&\n]*?\s-[A-Za-z]*[dF]")
# HTTPie sends a body, so POST by default, with --raw or with data piped into it.
_HTTPIE_RAW_RE = re.compile(r"(?:^|\s)(?:https?|xh)\s[^|;&\n]*--raw\b|\|\s*(?:https?|xh)\s+(?:-\S+\s+)*(?!(?:GET|HEAD|OPTIONS)\b)\S", re.IGNORECASE)
_UPLOAD_RE = re.compile(r"(?:^|\s)(?:-T|--upload-file)(?=[\s=])")
_SEND_PATH_RE = re.compile(r"/(send|launch|activate|start|resume|reply|enroll)\b", re.IGNORECASE)


def find_gtm_host(command: str) -> Optional[str]:
    for host in GTM_API_HOSTS:
        # whole host only: api.hubapi.com.evil.example does not count
        if re.search(r"(?:^|[/@'\"\s=(])" + re.escape(host) + r"(?=[/:'\"\s)?]|$)", command, re.IGNORECASE):
            return host
    m = _SALESFORCE_HOST_RE.search(command)
    return "salesforce.com" if m else None


_PRINT_ONLY_RE = re.compile(r"^\s*(?:echo|printf|Write-Output|Write-Host)\b", re.IGNORECASE)
# python -c 'print("...")': the code is one print() of one plain string literal, nothing else.
_PYTHON_PRINT_RE = re.compile(
    r"""^\s*python(?:3(?:\.\d+)?)?\s+-c\s+(?:'\s*print\(\s*"[^"'\\]*"\s*\)\s*'|"\s*print\(\s*'[^"'\\]*'\s*\)\s*")\s*$""")
_CHAINING_RE = re.compile(r"[;&|`\n]|\$\(")


def is_print_only(command: str) -> bool:
    """True when the whole command only prints text (echo 'curl -X POST ...').

    Anything chained, piped or substituted (&&, ;, |, $(...), backticks) is not print-only.
    """
    if _CHAINING_RE.search(command):
        return False
    return bool(_PRINT_ONLY_RE.match(command) or _PYTHON_PRINT_RE.match(command))


_HTTPIE_RE = re.compile(r"(?:^|[;&|(]|\s)(?:http|https|xh|xhs)\s+([^;&|\n]*)")
_HTTPIE_DATA_ITEM_RE = re.compile(r"^[^=:@\s]+(?::=@|:=|=@|@|=(?!=))")
_HTTPIE_METHOD_RE = re.compile(r"^[A-Z]+$")


def httpie_implicit_post(command: str) -> bool:
    """HTTPie (http, https, xh) sends POST with no method word when a data item
    (key=value, key:=json, key@file) follows the URL. Header items (Name:value)
    and query items (key==value) keep it a GET."""
    for m in _HTTPIE_RE.finditer(command):
        try:
            tokens = shlex.split(m.group(1))
        except ValueError:
            tokens = m.group(1).split()
        i = 0
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 1  # options before the method or URL
        if i < len(tokens) and _HTTPIE_METHOD_RE.match(tokens[i]):
            continue  # an explicit method word: _METHOD_RES decides
        if i >= len(tokens):
            continue
        if any(_HTTPIE_DATA_ITEM_RE.match(tok) for tok in tokens[i + 1:] if not tok.startswith("-")):
            return True
    return False


def classify_bash(command: str) -> Optional[tuple]:
    """Return (host, category) when a shell command writes to a sales tool's API.

    The method is not tied to the URL it belongs to: a command that names a
    sales API anywhere and writes anywhere is asked about. That errs toward asking.
    A command that only prints text is not a call.
    """
    if is_print_only(command):
        return None
    host = find_gtm_host(command)
    if not host:
        return None
    method = None
    for pattern in _METHOD_RES:
        m = pattern.search(command)
        if m:
            method = m.group(1).upper().split("_")[0]  # Ruby post_form is a POST
            break
    if not method and any(p.search(command) for p in _HIDDEN_METHOD_RES):
        method = "UNKNOWN"  # cannot tell, so it counts as a write
    if not method and _UPLOAD_RE.search(command):
        method = "PUT"
    if not method and (_BODY_RE.search(command)
                       or (re.search(r"\bcurl\b", command) and _CURL_CLUSTER_RE.search(command))):
        method = "POST"  # curl and wget send POST when given a body
    if not method and (httpie_implicit_post(command) or _HTTPIE_RAW_RE.search(command)):
        method = "POST"
    if not method:
        return None
    if method == "DELETE":
        return host, DELETE
    if _SEND_PATH_RE.search(command):
        return host, SEND
    if method == "POST" and host in SEQUENCER_API_HOSTS:
        for m in re.finditer(r"https?://" + re.escape(host) + r"(/[^\s'\"]*)", command, re.IGNORECASE):
            if is_enrol_path(m.group(1)):
                return host, SEND  # adding leads to a sequencer campaign can start emails
    return host, WRITE


_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]{0,63}$")

# The only path parts the log keeps. Anything else (a name, a slug, an id, an
# email, a number) could identify a person or an account, so it is shown as '*'.
ROUTE_WORDS = {
    "api", "rest", "crm", "objects", "object", "records", "record", "data", "public", "graphql",
    "contacts", "contact", "companies", "company", "deals", "deal", "leads", "lead",
    "people", "persons", "person", "accounts", "account", "opportunities", "opportunity",
    "campaigns", "campaign", "sequences", "sequence", "prospects", "prospect", "recipients",
    "lists", "list", "notes", "note", "tasks", "task", "emails", "email", "messages", "message",
    "activities", "activity", "webhooks", "webhook", "users", "user", "teams", "team",
    "owners", "properties", "associations", "pipelines", "stages", "fields", "tags", "labels",
    "unsubscribes", "unsubscribe", "blocklist", "suppression", "batch", "bulk",
    "search", "query", "create", "update", "upsert", "delete", "archive", "import", "export",
    "send", "launch", "activate", "start", "resume", "reply", "enroll", "enrollments",
    "stop", "pause", "status", "stats", "analytics", "schedule", "schedules", "drafts", "posts",
    "sobjects", "services", "workspaces", "workspace", "entries", "attributes",
}
_VERSION_RE = re.compile(r"^v\d{1,2}(?:\.\d{1,2})?$", re.IGNORECASE)

# Generic tools that reach any endpoint of the tool's API. lemlist always exposes
# call_api: "anything outside your bucket stays reachable through call_api"
# (https://developer.lemlist.com/mcp/setup). Its parameter names are not
# documented, so the method is looked for under several common keys.
GENERIC_API_TOOLS = {"call_api", "api_call", "api_request", "http_request", "raw_request",
                     "make_request", "request"}
_METHOD_KEYS = {"method", "http_method", "httpmethod", "verb", "request_method", "requestmethod"}
_PATH_KEYS = {"path", "endpoint", "url", "uri", "route"}
_READ_METHODS = {"GET", "HEAD", "OPTIONS"}
_LOG_METHODS = {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"}
# Nouns that name a collection: the path part right after one is an id slot, so it
# is a value (an id, a name, an email, a slug) even when it looks like a route word.
COLLECTION_WORDS = {
    "campaigns", "campaign", "sequences", "sequence", "leads", "lead", "contacts", "contact",
    "companies", "company", "deals", "deal", "prospects", "prospect", "recipients", "lists", "list",
    "people", "persons", "person", "records", "record", "objects", "object", "users", "user",
    "accounts", "account", "opportunities", "opportunity", "tasks", "task", "notes", "note",
    "emails", "email", "messages", "message", "webhooks", "webhook", "enrollments", "activities",
    "activity", "teams", "team", "owners", "pipelines", "stages", "workspaces", "workspace",
    "entries", "attributes", "sobjects", "drafts", "posts", "schedules", "tags", "labels", "fields",
}
_CAMPAIGN_WORDS_PATH = {"campaigns", "campaign", "sequences", "sequence"}
_LEAD_WORDS_PATH = {"leads", "contacts", "prospects", "recipients"}
_ENROL_TAIL = {"add", "bulk", "batch", "import"}


def _segments(raw: Optional[str]) -> list:
    """[(lowercased part, is_id_slot)] of a URL path, without host and query string."""
    if not raw:
        return []
    path = re.sub(r"^[a-z][a-z0-9+.\-]*://[^/]*", "", str(raw).strip(), flags=re.IGNORECASE)
    path = re.split(r"[?#]", path, maxsplit=1)[0]
    out, after_collection = [], False
    for part in path.split("/"):
        if not part:
            continue
        word = part.lower()
        out.append((word, after_collection))
        # the part after a collection word is an id slot, even when that word itself
        # sat in an id slot (/objects/campaigns/launch: both parts after objects are masked)
        after_collection = word in COLLECTION_WORDS
    return out


def is_enrol_path(raw: Optional[str]) -> bool:
    """True for a path that puts people INTO a campaign or sequence:
    .../campaigns/<id>/leads, optionally followed by add, bulk, batch, import or
    one id (the lead's email). .../leads/search and the like are not."""
    segs = _segments(raw)
    seen_campaign = False
    for i, (word, id_slot) in enumerate(segs):
        if id_slot:
            continue
        if word in _CAMPAIGN_WORDS_PATH:
            seen_campaign = True
        elif seen_campaign and word in _LEAD_WORDS_PATH:
            rest = segs[i + 1:]
            if not rest:
                return True
            if len(rest) == 1:
                nxt = rest[0][0]
                return nxt in _ENROL_TAIL or (nxt not in ROUTE_WORDS and not _VERSION_RE.match(nxt))
            return False
    return False


def _find_key(tool_input: dict, keys: set):
    """A string value under one of `keys` (any case), at the top or one level down."""
    for level in (tool_input, *[v for v in tool_input.values() if isinstance(v, dict)]):
        for key, value in level.items():
            if str(key).lower() in keys and isinstance(value, str):
                return value
    return None


def safe_path(raw: Optional[str]) -> str:
    """The path of a URL with no host and no query string. A part is kept only when
    it is a route word (ROUTE_WORDS, or a version such as v3) and does not sit in an
    id slot (right after a collection noun such as campaigns or leads). Every
    other part becomes '*'."""
    segs = _segments(raw)
    if not segs:
        return ""
    parts = [word if not id_slot and (word in ROUTE_WORDS or _VERSION_RE.match(word)) else "*"
             for word, id_slot in segs]
    return ("/" + "/".join(parts))[:200]


def classify_generic_call(tool_input: dict, sequencer: bool = False) -> tuple:
    """(category or None, method, safe path) for a generic API tool.

    GET, HEAD and OPTIONS are reads. A missing or unknown method asks.
    """
    method = (_find_key(tool_input, _METHOD_KEYS) or "").strip().upper()
    if method not in _LOG_METHODS:
        method = "unknown"  # never log or show a value that is not a method name
    raw_path = _find_key(tool_input, _PATH_KEYS)
    path = safe_path(raw_path)
    if method in _READ_METHODS:
        return None, method, path
    if method == "DELETE":
        return DELETE, method, path
    if method in ("POST", "PUT", "PATCH"):
        if _SEND_PATH_RE.search(path) or (sequencer and method == "POST" and is_enrol_path(raw_path)):
            return SEND, method, path  # starting a campaign, or adding leads to one
        # updating a lead or searching leads is a write that asks, not a send
        return WRITE, method, path
    return WRITE, method, path


def input_shape(tool_input) -> dict:
    """Field names and list sizes only. Values never leave this function.

    Only identifier-like keys are kept (a key that is an email address or
    free text is counted, not logged), at most 50 of them. Lists one level
    down are reported too: {"request": {"leads": [...]}} gives "request.leads".
    """
    shape = {"fields": [], "lists": {}, "other_fields": 0}
    if isinstance(tool_input, dict):
        for key, value in tool_input.items():
            key = str(key)
            if not _FIELD_RE.match(key) or len(shape["fields"]) >= 50:
                shape["other_fields"] += 1
                continue
            shape["fields"].append(key)
            if isinstance(value, list):
                shape["lists"][key] = len(value)
            elif isinstance(value, dict):
                for sub, sub_value in value.items():
                    sub = str(sub)
                    if isinstance(sub_value, list) and _FIELD_RE.match(sub) and len(shape["lists"]) < 50:
                        shape["lists"][f"{key}.{sub}"] = len(sub_value)
    return shape


def preview(shape: dict) -> str:
    if shape["lists"]:
        sizes = ", ".join(f"{k}: {v:,} item{'s' if v != 1 else ''}" for k, v in shape["lists"].items())
        return f"Lists in this call: {sizes}."
    return ""


# ── settings, log, output ───────────────────────────────────────────────────

def option(key: str, fallback_env: str, default: str = "") -> str:
    value = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}") or os.environ.get(fallback_env) or ""
    return value.strip() or default


LOG_MAX_BYTES = 5 * 1024 * 1024  # then guard-log.jsonl becomes guard-log.1.jsonl (one old generation)
LOCK_WAIT_SECONDS = 0.5           # never hold up the session for the log
LOCK_NAME = "guard-log.lock"      # held while the size check, rotation and append run


def _lock(f) -> bool:
    """Try for a short while to lock the log; False means skip this line."""
    try:
        import fcntl  # POSIX only; on Windows the append is unlocked
    except ImportError:
        return True
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.02)
        except OSError:
            return True  # a file system without locks: append unlocked


def write_log(record: dict) -> None:
    if option("log_calls", "GTM_GUARD_LOG", "true").lower() not in ("1", "true", "yes", "on"):
        return
    directory = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.path.expanduser("~"), ".claude", "gtm-guard")
    path = os.path.join(directory, "guard-log.jsonl")
    try:
        os.makedirs(directory, exist_ok=True)
        # One lock over the size check, the rotation and the append, so two hooks
        # running at once cannot both rotate and lose the old generation.
        with open(os.path.join(directory, LOCK_NAME), "a", encoding="utf-8") as lock:
            if not _lock(lock):
                return  # busy for too long: skip this line rather than slow the session
            try:
                if os.path.getsize(path) >= LOG_MAX_BYTES:
                    os.replace(path, os.path.join(directory, "guard-log.1.jsonl"))
            except FileNotFoundError:
                pass
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def decide(payload: dict) -> Optional[dict]:
    tool_name = payload.get("tool_name") or ""
    if not isinstance(tool_name, str):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}  # a list or string input is still classified by the tool name
    extra = {s.strip().lower() for s in option("extra_servers", "GTM_GUARD_EXTRA_SERVERS").split(",") if s.strip()}
    mode = option("mode", "GTM_GUARD_MODE", "ask").lower()

    request = None
    if tool_name in ("Bash", "PowerShell"):
        found = classify_bash(str(tool_input.get("command", "")))
        if not found:
            return None
        target, category = found
        label = f"this API call to {target}"
    else:
        server, tool = split_mcp_name(tool_name)
        if not server or not server_is_gtm(server, extra):
            return None
        sequencer = server_is_sequencer(server, extra)
        if tool.lower() in GENERIC_API_TOOLS:
            category, method, path = classify_generic_call(tool_input, sequencer=sequencer)
            if not category:
                return None
            request = {"method": method, "path": path}
            label = f"`{tool}` ({method} {path or 'no path given'}) on {server}"
        else:
            category = classify_tool(tool, sequencer=sequencer, publisher=server_is_publisher(server))
            if not category:
                return None
            label = f"`{tool}` on {server}"
        target = server

    shape = input_shape(tool_input)
    block = mode == "block-sends" and category in (SEND, DELETE)
    decision = "deny" if block else "ask"

    if block:
        reason = (f"gtm-guard blocked {label}: it {WHAT[category]}. Sends, launches and deletes "
                  f"are blocked here (gtm-guard mode block-sends). Show the user exactly what you "
                  f"were about to do and let them run it themselves.")
    else:
        reason = (f"gtm-guard: {label} {WHAT[category]}. {preview(shape)} "
                  f"Check the details before you approve.").replace("  ", " ")

    record = {
        "ts": _dt.datetime.now().isoformat(timespec="seconds"),
        "session_id": payload.get("session_id"),
        "project": os.path.basename(os.path.normpath(payload.get("cwd") or os.getcwd())),
        "tool": tool_name,
        "target": target,
        "category": category,
        "decision": decision,
        "fields": shape["fields"],
        "list_sizes": shape["lists"],
        "other_fields": shape["other_fields"],
    }
    if request:
        record["request"] = request  # method name and route words only, never the body
    write_log(record)

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    result = decide(payload)
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # a guard bug must never block the user's session
        print(f"gtm-guard: internal error {e!r}", file=sys.stderr)
        sys.exit(0)
