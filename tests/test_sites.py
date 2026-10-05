import contextlib
import copy
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

spec = importlib.util.spec_from_file_location("sites", Path(__file__).resolve().parents[1] / "scripts/sites.py")
sites = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sites)


class SitesTest(unittest.TestCase):
    def setUp(self):
        self.data = {"categories": [{"name": "数据工具", "sites": [
            {"name": "Example", "description": "", "url": "https://example.com/"}
        ]}]}

    def test_unsafe_url_rejected(self):
        for url in ("javascript:alert(1)", "https://user:secret@example.com", "example.com", "https://example.com/a b"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                sites.url_key(url)

    def test_duplicate_url_detected(self):
        self.data["categories"][0]["sites"].append({"name": "Alias", "url": "https://EXAMPLE.com"})
        count, warnings = sites.validate(self.data)
        self.assertEqual(count, 2)
        self.assertTrue(any("重复网址" in warning for warning in warnings))

    def test_yaml_duplicate_field_rejected(self):
        with self.assertRaises(ValueError):
            yaml.load("name: one\nname: two\n", Loader=sites.UniqueLoader)

    def test_add_round_trip_and_duplicate_no_write(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "sites.yml"
            data_path.write_text(yaml.safe_dump(self.data), encoding="utf-8")
            argv = ["sites.py", "add", "--category", "数据工具", "--name", "测试: '引号'", "--url", "https://example.org/?a=1&b=2", "--description", "多行\n描述"]
            with patch.object(sites, "DATA", data_path), patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
                sites.main()
                added = sites.read(data_path)["categories"][0]["sites"][-1]
                self.assertEqual(added["description"], "多行\n描述")
                self.assertEqual(added["url"], "https://example.org/?a=1&b=2")
                before = data_path.read_bytes()
                with self.assertRaises(ValueError):
                    sites.main()
                self.assertEqual(data_path.read_bytes(), before)

    def test_duplicate_category_rejected(self):
        self.data["categories"].append(copy.deepcopy(self.data["categories"][0]))
        with self.assertRaises(ValueError):
            sites.validate(self.data)


if __name__ == "__main__":
    unittest.main()
