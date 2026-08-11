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

    def test_runtime_docs_default_to_windows_powershell(self):
        docs = [
            REPOSITORY_ROOT / 'SKILL.md',
            REPOSITORY_ROOT / 'README.md',
            *sorted((REPOSITORY_ROOT / 'references').glob('*.md')),
        ]
        for path in docs:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('pwsh ', text, f'{path} requires PowerShell 7')

    def test_readme_agent_install_prompt_is_safe_and_complete(self):
        text = (REPOSITORY_ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('https://github.com/SsuJojo/everything-skill.git', text)
        self.assertIn('最终目录名设为 `everything`', text)
        self.assertIn('仅清理克隆得到的安装副本', text)
        for removable in (
            '`.git/`',
            '`.github/`',
            '`.gitattributes`',
            '`.gitignore`',
            '`tests/`',
            '`README.md`',
        ):
            self.assertIn(removable, text)
        self.assertIn('`SKILL.md`、`scripts/`、`bin/`、`references/`、`licenses/`', text)
        self.assertIn('不要删除其他文件', text)
        self.assertIn('在使用 `-AllowDownload` 修复前先征得用户同意', text)
        self.assertIn('不要自动安装 Everything 主程序', text)

    def test_ci_covers_powershell_5_and_7(self):
        text = (REPOSITORY_ROOT / '.github' / 'workflows' / 'ci.yml').read_text(
            encoding='utf-8'
        )
        self.assertIn("python-version: '3.10'", text)
        self.assertIn("python-version: '3.14'", text)
        self.assertIn('shell: powershell', text)
        self.assertIn('shell: pwsh', text)

    def test_skill_name_matches_optional_metadata(self):
        skill = (REPOSITORY_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        metadata = (REPOSITORY_ROOT / 'agents' / 'openai.yaml').read_text(encoding='utf-8')
        self.assertIn('\nname: everything\n', skill)
        self.assertIn('$everything', metadata)

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
