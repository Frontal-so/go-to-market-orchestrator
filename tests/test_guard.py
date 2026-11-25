import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from helpers import GUARD, clean_env, load, run_script

guard = load(GUARD, "guard")


def payload(tool_name, tool_input=None):
    return {"session_id": "s1", "cwd": "/tmp/acme", "hook_event_name": "PreToolUse",
            "tool_name": tool_name, "tool_input": tool_input or {}}


class ClassifyMcpTools(unittest.TestCase):
    def decision(self, tool_name, tool_input=None, **env):
        with tempfile.TemporaryDirectory() as data, \
                mock.patch.dict(os.environ, clean_env(CLAUDE_PLUGIN_DATA=data, **env), clear=True):
            result = guard.decide(payload(tool_name, tool_input))
        return result and result["hookSpecificOutput"]["permissionDecision"]

    def test_enrichment_spends_credits(self):
        self.assertEqual(guard.classify_tool("people_enrichment"), guard.SPEND)
        self.assertEqual(self.decision("mcp__apollo__people_enrichment"), "ask")

    def test_finding_emails_spends_credits_even_with_a_read_verb(self):
        self.assertEqual(guard.classify_tool("find_email"), guard.SPEND)

    def test_reads_pass_through(self):
        for tool in ("mcp__instantly__list_campaigns", "mcp__smartlead__get_campaign_schedule",
                     "mcp__claude_ai_HubSpot__search_crm_objects", "mcp__apollo__search_people"):
            self.assertIsNone(self.decision(tool), tool)

    def test_camel_case_connector_name_is_recognised(self):
        self.assertTrue(guard.server_is_gtm("claude_ai_HubSpot", set()))
        self.assertEqual(self.decision("mcp__claude_ai_HubSpot__create_contact"), "ask")

    def test_camel_case_tool_names_are_split(self):
        self.assertEqual(guard.classify_tool("sendEmail"), guard.SEND)

    def test_send_and_delete(self):
        self.assertEqual(guard.classify_tool("send_email"), guard.SEND)
        self.assertEqual(guard.classify_tool("activate_campaign"), guard.SEND)
        self.assertEqual(guard.classify_tool("delete_lead"), guard.DELETE)

    def test_adding_leads_to_a_campaign_counts_as_a_send(self):
        self.assertEqual(guard.classify_tool("add_leads_to_campaign"), guard.SEND)

    def test_plugin_server_names(self):
        self.assertEqual(self.decision("mcp__plugin_sales_lemlist__send_email"), "ask")

    def test_lemlist_oauth_server_name_lm(self):
        self.assertEqual(self.decision("mcp__lm__delete_lead"), "ask")

    def test_non_sales_servers_are_ignored(self):
        self.assertIsNone(self.decision("mcp__notion__create_page"))
        self.assertIsNone(self.decision("mcp__github__create_issue"))

    def test_block_sends_mode(self):
        self.assertEqual(self.decision("mcp__instantly__activate_campaign", CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "deny")
        self.assertEqual(self.decision("mcp__attio__delete_record", CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "deny")
        # writes and credit spends still ask in block-sends mode
        self.assertEqual(self.decision("mcp__attio__create_record", CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "ask")
        self.assertEqual(self.decision("mcp__apollo__people_enrichment", CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "ask")

    def test_extra_servers(self):
        self.assertIsNone(self.decision("mcp__acme-crm__update_deal"))
        self.assertEqual(self.decision("mcp__acme-crm__update_deal", CLAUDE_PLUGIN_OPTION_EXTRA_SERVERS="acme-crm, other"), "ask")


class TrickyToolNames(unittest.TestCase):
    def test_dangerous_verbs_beat_a_leading_read_verb(self):
        self.assertEqual(guard.classify_tool("get_and_delete_contact"), guard.DELETE)
        self.assertEqual(guard.classify_tool("list_and_send_campaign"), guard.SEND)
        self.assertEqual(guard.classify_tool("search_and_enrich_people"), guard.SPEND)
        self.assertEqual(guard.classify_tool("get_or_create_contact"), guard.WRITE)

    def test_fewer_false_alarms(self):
        self.assertIsNone(guard.classify_tool("find_email_templates"))
        self.assertIsNone(guard.classify_tool("verify_domain"))
        self.assertIsNone(guard.classify_tool("get_email_activity"))
        self.assertEqual(guard.classify_tool("add_campaign_to_folder"), guard.WRITE)
        self.assertEqual(guard.classify_tool("schedule_meeting"), guard.WRITE)

    def test_adding_leads_on_a_sequencer_is_a_send(self):
        self.assertEqual(guard.classify_tool("add_leads", sequencer=True), guard.SEND)
        self.assertEqual(guard.classify_tool("add_leads", sequencer=False), guard.WRITE)
        self.assertTrue(guard.server_is_sequencer("instantly"))
        self.assertFalse(guard.server_is_sequencer("claude_ai_HubSpot"))


class RoundThreeRegressions(unittest.TestCase):
    """Misses and false alarms an outside review found (2026-11-25)."""

    def decision(self, tool_name, tool_input=None, **env):
        with tempfile.TemporaryDirectory() as data, \
                mock.patch.dict(os.environ, clean_env(CLAUDE_PLUGIN_DATA=data, **env), clear=True):
            result = guard.decide(payload(tool_name, tool_input))
        return result and result["hookSpecificOutput"]["permissionDecision"]

    def test_more_send_verbs(self):
        for tool in ("enable_campaign", "turn_on_campaign", "turnOnSequence", "dispatch_message",
                     "deliver_email", "post_tweet", "post_message", "queue_post", "publish_post"):
            self.assertEqual(guard.classify_tool(tool), guard.SEND, tool)

    def test_post_as_a_noun_is_not_a_send(self):
        for tool in ("list_posts", "get_post", "get_post_analytics"):
            self.assertIsNone(guard.classify_tool(tool), tool)

    def test_adding_to_a_sequence_is_a_send_on_any_guarded_server(self):
        for tool in ("add_to_sequence", "enroll_contact", "add_contacts_to_campaign", "assign_to_cadence"):
            self.assertEqual(guard.classify_tool(tool), guard.SEND, tool)
        self.assertEqual(self.decision("mcp__claude_ai_HubSpot__add_to_sequence",
                                       CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "deny")
        self.assertEqual(guard.classify_tool("add_campaign_to_folder"), guard.WRITE)

    def test_scheduling_on_a_social_publisher_is_a_send(self):
        self.assertEqual(guard.classify_tool("schedule_draft", publisher=True), guard.SEND)
        self.assertEqual(self.decision("mcp__typefully__schedule_draft", CLAUDE_PLUGIN_OPTION_MODE="block-sends"), "deny")
        self.assertEqual(guard.classify_tool("schedule_draft"), guard.WRITE)
        self.assertIsNone(guard.classify_tool("get_scheduled_posts", publisher=True))
        self.assertEqual(guard.classify_tool("create_draft", publisher=True), guard.WRITE)

    def test_paid_lookups_spend_credits(self):
        for tool in ("email_finder", "lookup_email", "lookup_person", "reveal_phone"):
            self.assertEqual(guard.classify_tool(tool), guard.SPEND, tool)
        self.assertIsNone(guard.classify_tool("lookup_company"))

    def test_plugin_prefixed_and_connector_extra_names(self):
        extra = {"CLAUDE_PLUGIN_OPTION_EXTRA_SERVERS": "acme-crm"}
        self.assertEqual(self.decision("mcp__plugin_x_acme-crm__update_deal", **extra), "ask")
        self.assertEqual(self.decision("mcp__claude_ai_Acme_CRM__update_deal", **extra), "ask")
        self.assertIsNone(self.decision("mcp__notacme-crm__update_deal", **extra))

    def test_extra_server_named_like_a_sequencer(self):
        self.assertEqual(self.decision("mcp__acme-sequencer__add_leads", CLAUDE_PLUGIN_OPTION_MODE="block-sends",
                                       CLAUDE_PLUGIN_OPTION_EXTRA_SERVERS="acme-sequencer"), "deny")
        self.assertEqual(self.decision("mcp__acme-crm__add_leads", CLAUDE_PLUGIN_OPTION_MODE="block-sends",
                                       CLAUDE_PLUGIN_OPTION_EXTRA_SERVERS="acme-crm"), "ask")

    def test_a_leading_read_verb_beats_reply(self):
        for tool in ("get_reply_status", "search_replies", "list_reply_metrics"):
            self.assertIsNone(guard.classify_tool(tool), tool)
        for tool in ("reply_to_thread", "get_and_reply", "get_and_send"):
            self.assertEqual(guard.classify_tool(tool), guard.SEND, tool)

    def test_non_dict_tool_input_never_crashes(self):
        self.assertEqual(self.decision("mcp__instantly__send_email", ["x"]), "ask")
        self.assertIsNone(self.decision("Bash", "curl -X POST https://api.hubapi.com/x"))
        self.assertIsNone(self.decision(5))
        result = run_script(GUARD, json.dumps(payload("mcp__lemlist__delete_lead", "not a dict")))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertEqual(result.stderr, "")

    def test_list_sizes_one_level_down(self):
        shape = guard.input_shape({"request": {"leads": [1, 2, 3], "maya@northwind.example": [1]}, "id": 1})
        self.assertEqual(shape["lists"], {"request.leads": 3})
        self.assertIn("request.leads: 3 items", guard.preview(shape))

    def test_log_lock_never_blocks(self):
        try:
            import fcntl
        except ImportError:
            self.skipTest("POSIX only")
        with tempfile.TemporaryDirectory() as data:
            path = os.path.join(data, "guard-log.jsonl")
            open(path, "a").close()
            with open(os.path.join(data, guard.LOCK_NAME), "a") as holder:
                fcntl.flock(holder, fcntl.LOCK_EX)
                with mock.patch.dict(os.environ, clean_env(CLAUDE_PLUGIN_DATA=data), clear=True):
                    started = guard.time.monotonic()
                    guard.write_log({"tool": "x"})
                    waited = guard.time.monotonic() - started
            self.assertLess(waited, 2.0)
            self.assertEqual(os.path.getsize(path), 0)  # the line was skipped, not forced in

    def test_log_rotates_at_the_cap(self):
        with tempfile.TemporaryDirectory() as data, \
                mock.patch.object(guard, "LOG_MAX_BYTES", 100), \
                mock.patch.dict(os.environ, clean_env(CLAUDE_PLUGIN_DATA=data), clear=True):
            with open(os.path.join(data, "guard-log.jsonl"), "w") as f:
                f.write("x" * 200)
            guard.write_log({"tool": "new"})
            with open(os.path.join(data, "guard-log.1.jsonl")) as f:
                self.assertEqual(f.read(), "x" * 200)
            with open(os.path.join(data, "guard-log.jsonl")) as f:
                self.assertEqual(json.loads(f.read())["tool"], "new")

    def test_print_only_commands_are_not_calls(self):
        self.assertIsNone(guard.classify_bash("echo 'curl -X POST https://api.hubapi.com/crm/v3/objects/contacts'"))
        self.assertIsNone(guard.classify_bash('printf "%s" "curl -d x https://api.apollo.io/api/v1/contacts"'))
        # chained or substituted commands still count, and the method is still not tied to the URL
        self.assertEqual(guard.classify_bash("echo https://api.hubapi.com && curl -X POST https://example.com")[1], guard.WRITE)
        self.assertEqual(guard.classify_bash("echo $(curl -X POST https://api.hubapi.com/x)")[1], guard.WRITE)


class RoundFourRegressions(unittest.TestCase):
    """Misses and false alarms a fourth outside review found (2026-11-25)."""

    def decide(self, tool_name, tool_input=None, **env):
        with tempfile.TemporaryDirectory() as data, \
                mock.patch.dict(os.environ, clean_env(CLAUDE_PLUGIN_DATA=data, **env), clear=True):
            result = guard.decide(payload(tool_name, tool_input))
            log = os.path.join(data, "guard-log.jsonl")
            lines = []
            if os.path.exists(log):
                with open(log) as f:
                    lines = f.read().splitlines()
        return result and result["hookSpecificOutput"], lines

    def test_lemlist_call_api_reads_the_method(self):
        for tool in ("mcp__lm__call_api", "mcp__lemlist__call_api"):
            out, _ = self.decide(tool, {"method": "POST", "path": "/api/campaigns/cam_1/start"})
            self.assertEqual(out["permissionDecision"], "ask", tool)
            self.assertIn("starts, resumes or feeds a sequence", out["permissionDecisionReason"])
            out, _ = self.decide(tool, {"method": "GET", "path": "/api/campaigns"})
            self.assertIsNone(out, tool)
            out, _ = self.decide(tool, {"method": "delete", "path": "/api/leads/x"})
            self.assertIn("deletes", out["permissionDecisionReason"])
            out, _ = self.decide(tool, {"path": "/api/campaigns"})
            self.assertEqual(out["permissionDecision"], "ask", tool)  # no method given: ask

    def test_call_api_method_one_level_down_and_block_mode(self):
        out, _ = self.decide("mcp__lm__call_api", {"request": {"httpMethod": "PATCH", "endpoint": "/api/leads/x"}})
        self.assertEqual(out["permissionDecision"], "ask")
        out, _ = self.decide("mcp__lm__call_api", {"method": "POST", "path": "/api/campaigns/cam_1/leads/a@b.example"},
                             CLAUDE_PLUGIN_OPTION_MODE="block-sends")
        self.assertEqual(out["permissionDecision"], "deny")  # adding a lead on a sequencer is a send

    def test_call_api_log_holds_method_and_path_never_values(self):
        _, lines = self.decide("mcp__lm__call_api", {
            "method": "POST", "path": "/api/campaigns/cam_1/leads/maya@northwind.example?token=abc",
            "body": {"firstName": "Maya", "email": "maya@northwind.example"}})
        record = json.loads(lines[-1])
        self.assertEqual(record["request"], {"method": "POST", "path": "/api/campaigns/*/leads/*"})
        self.assertNotIn("maya", lines[-1].lower())
        self.assertNotIn("abc", record["request"]["path"])

    def test_hidden_methods_and_ruby_count_as_writes(self):
        for command in ('METHOD=POST curl -X "$METHOD" https://api.hubapi.com/crm/v3/objects/contacts',
                        "curl -X $M https://api.hubapi.com/crm/v3/objects/contacts",
                        'curl --request "${M}" https://api.hubapi.com/crm/v3/objects/contacts',
                        'curl -X"$M" https://api.hubapi.com/crm/v3/objects/contacts',
                        "curl --config request.conf https://api.hubapi.com/crm/v3/objects/contacts",
                        "curl -K request.conf https://api.hubapi.com/crm/v3/objects/contacts",
                        "ruby -rnet/http -ruri -e 'u=URI(\"https://api.hubapi.com/crm/v3/objects/contacts\"); "
                        "Net::HTTP.post(u,\"{}\")'",
                        "ruby -e 'Net::HTTP.post_form(URI(\"https://api.hubapi.com/x\"), {})'",
                        "ruby -e 'Net::HTTP::Put.new(URI(\"https://api.hubapi.com/x\"))'"):
            self.assertEqual(guard.classify_bash(command), ("api.hubapi.com", guard.WRITE), command)
        self.assertEqual(guard.classify_bash(
            "ruby -e 'Net::HTTP::Delete.new(URI(\"https://api.attio.com/v2/objects/people/records/1\"))'"),
            ("api.attio.com", guard.DELETE))
        # GET forms still pass
        self.assertIsNone(guard.classify_bash("curl -X GET https://api.hubapi.com/crm/v3/objects/contacts"))
        self.assertIsNone(guard.classify_bash("curl -s https://api.hubapi.com/crm/v3/objects/contacts"))
        self.assertIsNone(guard.classify_bash("ruby -e 'Net::HTTP.get(URI(\"https://api.hubapi.com/x\"))'"))

    def test_python_print_of_a_string_is_print_only(self):
        self.assertIsNone(guard.classify_bash(
            "python3 -c 'print(\"curl -X POST https://api.hubapi.com/crm/v3/objects/contacts\")'"))
        self.assertIsNone(guard.classify_bash(
            "python -c \"print('curl -d x https://api.apollo.io/api/v1/contacts')\""))
        self.assertEqual(guard.classify_bash(
            "python3 -c 'import requests; requests.post(\"https://api.apollo.io/api/v1/contacts\")'"),
            ("api.apollo.io", guard.WRITE))
        self.assertEqual(guard.classify_bash(
            "python3 -c 'print(\"x\")' && curl -X POST https://api.hubapi.com/x")[1], guard.WRITE)
        self.assertEqual(guard.classify_bash(
            "python3 -c 'print(f\"{x}\")' https://api.hubapi.com -X POST")[1], guard.WRITE)

    def test_report_names_with_an_action_word_are_reads(self):
        for tool in ("get_send_status", "get_enrichment_status", "list_archive_records",
                     "list_archived_campaigns", "get_launch_history", "get_import_status"):
            self.assertIsNone(guard.classify_tool(tool), tool)
        self.assertEqual(guard.classify_tool("get_or_create_contact"), guard.WRITE)
        self.assertEqual(guard.classify_tool("find_and_enrich"), guard.SPEND)
        self.assertEqual(guard.classify_tool("search_and_send"), guard.SEND)
        self.assertEqual(guard.classify_tool("get_and_send_report"), guard.SEND)
        self.assertEqual(guard.classify_tool("lookup_email_status"), guard.SPEND)  # a paid lookup still spends

    def test_rotation_under_concurrent_writers_loses_nothing(self):
        try:
            import fcntl  # noqa: F401
        except ImportError:
            self.skipTest("POSIX only")
        writers, per_writer = 4, 15
        child = (
            "import importlib.util, sys\n"
            "s = importlib.util.spec_from_file_location('guard', sys.argv[1])\n"
            "g = importlib.util.module_from_spec(s); s.loader.exec_module(g)\n"
            "g.LOG_MAX_BYTES = 1500; g.LOCK_WAIT_SECONDS = 20\n"
            "for i in range(int(sys.argv[3])):\n"
            "    g.write_log({'w': sys.argv[2], 'i': i, 'pad': 'x' * 10})\n"
        )
        with tempfile.TemporaryDirectory() as data:
            env = clean_env(CLAUDE_PLUGIN_DATA=data)
            procs = [subprocess.Popen([sys.executable, "-c", child, GUARD, str(w), str(per_writer)], env=env)
                     for w in range(writers)]
            for proc in procs:
                self.assertEqual(proc.wait(timeout=60), 0)
            seen = []
            for name in ("guard-log.jsonl", "guard-log.1.jsonl"):
                with open(os.path.join(data, name)) as f:
                    seen += [(r["w"], r["i"]) for r in map(json.loads, f.read().splitlines())]
            expected = {(str(w), i) for w in range(writers) for i in range(per_writer)}
            self.assertEqual(sorted(seen), sorted(expected))  # each line once, none lost


class RoundFiveRegressions(unittest.TestCase):
    """A fifth outside review (2026-11-25): path values in the log, more hidden methods, sends."""

    decide = RoundFourRegressions.decide

    def test_log_path_keeps_route_words_only(self):
        values = ["MayaChen", "Acme-West", "customer_123", "abc123def",
                  "9f1c2b7e-1d2a-4c3b-9a8e-123456789abc", "maya@northwind.example", "48213"]
        for value in values:
            _, lines = self.decide("mcp__lm__call_api",
                                   {"method": "PATCH", "path": "/api/contacts/%s/Acme-West" % value})
            self.assertNotIn(value.lower(), lines[-1].lower(), value)
            self.assertNotIn("acme-west", lines[-1].lower())  # "project" is the cwd folder name, by design
            self.assertEqual(json.loads(lines[-1])["request"]["path"], "/api/contacts/*/*")
        self.assertEqual(guard.safe_path("https://api.hubapi.com/crm/v3/objects/contacts/search?q=x"),
                         "/crm/v3/objects/*/*")  # the part after any collection noun is an id slot
        self.assertEqual(guard.safe_path("/v2/objects/people/records/%s" % values[4]),
                         "/v2/objects/*/*/*")

    def test_form_string_and_dynamic_methods_count_as_writes(self):
        host = "https://api.hubapi.com/crm/v3/objects/contacts"
        for command in ("curl --form-string note=x " + host,
                        'wget --method="$METHOD" ' + host,
                        "wget --method=$M " + host,
                        "node -e \"fetch('%s', {method: process.env.METHOD})\"" % host,
                        "node -e \"axios({url: '%s', method: m})\"" % host,
                        "python3 -c \"import os,requests; requests.request(os.environ['METHOD'], '%s')\"" % host,
                        "python3 -c \"import httpx; httpx.request(m, '%s')\"" % host,
                        "python3 -c \"import requests; requests.request(method=m, url='%s')\"" % host,
                        "python3 -c \"import requests; requests.request('POST', '%s')\"" % host):
            self.assertEqual(guard.classify_bash(command), ("api.hubapi.com", guard.WRITE), command)
        for command in ("wget --method=GET " + host,
                        "node -e \"fetch('%s', {method: 'GET'})\"" % host,
                        "python3 -c \"import requests; requests.request('GET', '%s')\"" % host,
                        "python3 -c \"import requests; requests.request(method='GET', url='%s')\"" % host):
            self.assertIsNone(guard.classify_bash(command), command)

    def test_block_sends_denies_enrolment_not_record_upkeep(self):
        mode = {"CLAUDE_PLUGIN_OPTION_MODE": "block-sends"}
        for tool_input in ({"method": "PATCH", "path": "/api/leads/123"},
                           {"method": "PUT", "path": "/api/leads/maya@northwind.example"},
                           {"method": "POST", "path": "/api/leads/search"}):
            out, _ = self.decide("mcp__lm__call_api", tool_input, **mode)
            self.assertEqual(out["permissionDecision"], "ask", tool_input)
        for tool_input in ({"method": "POST", "path": "/api/campaigns/cam_1/leads"},
                           {"method": "POST", "path": "/api/campaigns/cam_1/leads/maya@northwind.example"},
                           {"method": "POST", "path": "/api/campaigns/cam_1/start"}):
            out, _ = self.decide("mcp__lm__call_api", tool_input, **mode)
            self.assertEqual(out["permissionDecision"], "deny", tool_input)


class RoundSixRegressions(unittest.TestCase):
    """A sixth outside review (2026-11-25) of the guard: id slots, methods, JS and PowerShell forms, enrolment."""

    decide = RoundFourRegressions.decide

    def test_part_after_a_collection_noun_is_a_value(self):
        self.assertEqual(guard.safe_path("/api/campaigns/launch"), "/api/campaigns/*")
        self.assertEqual(guard.safe_path("/api/campaigns/123/launch"), "/api/campaigns/*/launch")
        self.assertEqual(guard.safe_path("/api/leads/search/start"), "/api/leads/*/start")
        _, lines = self.decide("mcp__lm__call_api", {"method": "PATCH", "path": "/api/campaigns/launch"})
        self.assertEqual(json.loads(lines[-1])["request"]["path"], "/api/campaigns/*")
        self.assertNotIn("launch", lines[-1])

    def test_only_method_names_are_logged(self):
        out, lines = self.decide("mcp__lm__call_api", {"method": "maya@northwind.example", "path": "/api/leads"})
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertNotIn("maya", lines[-1].lower())
        self.assertNotIn("maya", out["permissionDecisionReason"].lower())
        self.assertEqual(json.loads(lines[-1])["request"]["method"], "unknown")

    def test_dynamic_js_and_powershell_methods_ask(self):
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        for command in ("node -e \"fetch('%s', {method})\"" % url,
                        "node -e \"fetch('%s', {headers, method, body})\"" % url,
                        "node -e 'axios({url:\"%s\", \"method\":process.env.METHOD})'" % url,
                        "pwsh -c \"$p=@{Uri='%s'; Method=$env:METHOD}; Invoke-RestMethod @p\"" % url,
                        "node -e 'axios({url:\"%s\", \"method\":\"POST\"})'" % url,
                        "pwsh -c \"$p=@{Uri='%s'; Method='Post'}; Invoke-RestMethod @p\"" % url):
            self.assertEqual(guard.classify_bash(command), ("api.hubapi.com", guard.WRITE), command)
        for command in ("node -e 'axios({url:\"%s\", \"method\":\"GET\"})'" % url,
                        "node -e \"fetch('%s', {method: 'GET'})\"" % url,
                        "pwsh -c \"$p=@{Uri='%s'; Method='Get'}; Invoke-RestMethod @p\"" % url,
                        "pwsh -c \"Invoke-RestMethod -Uri '%s' -Method Get\"" % url):
            self.assertIsNone(guard.classify_bash(command), command)

    def test_bash_enrolment_on_a_sequencer_is_a_send(self):
        add = "curl -X POST https://api.instantly.ai/api/v2/campaigns/abc/leads -d '{}'"
        self.assertEqual(guard.classify_bash(add), ("api.instantly.ai", guard.SEND))
        self.assertEqual(guard.classify_bash(
            "curl -X POST https://api.lemlist.com/api/campaigns/cam_1/leads/maya@northwind.example?deduplicate=true"),
            ("api.lemlist.com", guard.SEND))
        self.assertEqual(guard.classify_bash(
            "curl -X POST https://api.instantly.ai/api/v2/campaigns/abc/leads/search -d '{}'"),
            ("api.instantly.ai", guard.WRITE))
        self.assertEqual(guard.classify_bash(
            "curl -X PATCH https://api.instantly.ai/api/v2/campaigns/abc/leads -d '{}'"),
            ("api.instantly.ai", guard.WRITE))
        self.assertEqual(guard.classify_bash(
            "curl -X POST https://api.hubapi.com/crm/v3/objects/campaigns/abc/contacts -d '{}'"),
            ("api.hubapi.com", guard.WRITE))  # not a sequencer host
        with tempfile.TemporaryDirectory() as data, mock.patch.dict(
                os.environ, clean_env(CLAUDE_PLUGIN_DATA=data), clear=True):
            out = guard.decide(payload("Bash", {"command": add}))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")
        with tempfile.TemporaryDirectory() as data, mock.patch.dict(
                os.environ, clean_env(CLAUDE_PLUGIN_DATA=data, CLAUDE_PLUGIN_OPTION_MODE="block-sends"), clear=True):
            out = guard.decide(payload("Bash", {"command": add}))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_enrol_path_is_anchored(self):
        mode = {"CLAUDE_PLUGIN_OPTION_MODE": "block-sends"}
        for path in ("/api/campaigns/cam_1/leads/search", "/api/campaigns/cam_1/leads/search?x=1",
                     "/api/campaigns/cam_1/leads/maya@northwind.example/notes"):
            out, _ = self.decide("mcp__lm__call_api", {"method": "POST", "path": path}, **mode)
            self.assertEqual(out["permissionDecision"], "ask", path)
        for path in ("/api/campaigns/cam_1/leads?deduplicate=true", "/api/campaigns/cam_1/leads/bulk",
                     "/api/sequences/s1/contacts/import", "/api/campaigns/cam_1/leads/maya@northwind.example"):
            out, _ = self.decide("mcp__lm__call_api", {"method": "POST", "path": path}, **mode)
            self.assertEqual(out["permissionDecision"], "deny", path)


class RoundSevenRegressions(unittest.TestCase):
    """A seventh outside review (2026-11-25) of the guard."""

    def test_collection_word_in_an_id_slot_masks_the_next_part(self):
        self.assertEqual(guard.safe_path("/api/objects/campaigns/launch"), "/api/objects/*/*")
        self.assertEqual(guard.safe_path("/api/campaigns/123/launch"), "/api/campaigns/*/launch")
        self.assertEqual(guard.safe_path("/api/lists/leads/contacts/MayaChen"), "/api/lists/*/*/*")
        for path in ("/api/objects/campaigns/launch", "/api/teams/leads/start", "/api/objects/people/search"):
            kept = [p for p in guard.safe_path(path).split("/") if p not in ("", "*")]
            self.assertEqual(kept, ["api", path.split("/")[2]], path)

    def test_attached_and_clustered_body_options_are_posts(self):
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        for command in ("curl -dname=Maya " + url, "curl -Ffile=@leads.csv " + url,
                        "curl --data-raw=x " + url, "curl -sd 'name=Maya' " + url,
                        "curl -sSF file=@leads.csv " + url, "curl --form-string a=b " + url):
            self.assertEqual(guard.classify_bash(command), ("api.hubapi.com", guard.WRITE), command)
        for command in ("curl -sSL " + url, "curl -o out.json " + url, "curl -D headers.txt " + url):
            self.assertIsNone(guard.classify_bash(command), command)

    def test_httpie_data_items_mean_post(self):
        url = "https://api.attio.com/v2/objects/people/records"
        for tool in ("http", "https", "xh"):
            for items in ("name=Maya", "age:=34", "photo@me.png", "bio=@bio.txt", "tags:=@tags.json"):
                command = "%s %s %s" % (tool, url, items)
                self.assertEqual(guard.classify_bash(command), ("api.attio.com", guard.WRITE), command)
            for items in ("", "Authorization:'Bearer $T'", "limit==10", "X-Email:maya@northwind.example"):
                command = ("%s %s %s" % (tool, url, items)).strip()
                self.assertIsNone(guard.classify_bash(command), command)
            self.assertIsNone(guard.classify_bash("%s GET %s name==Maya" % (tool, url)))
            self.assertIsNone(guard.classify_bash("%s --print=HhBb GET %s" % (tool, url)))
        self.assertEqual(guard.classify_bash("http --form %s name=Maya" % url), ("api.attio.com", guard.WRITE))
        self.assertEqual(guard.classify_bash("http POST %s" % url), ("api.attio.com", guard.WRITE))


class ClassifyBash(unittest.TestCase):
    def test_attached_flags_clients_and_powershell(self):
        cases = {
            "curl -XPOST https://api.instantly.ai/api/v2/campaigns/x/activate": guard.SEND,
            "curl --request=POST https://api.hubapi.com/crm/v3/objects/contacts": guard.WRITE,
            "curl -d'{}' https://api.apollo.io/api/v1/contacts": guard.WRITE,
            "curl --upload-file leads.csv https://api.hubapi.com/files/v3/files": guard.WRITE,
            "node -e \"axios.post('https://api.hubapi.com/crm/v3/objects/contacts', body)\"": guard.WRITE,
            "Invoke-RestMethod -Method Post -Uri https://api.hubapi.com/crm/v3/objects/contacts": guard.WRITE,
            "http POST https://api.attio.com/v2/objects/people/records name=x": guard.WRITE,
        }
        for command, category in cases.items():
            self.assertEqual(guard.classify_bash(command)[1], category, command)

    def test_lookalike_hosts_do_not_count(self):
        self.assertIsNone(guard.classify_bash("curl -X POST https://api.hubapi.com.evil.example/x"))

    def test_salesforce_instance_hosts(self):
        self.assertEqual(guard.classify_bash(
            "curl -X PATCH https://acme.my.salesforce.com/services/data/v60.0/sobjects/Lead/1")[1], guard.WRITE)

    def test_get_requests_pass_through(self):
        self.assertIsNone(guard.classify_bash("curl -s https://api.hubapi.com/crm/v3/objects/contacts"))
        self.assertIsNone(guard.classify_bash("ls -la"))

    def test_curl_writes(self):
        self.assertEqual(guard.classify_bash(
            "curl -X POST https://api.instantly.ai/api/v2/campaigns/abc/activate"), ("api.instantly.ai", guard.SEND))
        self.assertEqual(guard.classify_bash(
            "curl -X DELETE https://api.attio.com/v2/objects/people/records/1"), ("api.attio.com", guard.DELETE))
        self.assertEqual(guard.classify_bash(
            "curl https://api.hubapi.com/crm/v3/objects/contacts -d '{}'"), ("api.hubapi.com", guard.WRITE))

    def test_python_requests_write(self):
        self.assertEqual(guard.classify_bash(
            "python3 -c \"import requests; requests.post('https://api.apollo.io/api/v1/contacts')\""),
            ("api.apollo.io", guard.WRITE))


class LogAndOutput(unittest.TestCase):
    def test_log_holds_field_names_and_sizes_never_values(self):
        with tempfile.TemporaryDirectory() as data:
            result = run_script(GUARD, json.dumps(payload(
                "mcp__instantly__add_leads_to_campaign",
                {"campaign_id": "cmp_123", "leads": [{"email": "maya@northwind.example"}] * 3})),
                CLAUDE_PLUGIN_DATA=data)
            self.assertEqual(result.returncode, 0)
            out = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "PreToolUse")
            self.assertEqual(out["permissionDecision"], "ask")
            self.assertIn("leads: 3 items", out["permissionDecisionReason"])
            with open(os.path.join(data, "guard-log.jsonl"), encoding="utf-8") as f:
                line = f.read()
            record = json.loads(line)
            self.assertEqual(record["fields"], ["campaign_id", "leads"])
            self.assertEqual(record["list_sizes"], {"leads": 3})
            self.assertNotIn("northwind", line)
            self.assertNotIn("cmp_123", line)

    def test_log_can_be_turned_off(self):
        with tempfile.TemporaryDirectory() as data:
            run_script(GUARD, json.dumps(payload("mcp__apollo__people_enrichment")),
                       CLAUDE_PLUGIN_DATA=data, CLAUDE_PLUGIN_OPTION_LOG_CALLS="false")
            self.assertFalse(os.path.exists(os.path.join(data, "guard-log.jsonl")))

    def test_keys_that_are_not_field_names_are_counted_not_logged(self):
        with tempfile.TemporaryDirectory() as data:
            run_script(GUARD, json.dumps(payload("mcp__attio__create_record", {"maya@northwind.example": {}, "name": "x"})),
                       CLAUDE_PLUGIN_DATA=data)
            with open(os.path.join(data, "guard-log.jsonl"), encoding="utf-8") as f:
                line = f.read()
            self.assertNotIn("northwind", line)
            self.assertEqual(json.loads(line)["other_fields"], 1)

    def test_powershell_tool_is_checked(self):
        out = run_script(GUARD, json.dumps(payload("PowerShell", {
            "command": "Invoke-RestMethod -Method Delete -Uri https://api.attio.com/v2/objects/people/records/1"})))
        self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_bad_input_is_silent_and_never_fails(self):
        for stdin in ("", "not json", "[]", '{"tool_name": 5}'):
            result = run_script(GUARD, stdin)
            self.assertEqual(result.returncode, 0, stdin)
            self.assertEqual(result.stdout, "", stdin)



class RoundEightRegressions(unittest.TestCase):
    """Combined curl flags and HTTPie forms from the eighth review."""

    def cat(self, command):
        r = guard.classify_bash(command)
        return r[1] if r else None

    def test_combined_curl_flags_are_writes(self):
        for cmd in ("curl -sXPOST https://api.hubapi.com/crm/v3/objects/contacts",
                    "curl -sFfile=@leads.csv https://api.hubapi.com/crm/v3/objects/contacts",
                    "curl -sdname=Maya https://api.hubapi.com/crm/v3/objects/contacts",
                    'curl -sX "$M" https://api.hubapi.com/crm/v3/objects/contacts'):
            self.assertIsNotNone(self.cat(cmd), cmd)

    def test_httpie_flags_before_method_and_raw_bodies(self):
        for cmd in ("http -f POST https://api.attio.com/v2/objects/people/records name=Maya",
                    "http --verify=no POST https://api.attio.com/v2/objects/people/records",
                    "http --raw '{\"name\":\"Maya\"}' https://api.attio.com/v2/objects/people/records",
                    "printf '{}' | http https://api.attio.com/v2/objects/people/records"):
            self.assertIsNotNone(self.cat(cmd), cmd)

    def test_reads_still_pass(self):
        for cmd in ("curl -fsSL https://api.hubapi.com/crm/v3/objects/contacts",
                    "curl -sS https://api.hubapi.com/crm/v3/objects/contacts?limit=5",
                    "http GET https://api.attio.com/v2/objects/people/records",
                    "printf '' | http GET https://api.attio.com/v2/objects/people/records"):
            self.assertIsNone(self.cat(cmd), cmd)


if __name__ == "__main__":
    unittest.main()
