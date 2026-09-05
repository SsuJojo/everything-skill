import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter_declares_everything(self):
        text = (REPOSITORY_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertRegex(text, r'\A---\nname: everything\ndescription: .+\n---\n')

    def test_runtime_text_has_no_machine_specific_paths(self):
        text_files = [
            REPOSITORY_ROOT / 'SKILL.md',
            REPOSITORY_ROOT / 'README.md',
            REPOSITORY_ROOT / 'scripts' / 'ensure-everything-tools.ps1',
            REPOSITORY_ROOT / 'scripts' / 'es_wrapper.py',
        ]
        forbidden = ('WorkspaceRoot', '.openclaw', 'C:\\Users\\SsuJo_')
        for path in text_files:
            text = path.read_text(encoding='utf-8')
            for value in forbidden:
                self.assertNotIn(value, text, f'{path} contains {value}')

    def test_skill_links_are_relative_and_exist(self):
        text = (REPOSITORY_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        text = text.replace('`<skill-root>\\scripts\\ensure-everything-tools.ps1`', '')
        links = re.findall(r'`(references/[^`]+\.md)`', text)
        self.assertEqual(set(links), {'references/es-cli.md', 'references/everything-options.md'})
        for link in links:
            self.assertTrue((REPOSITORY_ROOT / link).is_file(), f'Missing link target: {link}')

    def test_ci_covers_python_and_both_powershell_hosts(self):
        text = (REPOSITORY_ROOT / '.github' / 'workflows' / 'ci.yml').read_text(
            encoding='utf-8'
        )
        self.assertIn("python-version: '3.10'", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn('shell: powershell', text)
        self.assertIn('shell: pwsh', text)


if __name__ == '__main__':
    unittest.main()
