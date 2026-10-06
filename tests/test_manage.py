import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import manage


class ManageTest(unittest.TestCase):
    def setUp(self):
        self.site = {"name": "Example", "description": "", "url": "https://example.com/"}
        self.data = {"categories": [{"name": "常用", "sites": [self.site]}]}

    def test_add_new_category_without_mutating_source(self):
        original = copy.deepcopy(self.data)
        new = {"name": "中文 & quote", "url": "https://example.org/?a=1&b=2", "description": ""}
        changed = manage.change(self.data, None, "新分类", new)
        self.assertEqual(changed["categories"][1]["sites"], [new])
        self.assertEqual(self.data, original)

    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):
            manage.change(self.data, None, "常用", self.site)

    def test_edit_move_delete(self):
        edited = dict(self.site, name="新名称", url="https://example.org/")
        result = manage.change(self.data, (0, 0), "分类2", edited)
        self.assertEqual(result["categories"][0]["sites"], [])
        self.assertEqual(result["categories"][1]["sites"], [edited])
        result = manage.change(result, (1, 0))
        self.assertEqual(result["categories"][1]["sites"], [])

    def test_reject_invalid_url(self):
        with self.assertRaises(ValueError):
            manage.change(self.data, (0, 0), "常用", dict(self.site, url="javascript:alert(1)"))

    def test_save_backup_and_refuse_stale_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sites.yml"
            original = yaml.safe_dump(self.data).encode()
            path.write_bytes(original)
            with patch.object(manage.sites, "ROOT", root), patch.object(manage.sites, "DATA", path):
                changed = manage.change(self.data, (0, 0), "常用", dict(self.site, name="new"))
                manage.save(changed, original)
                backups = list((root / ".local-publish").glob("*-sites.yml"))
                self.assertEqual(backups[0].read_bytes(), original)
                self.assertEqual(yaml.safe_load(path.read_text()), changed)
                with self.assertRaises(ValueError):
                    manage.save(self.data, original)
                self.assertFalse((root / ".local-publish/running.lock").exists())


if __name__ == "__main__":
    unittest.main()
