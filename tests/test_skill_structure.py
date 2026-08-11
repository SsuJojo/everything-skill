import hashlib
import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_runtime_text_has_no_legacy_hardcodes(self):
        forbidden = (
            'OpenClaw',
            '.openclaw',
            'WorkspaceRoot',
            'skills\\everything',
            'voidtools/Everything',
            'C:\\Users\\SsuJo',
        )
        text_files = [
            REPOSITORY_ROOT / 'SKILL.md',
            REPOSITORY_ROOT / 'README.md',
            *sorted(path for path in (REPOSITORY_ROOT / 'scripts').glob('*') if path.is_file()),
            *sorted((REPOSITORY_ROOT / 'references').glob('*.md')),
        ]
        for path in text_files:
            text = path.read_text(encoding='utf-8')
            for value in forbidden:
                self.assertNotIn(value, text, f'{path} contains {value}')

    def test_skill_markdown_relative_links_exist(self):
        text = (REPOSITORY_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        links = re.findall(r'\[[^]]+\]\(([^)]+)\)', text)
        relative_links = [link for link in links if '://' not in link and not link.startswith('#')]
        self.assertTrue(relative_links)
        for link in relative_links:
            self.assertTrue((REPOSITORY_ROOT / link).is_file(), f'Missing link target: {link}')

    def test_manifest_matches_bundled_es(self):
        manifest = json.loads(
            (REPOSITORY_ROOT / 'bin' / 'es.manifest.json').read_text(encoding='utf-8')
        )
        binary = REPOSITORY_ROOT / 'bin' / 'es.exe'
        digest = hashlib.sha256(binary.read_bytes()).hexdigest().upper()
        self.assertEqual(manifest['version'], '1.1.0.37')
        self.assertEqual(manifest['architecture'], 'x64')
        self.assertEqual(manifest['sha256'], digest)
        self.assertEqual(manifest['upstream_repository'], 'https://github.com/voidtools/ES')

    def test_bundled_es_is_x64_pe(self):
        data = (REPOSITORY_ROOT / 'bin' / 'es.exe').read_bytes()
        pe_offset = int.from_bytes(data[0x3C:0x40], 'little')
        self.assertEqual(data[:2], b'MZ')
        self.assertEqual(data[pe_offset:pe_offset + 4], b'PE\0\0')
        self.assertEqual(int.from_bytes(data[pe_offset + 4:pe_offset + 6], 'little'), 0x8664)


if __name__ == '__main__':
    unittest.main()
