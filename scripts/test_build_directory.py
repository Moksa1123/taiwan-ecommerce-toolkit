#!/usr/bin/env python3
"""
directory-plugin/ 的自我測試：要和原始檔同步、只放官方目錄允許的檔、不含禁用字詞。

用法:
    python3 scripts/test_build_directory.py
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as bd  # noqa: E402


class DirectoryPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.want = bd.build()
        cls.have = bd.existing()

    def test_in_sync(self):
        self.assertEqual(bd.differences(self.want, self.have), [],
                         'directory-plugin/ 與原始檔不同步：跑 python3 scripts/build_directory.py')

    def test_detects_stale_and_extra(self):
        have = dict(self.want)
        key = next(k for k in have if k.endswith('SKILL.md'))
        have[key] = have[key] + b'hand edit'
        have['skills/taiwan-payment/scripts/search.py'] = b''
        diff = bd.differences(self.want, have)
        self.assertTrue(any(d.startswith('過期') for d in diff))
        self.assertTrue(any(d.startswith('多出') for d in diff))

    def test_only_allowed_files(self):
        for rel, data in self.want.items():
            self.assertIn(Path(rel).suffix, bd.ALLOWED, rel)
            if not rel.endswith('.png'):
                self.assertLessEqual(len(data), bd.MAX_BYTES, rel)
                self.assertFalse(data.startswith(b'#!'), rel)
        self.assertLess(len(self.want), 512)
        for name in ('package.json', '.npmignore', 'requirements.txt'):
            self.assertFalse(any(Path(k).name == name for k in self.want), name)

    @staticmethod
    def bad(text):
        low = text.lower()
        return (bd.FORBIDDEN.search(text) or bd.FORBIDDEN_CS.search(text)
                or any(s.lower() in low for s in bd.SECRETS))

    def test_no_forbidden_words(self):
        for rel, data in self.want.items():
            if rel.endswith('.png'):
                continue
            for i, line in enumerate(data.decode('utf-8').splitlines(), 1):
                self.assertFalse(self.bad(line), f'{rel}:{i}')

    def test_forbidden_pattern_catches(self):
        for bad in ('ssh user@host', 'cat .env', 'process.env.ECPAY_HASH_KEY', "os.environ['KEY']",
                    "getenv('KEY')", 'password', 'id_rsa', 'key.pem', 'YOUR_HASH_KEY', 'wp-config.php',
                    'config.ECPAY_HASH_KEY', "config['KEY']", 'echo $SHOPLINE_API_KEY', '${ECPAY_HASH_KEY}',
                    'credentials = base64', 'HashKey pwFHCqoQZGmho4w6', 'hashkey%3dpwfhcqoqzgmho4w6'):
            self.assertTrue(self.bad(bad), bad)
        for ok in ('$merchantId', 'this.config.hashKey', '${MerchantID}', 'not real credentials'):
            self.assertFalse(self.bad(ok), ok)

    def test_rewrites(self):
        ph = bd.SECRET_PLACEHOLDER
        cases = {
            'hashKey: process.env.NEWEBPAY_HASH_KEY!,': "hashKey: '<NEWEBPAY_HASH_KEY>',",
            "apiUrl: process.env.NODE_ENV === 'production'": 'apiUrl: isProduction',
            'url: `${process.env.NEXT_PUBLIC_BASE_URL}/api/cb`': 'url: `<NEXT_PUBLIC_BASE_URL>/api/cb`',
            "key = os.environ['ECPAY_HASH_KEY']": "key = '<ECPAY_HASH_KEY>'",
            "key = os.environ.get('ECPAY_HASH_KEY', '')": "key = '<ECPAY_HASH_KEY>'",
            "$k = getenv('SHOPLINE_SIGN_KEY');": "$k = '<SHOPLINE_SIGN_KEY>';",
            'echo $SHOPLINE_API_KEY': 'echo <SHOPLINE_API_KEY>',
            'credentials = b64(x)': 'basic_auth = b64(x)',
            '`.env` 檔': '設定檔',
            "hashKey: 'YOUR_HASH_KEY',": "hashKey: '<HASH_KEY>',",
            'TransData(string company, string password)': 'TransData(string company, string <帳密欄位>)',
            '密碼 `test1234`': '密碼 `<官方公開測試值>`',
            "hashKey: 'pwFHCqoQZGmho4w6',": f"hashKey: '{ph}',",
            'HashKey%3dpwfhcqoqzgmho4w6': f'HashKey%3d{ph}',
            "$merchantId = $row['id'];": "$merchantId = $row['id'];",
        }
        for src, want in cases.items():
            self.assertEqual(bd.credential_free(src), want, src)
            self.assertFalse(self.bad(bd.credential_free(src)), src)

    def test_frontmatter_quoted(self):
        for s in bd.SKILLS:
            text = self.want[f'skills/taiwan-{s}/SKILL.md'].decode('utf-8')
            line = next(l for l in text.splitlines() if l.startswith('description: '))
            value = line[len('description: '):]
            self.assertTrue(value.startswith('"') and value.endswith('"'), s)
            self.assertIn('Directory edition', json.loads(value))

    def test_plugin_json(self):
        pj = json.loads(self.want['.claude-plugin/plugin.json'])
        self.assertEqual(pj['skills'], [f'./skills/taiwan-{s}' for s in bd.SKILLS])
        self.assertIn('unofficial', pj['displayName'].lower())
        self.assertNotIn('userConfig', pj)

    def test_skill_md_points_to_full_edition(self):
        for s in bd.SKILLS:
            text = self.want[f'skills/taiwan-{s}/SKILL.md'].decode('utf-8')
            self.assertIn(f'npx taiwan-{s}-skill@{bd.pkg_version(s)} init', text)
            self.assertIn('Directory edition', text)
            self.assertNotIn('{{', text)

    def test_data_complete(self):
        """JSON 筆數合計要等於原始 CSV 筆數（拆檔不能掉資料）。"""
        for s in bd.SKILLS:
            csv_total = sum(len(bd.csv_rows(p)) for p in (bd.ROOT / f'taiwan-{s}' / 'data').glob('*.csv'))
            json_total = sum(len(json.loads(v)['rows']) for k, v in self.want.items()
                             if k.startswith(f'skills/taiwan-{s}/data/'))
            self.assertEqual(csv_total, json_total, s)


if __name__ == '__main__':
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, 'reconfigure'):
            s.reconfigure(encoding='utf-8', errors='replace')
    unittest.main(verbosity=1)
