import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import batch


class BatchTest(unittest.TestCase):
    def setUp(self):
        self.data = {"categories": [{"name": "常用", "sites": [
            {"name": "Keep", "url": "https://keep.example/", "description": ""},
            {"name": "Delete", "url": "https://delete.example/", "description": ""}
        ]}]}

    def test_exact_delete_preserves_other_site(self):
        result, _, changed = batch.plan(self.data, "删除|https://delete.example/")
        self.assertTrue(changed)
        self.assertEqual([s["name"] for s in result["categories"][0]["sites"]], ["Keep"])
        self.assertEqual(len(self.data["categories"][0]["sites"]), 2)

    def test_bad_later_line_leaves_original_unchanged(self):
        before = copy.deepcopy(self.data)
        with self.assertRaises(ValueError):
            batch.plan(self.data, "删除|https://delete.example/\n删除|delete.example")
        self.assertEqual(self.data, before)

    def test_modify_and_query(self):
        result, logs, _ = batch.plan(self.data, "修改|https://keep.example/||New||\n查询|New")
        self.assertEqual(result["categories"][0]["sites"][0]["name"], "New")
        self.assertTrue(any("查询" in message for message in logs))
        _, _, changed = batch.plan(self.data, "查询|Keep")
        self.assertFalse(changed)

    def test_retry_does_not_repeat_delete_or_import_old_inbox(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "sites.yml"
            inbox = root / "网站操作.txt"
            data.write_text(yaml.safe_dump(self.data))
            original = "删除|https://delete.example/"
            inbox.write_text(original)
            with patch.object(batch.sites, "ROOT", root), patch.object(batch.sites, "DATA", data), \
                 patch.object(batch.publish, "publish", side_effect=[ValueError("offline"), None]) as publish:
                with self.assertRaises(ValueError):
                    batch.main()
                self.assertEqual(inbox.read_text(), original)
                batch.main()
                self.assertEqual(len(yaml.safe_load(data.read_text())["categories"][0]["sites"]), 1)
                self.assertEqual(inbox.read_text(), batch.TEMPLATE)
                self.assertFalse((root / ".local-publish/batch-pending.json").exists())
                self.assertEqual(publish.call_args.kwargs, {"include_inbox": False})


if __name__ == "__main__":
    unittest.main()
