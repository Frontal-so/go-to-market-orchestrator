"""Shared helpers for the tests. Standard library only."""

import importlib.util
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, "plugins", "gtm-guard", "scripts", "guard.py")
NOTIFY = os.path.join(ROOT, "plugins", "gtm-notify", "scripts", "notify.py")
MIGRATE = os.path.join(ROOT, "scripts", "remove-v1-hooks.py")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_env(**extra):
    """The test process's environment minus anything the scripts read, plus `extra`."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("CLAUDE_PLUGIN_", "GTM_", "SLACK_", "DISCORD_"))}
    env.update(extra)
    return env


def run_script(path, stdin, args=(), **env):
    return subprocess.run([sys.executable, path, *args], input=stdin, capture_output=True,
                          text=True, env=clean_env(**env), timeout=30)
