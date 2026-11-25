#!/usr/bin/env python3
"""Remove what the April 2026 (v1) installer of go-to-market-orchestrator left behind.

v1's scripts/install.sh merged up to 30 hooks into your GLOBAL
~/.claude/settings.json (every command calls $CLAUDE_GTM_DIR/orchestrator/run.sh)
and copied skills, agents and a command into ~/.claude/. Those hooks fire in
every project, on every turn or tool call, whether you use the repo or not.

This script:
  1. lists the v1 hooks in a settings file, and with --apply removes them
     (a timestamped backup of the file is written first);
  2. lists the v1 skill, agent and command copies in ~/.claude/ (only files
     that are byte for byte a v1 file, or links into a v1 clone; a skill of
     your own with the same name is left alone, even when v1's install record
     lists that name), and with --apply --move-copies moves them into a backup
     folder (nothing is deleted).

A v1 hook is one whose whole command is v1's own form,
bash "$CLAUDE_GTM_DIR/orchestrator/run.sh" <tool> <action>. It never touches a
settings file it cannot parse, and it leaves every other hook exactly as it was.

    python3 scripts/remove-v1-hooks.py                 # dry run: show what would change
    python3 scripts/remove-v1-hooks.py --apply         # remove the v1 hooks
    python3 scripts/remove-v1-hooks.py --apply --move-copies
    python3 scripts/remove-v1-hooks.py --settings .claude/settings.json --apply

Standard library only, Python 3.9+.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import stat
import sys
import tempfile

# Every v1 hook command was exactly: bash "$CLAUDE_GTM_DIR/orchestrator/run.sh" <tool> <action>
# (30 hooks, all in this form). Quoted or not, ${...} or $..., with or without "bash".
_V1_HOOK_RE = re.compile(
    r"""^\s*(?:bash\s+)?(["']?)\$(?:\{CLAUDE_GTM_DIR\}|CLAUDE_GTM_DIR)/orchestrator/run\.sh\1"""
    r"""\s+[a-z0-9][a-z0-9-]*\s+[a-z0-9][a-z0-9-]*\s*$""")

V1_SKILLS = ["campaign-builder", "lead-enrichment", "personalization-writer",
             "pipeline-reviewer", "reply-classifier", "signal-monitor"]
V1_AGENTS = ["hook-writer.md", "lead-prioritizer.md", "meeting-prep.md", "prospect-profiler.md",
             "reply-classifier.md", "sequence-builder.md", "signal-scraper.md"]
V1_COMMANDS = ["outbound-pipeline.md"]
V1_MARKER_FILE = ".gtm-installed.json"


def is_v1_hook(hook) -> bool:
    command = hook.get("command") if isinstance(hook, dict) else None
    return isinstance(command, str) and bool(_V1_HOOK_RE.match(command))


def strip_v1_hooks(settings: dict):
    """Return (new_settings, removed) where removed lists (event, matcher, command)."""
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return settings, []
    removed = []
    new_hooks = {}
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            new_hooks[event] = groups
            continue
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                kept_groups.append(group)
                continue
            kept = []
            for hook in group["hooks"]:
                if is_v1_hook(hook):
                    removed.append((event, group.get("matcher", ""), hook.get("command", "")))
                else:
                    kept.append(hook)
            if kept:
                new_group = dict(group)
                new_group["hooks"] = kept
                kept_groups.append(new_group)
            elif not group["hooks"]:
                kept_groups.append(group)  # it was already empty; not ours to judge
        if kept_groups:
            new_hooks[event] = kept_groups
    result = dict(settings)
    if new_hooks:
        result["hooks"] = new_hooks
    else:
        result.pop("hooks", None)
    return result, removed


# sha256 of the files v1 (2026-04-27) copied into ~/.claude
V1_HASHES = {
    "fd81645e57525e9741e05eb9a4fa409a7aef25fc6ed5e03e98f9e9f4f711e45e", "7cea8a765b7ad3679ff592a71595c2898fdd331ea0fa85d429182d31d57bab1a",
    "01575c6e72584c1164f28d41ab7cf4d232bf36ef8f3bfeaa04b464b0464c4753", "76c37331d6bcfcd8060e95765f0508a3ae230e8b22b31526e91927d585b258f8",
    "96e1f118fe58c884fa9509403f4691879a83bf2cd401a80aeb1a94c8d3915877", "ef939f523da73dae2c02004502ab64c54af5dac329ac8ee4fa61313032d7919d",
    "3af71e779149d76dc493c695dd0ee84c40e791f3626cb1a6293b5970b0ffe031", "7a82c0a666776be35799163c8dc9dd1b594439c3d8444fd8ff77dd057ea62eb0",
    "e2064e732305133709f2d439c8ac1451e94056b17ec97bec5020b46cf7520846", "a1aa9fbcaf7fab037cb5f9bee9ef8e78f54d4cfc98c60635bcb5b990f4f29929",
    "51f4124640b4fff2bb6d999e864e61f15228fb80ed4864d9a748f62c79d87e5f", "b99f1caa882accccef44471fce4fdf4e102ee65e93136e022fa0c61096753115",
    "26c038d0bc00097285d08705118423a59c19fd3065cd89a6f48150bd634c122f", "2ba080d1270377a8116b77a092b9c18a0dde1ccc5209151e496e945ab14e969b",
}


def installer_record(claude_home: str) -> dict:
    """v1's own install record (~/.claude/.gtm-installed.json), or {} if absent or unreadable."""
    try:
        with open(os.path.join(claude_home, V1_MARKER_FILE), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def sha256(path: str) -> str:
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# Where v1 kept each kind of file inside its clone (install.sh copied or linked from there).
_V1_LAYOUT = {"skills": "skills/{name}/SKILL.md", "agents": "agents/{name}", "commands": "agents/commands/{name}"}


def looks_like_v1_clone(directory: str) -> bool:
    return os.path.isfile(os.path.join(directory, "orchestrator", "run.sh"))


def link_into_v1_clone(link: str, rel: str, record_root: str = "") -> bool:
    """True when `link` is a symlink whose resolved target is `<clone>/<rel>` and <clone> is a v1 clone.

    <clone> counts as a v1 clone when it holds orchestrator/run.sh, or (for a dangling link
    into a clone deleted since) when it is exactly the `root` that v1's own install record names.
    """
    if not os.path.islink(link):
        return False
    target = os.path.realpath(link)
    suffix = os.sep + rel.replace("/", os.sep)
    if not target.endswith(suffix):
        return False
    clone = target[: -len(suffix)]
    if not clone:
        return False
    if looks_like_v1_clone(clone):
        return True
    return bool(record_root) and clone == os.path.realpath(record_root)


def is_v1_copy(path: str, kind: str, recorded: set, record_root: str = "") -> bool:
    """True only with real evidence: an exact v1 file (sha256), or a link into a v1 clone.

    Being listed in v1's install record is not enough on its own: the file there may have been
    replaced by one of your own since. The record only lets a link into its own `root` count.
    """
    name = os.path.basename(path)
    root = record_root if name in recorded else ""
    rel = _V1_LAYOUT[kind].format(name=name)
    if kind == "skills":
        if link_into_v1_clone(path, os.path.dirname(rel), root):  # the whole skill folder is a link
            return True
        target = os.path.join(path, "SKILL.md")
    else:
        target = path
    if link_into_v1_clone(target, rel, root):
        return True
    if os.path.islink(target) or (kind == "skills" and os.path.islink(path)):
        return False  # a link, but not into a v1 clone: not ours to move
    try:
        return os.path.isfile(target) and sha256(target) in V1_HASHES
    except OSError:
        return False


def find_copies(claude_home: str):
    """(found, kept): v1 copies to move, and names v1's record lists that no longer match v1 (left alone)."""
    record = installer_record(claude_home)
    record_root = record.get("root") if isinstance(record.get("root"), str) else ""
    found, kept = [], []
    for kind, names in (("skills", V1_SKILLS), ("agents", V1_AGENTS), ("commands", V1_COMMANDS)):
        listed = record.get(kind) if isinstance(record.get(kind), list) else []
        recorded = {n for n in listed if n in names}
        for name in names:
            path = os.path.join(claude_home, kind, name)
            if not os.path.lexists(path):
                continue
            if is_v1_copy(path, kind, recorded, record_root):
                found.append(path)
            elif name in recorded:
                kept.append(path)
    if record:
        found.append(os.path.join(claude_home, V1_MARKER_FILE))
    return found, kept


def unique_path(base: str) -> str:
    path, n = base, 1
    while os.path.lexists(path):
        n += 1
        path = f"{base}-{n}"
    return path


_MASKS = [
    # webhook URLs carry their secret in the path
    (re.compile(r"https?://(?:hooks\.slack\.com|(?:[a-z]+\.)?discord(?:app)?\.com/api/webhooks|hooks\.zapier\.com)"
                r"/[^\s'\"]*", re.IGNORECASE), "[webhook URL]"),
    (re.compile(r"\b(Bearer|Basic|Token)\s+[^\s'\"]+", re.IGNORECASE), r"\1 [...]"),
    # API_KEY=..., token: ..., --password=..., ?access_token=...
    (re.compile(r"((?:[A-Za-z0-9_\-]*(?:key|token|secret|passw(?:or)?d|pwd)[A-Za-z0-9_\-]*)\s*[=:]\s*)"
                r"(\"[^\"]*\"|'[^']*'|[^\s&'\"]+)", re.IGNORECASE), r"\1[...]"),
    (re.compile(r"[A-Za-z0-9_\-]{24,}"), "[...]"),  # any other long token
]


def mask(command: str) -> str:
    """Secrets in a hook command are masked before printing, then the line is cut to 160 characters."""
    for pattern, repl in _MASKS:
        command = pattern.sub(repl, command)
    return command[:160]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--settings", default=None,
                        help="settings file to clean (default: ~/.claude/settings.json)")
    parser.add_argument("--claude-home", default=os.environ.get("CLAUDE_HOME") or os.path.expanduser("~/.claude"))
    parser.add_argument("--apply", action="store_true", help="write the change (default is a dry run)")
    parser.add_argument("--move-copies", action="store_true",
                        help="also move v1 skill/agent/command copies into a backup folder")
    args = parser.parse_args(argv)

    claude_home = os.path.abspath(os.path.expanduser(args.claude_home))
    settings_path = os.path.abspath(os.path.expanduser(args.settings or os.path.join(claude_home, "settings.json")))
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    exit_code = 0

    print(f"Settings file: {settings_path}")
    if not os.path.isfile(settings_path):
        print("  not found, nothing to clean.")
    else:
        real_path = os.path.realpath(settings_path)  # a symlinked settings file is edited where it lives
        try:
            with open(real_path, "rb") as f:
                original = f.read()
            settings = json.loads(original.decode("utf-8"))
        except OSError as e:
            print(f"  could not read it ({e}). Nothing was changed.")
            return 3
        except ValueError as e:
            print(f"  could not parse it ({e}). Nothing was changed; fix the JSON first.")
            return 2
        if not isinstance(settings, dict):
            print("  it is not a JSON object. Nothing was changed.")
            return 2
        cleaned, removed = strip_v1_hooks(settings)
        if not removed:
            print("  no v1 hooks found.")
        else:
            print(f"  {len(removed)} v1 hook(s){' removed' if args.apply else ' would be removed'}:")
            for event, matcher, command in removed:
                print(f"    {event:<16} {('matcher=' + matcher) if matcher else '':<22} {mask(command)}")
            if args.apply:
                backup = unique_path(f"{settings_path}.bak-v1-{stamp}")
                tmp = None
                try:
                    mode = stat.S_IMODE(os.stat(real_path).st_mode)  # a 0600 settings file keeps 0600, backup included
                    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
                    with os.fdopen(fd, "wb") as f:
                        os.fchmod(f.fileno(), mode)
                        f.write(original)
                    # an exclusive temp file with an unpredictable name, beside the real file
                    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(real_path), prefix=".settings-v1-clean-", suffix=".tmp")
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        os.fchmod(f.fileno(), mode)
                        json.dump(cleaned, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                    # Last look right before the swap. A write landing between this read and os.replace
                    # would still be lost: that window is a few microseconds, and the backup above holds
                    # the file as it was when this script read it.
                    with open(real_path, "rb") as f:
                        if f.read() != original:
                            os.remove(tmp)
                            print("  the file changed while this ran (is Claude Code open?). Nothing was changed; run it again.")
                            return 4
                    os.replace(tmp, real_path)
                    tmp = None
                except OSError as e:
                    if tmp and os.path.exists(tmp):
                        os.remove(tmp)
                    print(f"  could not write it ({e}). The file was not changed.")
                    return 3
                print(f"  backup: {backup}")

    copies, kept = find_copies(claude_home)
    print(f"\nv1 copies in {claude_home}:")
    if not copies:
        print("  none found.")
    elif args.move_copies and args.apply:
        backup_dir = unique_path(os.path.join(claude_home, f"gtm-v1-backup-{stamp}"))
        marker = os.path.join(claude_home, V1_MARKER_FILE)
        moved, not_moved = [], []

        def move(path):
            dest = os.path.join(backup_dir, os.path.relpath(path, claude_home))
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(path, dest)  # a symlink is moved as a link
                moved.append((path, dest))
            except OSError as e:
                not_moved.append((path, e))

        for path in copies:
            if path != marker:
                move(path)
        # v1's install record goes last, and only when everything else moved: a re-run needs its
        # recorded root to recognise a link left dangling by a deleted clone.
        marker_kept = marker in copies and bool(not_moved)
        if marker in copies and not marker_kept:
            move(marker)
        for path, dest in moved:
            print(f"  moved {path} -> {dest}")
        if not_moved or marker_kept:
            print(f"  NOT moved ({len(not_moved) + marker_kept}), still in place:")
            for path, e in not_moved:
                print(f"    {path}: {e}")
            if marker_kept:
                print(f"    {marker}: kept so a re-run still knows v1's install folder; "
                      "it moves once everything above has moved")
            print(f"  {len(moved)} moved to {backup_dir}, {len(not_moved) + marker_kept} not moved. "
                  "Fix the cause and run it again.")
            exit_code = 3
    else:
        for path in copies:
            print(f"  {path}")
        print("  (add --apply --move-copies to move them into a backup folder)")
    if kept:
        print("  left alone (v1's install record lists them, but they are no longer v1's files):")
        for path in kept:
            print(f"    {path}")

    if not args.apply:
        print("\nDry run: nothing was changed. Run again with --apply to make the change.")
    print("\nAlso check by hand: the `export CLAUDE_GTM_DIR=...` line in your shell profile, and the v1 .env "
          "file. If you ever shared hook logs or ran v1 with real keys, rotate those keys.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
