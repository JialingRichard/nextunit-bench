"""Offline tests of the raw-data tools: unpacking, nested extraction, hash checks, prepared-data verification."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from nextunit.data import download


def zip_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buffer.getvalue()


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='nextunit-data-test-'))

    def test_check_size_and_hashes(self):
        path = self.root / 'f.bin'
        path.write_bytes(b'abc')
        self.assertTrue(download.check(path, {'bytes': 3, 'md5': hashlib.md5(b'abc').hexdigest()}))
        self.assertFalse(download.check(path, {'bytes': 4}))
        self.assertFalse(download.check(path, {'sha256': '0' * 64}))

    def test_unpack_keeps_layout(self):
        archive = self.root / 'a.zip'
        archive.write_bytes(zip_bytes({'DS/data/x.txt': b'1', 'DS/data/y.txt': b'2'}))
        download._unpack(archive, self.root / 'raw')
        self.assertEqual((self.root / 'raw/DS/data/y.txt').read_bytes(), b'2')

    def test_nested_extract_rules(self):
        inner2 = zip_bytes({'Test_set/B1/acc_1.csv': b'a', 'Test_set/B1/temp_1.csv': b't'})
        inner1 = zip_bytes({'Test_set.zip': inner2, 'readme.txt': b'r', 'train_FD004.txt': b'x'})
        outer = self.root / 'outer.zip'
        outer.write_bytes(zip_bytes({'pkg/inner.zip': inner1}))
        raw = self.root / 'raw'
        download._extract(outer, raw, [
            {'from': ['pkg/inner.zip'], 'member': 'train_FD004.txt', 'to': 'X/train/train_FD004.txt'},
            {'from': ['pkg/inner.zip', 'Test_set.zip'], 'prefix': 'Test_set/', 'pattern': '*/acc_*.csv', 'to': 'X/test/'},
        ], self.root)
        self.assertEqual((raw / 'X/train/train_FD004.txt').read_bytes(), b'x')
        self.assertEqual((raw / 'X/test/B1/acc_1.csv').read_bytes(), b'a')
        self.assertFalse((raw / 'X/test/B1/temp_1.csv').exists())

    def test_sources_cover_all_datasets(self):
        from nextunit import definition
        sources = download.sources()
        self.assertEqual(sorted(sources), list(definition.datasets()))
        for name, entry in sources.items():
            self.assertTrue(entry['routes'], name)
            for route in entry['routes']:
                self.assertTrue(route.get('manual') or route['files'], (name, route['name']))


if __name__ == '__main__':
    unittest.main()
