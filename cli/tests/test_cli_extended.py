"""Extended CLI tests: --config, --exclude, edge cases, Unicode, binary files."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

CLI = [sys.executable, "-m", "promptlint"]


def run(*args: str, cwd: str | Path | None = None, input_data: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*CLI, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        input=input_data,
        timeout=30,
    )


# ── --config flag ───────────────────────────────────────────────────────


class TestConfigFlag:
    def test_custom_config_changes_model(self, tmp_path):
        cfg = tmp_path / "custom.yaml"
        cfg.write_text(textwrap.dedent("""\
            model: gpt-3.5-turbo
            token_limit: 50
        """), encoding="utf-8")
        prompt = tmp_path / "p.txt"
        prompt.write_text("Hello world", encoding="utf-8")
        r = run("--file", str(prompt), "--config", str(cfg), "--format", "json")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        cost_finding = [f for f in data["findings"] if f["rule"] == "cost"]
        assert len(cost_finding) == 1
        assert "gpt-3.5-turbo" in cost_finding[0]["message"]

    def test_nonexistent_config_error(self, tmp_path):
        r = run("-t", "Hello", "--config", str(tmp_path / "nope.yaml"))
        assert r.returncode != 0

    def test_config_disables_rule(self, tmp_path):
        cfg = tmp_path / "quiet.yaml"
        cfg.write_text(textwrap.dedent("""\
            rules:
              politeness_bloat:
                enabled: false
        """), encoding="utf-8")
        prompt = tmp_path / "p.txt"
        prompt.write_text("Please write code", encoding="utf-8")
        r = run("--file", str(prompt), "--config", str(cfg))
        assert "politeness-bloat" not in r.stdout


# ── --exclude flag ──────────────────────────────────────────────────────


class TestExcludeFlag:
    def test_exclude_removes_file(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("Hello from A", encoding="utf-8")
        b.write_text("Hello from B", encoding="utf-8")
        r = run(str(a), str(b), "--exclude", str(b))
        assert r.returncode == 0
        assert "1 file(s) scanned" in r.stdout

    def test_exclude_all_files_shows_help(self, tmp_path):
        a = tmp_path / "a.txt"
        a.write_text("Hello", encoding="utf-8")
        r = run(str(a), "--exclude", str(a))
        assert r.returncode == 0
        assert "usage:" in r.stdout.lower() or "promptlint" in r.stdout.lower()


# ── Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_string_text(self):
        r = run("-t", "")
        assert r.returncode == 0 or r.returncode == 2

    def test_whitespace_only(self):
        r = run("-t", "   ")
        assert r.returncode == 0 or r.returncode == 2

    def test_unicode_emoji(self):
        r = run("-t", "Write code \U0001F600 with emojis \u2603")
        assert r.returncode == 0
        assert "finding(s)" in r.stdout

    def test_cjk_text(self):
        r = run("-t", "\u8bf7\u5199\u4e00\u4e2aPython\u51fd\u6570")
        assert r.returncode == 0

    def test_binary_file_error(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\xff\xfe\xfd" * 100)
        r = run("--file", str(f))
        assert r.returncode != 0

    def test_fix_json_includes_optimized_prompt(self):
        r = run("-t", "Please write code", "--fix", "--format", "json")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "optimized_prompt" in data
        assert data["optimized_prompt"] is not None

    def test_show_dashboard_text_mode(self):
        r = run("-t", "Hello world", "--show-dashboard")
        assert r.returncode == 0
        assert "Savings Dashboard" in r.stdout or "Current Tokens" in r.stdout


# ── stdin pipe ──────────────────────────────────────────────────────────


class TestStdinPipe:
    def test_stdin_pipe(self):
        r = run(input_data="Hello world from stdin")
        assert r.returncode == 0
        assert "finding(s)" in r.stdout

    def test_stdin_json(self):
        r = run("--format", "json", input_data="Hello world from stdin")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "findings" in data


# ── empty politeness words ──────────────────────────────────────────────


class TestEmptyPolitenessWords:
    def test_empty_politeness_words_no_crash(self, tmp_path):
        cfg = tmp_path / "empty_pol.yaml"
        cfg.write_text(textwrap.dedent("""\
            rules:
              politeness_bloat:
                enabled: true
                words: []
        """), encoding="utf-8")
        prompt = tmp_path / "p.txt"
        prompt.write_text("Please write code", encoding="utf-8")
        r = run("--file", str(prompt), "--config", str(cfg))
        assert r.returncode == 0
        assert "politeness-bloat" not in r.stdout
