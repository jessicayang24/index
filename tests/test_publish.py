import contextlib
import copy
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import publish


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.data = {"categories": [{"name": "数据工具", "sites": [
            {"name": "Example", "description": "", "url": "https://example.com/"}
        ]}]}

    def test_url_only_and_optional_fields(self):
        entries = publish.parse_inbox("# 注释\nhttps://example.org/?a=1&b=2\nhttps://example.net/ | 网站 | 新分类 | 说明\n")
        self.assertEqual(entries[0][0], "待整理")
        self.assertEqual(entries[0][1]["name"], "example.org")
        self.assertEqual(entries[1][0], "新分类")
        self.assertEqual(entries[1][1]["description"], "说明")

    def test_bad_line_rejects_whole_batch(self):
        with self.assertRaises(ValueError):
            publish.parse_inbox("https://example.org/\njavascript:alert(1)")

    def test_repeat_import_is_idempotent(self):
        original = copy.deepcopy(self.data)
        entries = publish.parse_inbox("https://example.org/\nhttps://example.org/\nhttps://example.com/")
        with contextlib.redirect_stdout(io.StringIO()):
            merged, count = publish.merge(self.data, entries)
            again, second = publish.merge(merged, entries)
        self.assertEqual(count, 1)
        self.assertEqual(second, 0)
        self.assertEqual(again, merged)
        self.assertEqual(self.data, original)

    def run_fake_publish(self, push_fails=False, edit_during_push=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inbox = root / "新增网址.txt"
            original = "https://example.com/\n"
            inbox.write_text(original, encoding="utf-8")
            data_file = root / "sites.yml"
            data_file.write_text(yaml.safe_dump(self.data), encoding="utf-8")
            (root / ".local-publish").mkdir()

            def fake_git(*args, **kwargs):
                if args[:2] == ("branch", "--show-current"):
                    return "gh-pages"
                if args[:2] == ("remote", "get-url"):
                    return "https://github.com/jessicayang24/index.git"
                if args[:2] == ("rev-parse", "--git-path"):
                    return ".git/" + args[2]
                if args[0] == "push":
                    if push_fails:
                        raise ValueError("simulated authentication failure")
                    if edit_during_push:
                        inbox.write_text(original + "https://example.net/\n", encoding="utf-8")
                return ""

            with patch.object(publish, "ROOT", root), patch.object(publish, "INBOX", inbox), \
                 patch.object(publish.sites, "DATA", data_file), patch.object(publish, "git", fake_git), \
                 patch.object(publish, "changed_paths", return_value=set()), \
                 patch.object(publish.subprocess, "run"), contextlib.redirect_stdout(io.StringIO()):
                if push_fails:
                    with self.assertRaises(ValueError):
                        publish.publish()
                    self.assertEqual(inbox.read_text(), original)
                    self.assertEqual(list((root / ".local-publish").glob("*.txt")), [])
                else:
                    publish.publish()
                    backups = list((root / ".local-publish").glob("*.txt"))
                    self.assertEqual(len(backups), 1)
                    self.assertEqual(backups[0].read_text(), original)
                    self.assertEqual(inbox.read_text(), original + "https://example.net/\n" if edit_during_push else publish.EMPTY_INBOX)

    def test_failed_push_preserves_input(self):
        self.run_fake_publish(push_fails=True)

    def test_success_backs_up_and_clears(self):
        self.run_fake_publish()

    def test_edits_during_push_are_preserved(self):
        self.run_fake_publish(edit_during_push=True)


if __name__ == "__main__":
    unittest.main()
