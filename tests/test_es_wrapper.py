import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'es_wrapper.py'
SPEC = importlib.util.spec_from_file_location('es_wrapper', MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
es_wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(es_wrapper)


class WrapperFunctionTests(unittest.TestCase):
    def test_wrapper_stdio_is_configured_as_utf8(self):
        stdout = mock.Mock()
        stderr = mock.Mock()
        with mock.patch.object(es_wrapper.sys, 'stdout', stdout), mock.patch.object(
            es_wrapper.sys, 'stderr', stderr
        ):
            es_wrapper.configure_utf8_stdio()
        stdout.reconfigure.assert_called_once_with(encoding='utf-8', errors='strict')
        stderr.reconfigure.assert_called_once_with(encoding='utf-8', errors='strict')

    def test_default_es_path_is_relative_to_wrapper(self):
        expected = MODULE_PATH.parents[1] / 'bin' / 'es.exe'
        self.assertEqual(es_wrapper.resolve_es_path(None), expected)

    def test_argv_and_utf8_code_page_are_first_and_not_duplicated(self):
        self.assertEqual(
            es_wrapper.normalize_core_flags(['query', '-argv', '-ARGV']),
            ['-argv', '-cp', '65001', 'query'],
        )

    def test_caller_code_page_options_are_replaced(self):
        cases = (
            ['-cp', '936', 'query'],
            ['-cp=936', 'query'],
            ['-code-page', '936', 'query'],
            ['-CODEPAGE=936', 'query'],
            ['/cp', '936', 'query'],
            ['/codepage=936', 'query'],
        )
        for arguments in cases:
            self.assertEqual(
                es_wrapper.normalize_core_flags(arguments),
                ['-argv', '-cp', '65001', 'query'],
            )

    def test_utf8_output_decodes_chinese_path(self):
        raw = 'C:\\资料\\简历.pdf'.encode('utf-8')
        entries, text = es_wrapper.decode_output(raw)
        self.assertEqual(text, 'C:\\资料\\简历.pdf')
        self.assertNotIn('encoding', entries[0])

    def test_invalid_utf8_fails_explicitly(self):
        with self.assertRaises(UnicodeDecodeError):
            es_wrapper.decode_output(b'\xff')

    def test_limit_and_offset_injection_are_exact(self):
        arguments, limit_injected = es_wrapper.inject_result_limit(['-argv', 'query'], 20)
        arguments, offset_injected = es_wrapper.inject_offset(arguments, 40)
        self.assertTrue(limit_injected)
        self.assertTrue(offset_injected)
        self.assertEqual(arguments[-4:], ['-max-results', '20', '-offset', '40'])

    def test_existing_es_limits_and_offsets_are_preserved(self):
        arguments = ['-argv', '-n', '5', '-offset=10', 'query']
        self.assertFalse(es_wrapper.inject_result_limit(arguments, 20)[1])
        self.assertFalse(es_wrapper.inject_offset(arguments, 30)[1])


class WrapperMainTests(unittest.TestCase):
    def run_main(self, argv, completed_process):
        output = io.StringIO()
        with (
            mock.patch.object(
                es_wrapper, 'resolve_es_path', return_value=Path('C:/skill/bin/es.exe')
            ),
            mock.patch.object(Path, 'is_file', return_value=True),
            mock.patch.object(es_wrapper.subprocess, 'run', return_value=completed_process) as run,
            redirect_stdout(output),
        ):
            return_code = es_wrapper.main(argv)
        return return_code, json.loads(output.getvalue()), run.call_args.args[0]

    def test_json_preserves_native_exit_code_and_paging(self):
        process = subprocess.CompletedProcess([], 8, stdout=b'a\r\nb\r\n', stderr=b'')
        code, payload, command = self.run_main(
            ['--format', 'json', '--output-limit', '2', '--offset', '10', '--', 'query'],
            process,
        )
        self.assertEqual(code, 8)
        self.assertEqual(payload['exit_code'], 8)
        self.assertEqual([item['path'] for item in payload['results']], ['a', 'b'])
        self.assertEqual(payload['returned_count'], 2)
        self.assertEqual(payload['next_offset'], 12)
        self.assertNotIn('output_limited', payload)
        self.assertEqual(command[1:4], ['-argv', '-cp', '65001'])
        self.assertEqual(command[-4:], ['-max-results', '2', '-offset', '10'])

    def test_full_page_advances_and_short_or_empty_pages_stop_naturally(self):
        full_output = b'\n'.join(f'item-{index}'.encode() for index in range(20)) + b'\n'
        full = subprocess.CompletedProcess([], 0, stdout=full_output, stderr=b'')
        _, full_payload, _ = self.run_main(
            ['--format', 'json', '--output-limit', '20', '--', 'query'], full
        )
        self.assertEqual(full_payload['returned_count'], 20)
        self.assertEqual(full_payload['next_offset'], 20)

        short = subprocess.CompletedProcess([], 0, stdout=b'one\ntwo\n', stderr=b'')
        _, short_payload, _ = self.run_main(
            ['--format', 'json', '--output-limit', '20', '--offset', '20', '--', 'query'],
            short,
        )
        self.assertEqual(short_payload['returned_count'], 2)
        self.assertEqual(short_payload['next_offset'], 22)

        empty = subprocess.CompletedProcess([], 0, stdout=b'', stderr=b'')
        _, empty_payload, _ = self.run_main(
            ['--format', 'json', '--output-limit', '20', '--offset', '40', '--', 'query'],
            empty,
        )
        self.assertEqual(empty_payload['returned_count'], 0)
        self.assertEqual(empty_payload['next_offset'], 40)


if __name__ == '__main__':
    unittest.main()
