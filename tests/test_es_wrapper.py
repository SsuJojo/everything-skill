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
    def test_default_es_path_is_relative_to_wrapper(self):
        expected = MODULE_PATH.parents[1] / 'bin' / 'es.exe'
        self.assertEqual(es_wrapper.resolve_es_path(None), expected)

    def test_argv_is_first_and_not_duplicated(self):
        self.assertEqual(
            es_wrapper.ensure_argv(['query', '-argv', '-ARGV']),
            ['-argv', 'query'],
        )

    def test_candidate_encoding_order_is_deterministic(self):
        with mock.patch.object(es_wrapper.locale, 'getpreferredencoding', return_value='cp1252'):
            self.assertEqual(
                es_wrapper.candidate_encodings(),
                ['utf-8', 'cp1252', 'mbcs', 'gbk'],
            )

    def test_preferred_cp1252_is_not_guessed_as_gbk(self):
        raw = 'C:\\docs\\éé.txt'.encode('cp1252')
        with mock.patch.object(es_wrapper.locale, 'getpreferredencoding', return_value='cp1252'):
            entries, text = es_wrapper.decode_output(raw)
        self.assertEqual(text, 'C:\\docs\\éé.txt')
        self.assertEqual(entries[0]['encoding'], 'cp1252')

    def test_gbk_fallback_decodes_chinese_path(self):
        raw = 'C:\\资料\\简历.pdf'.encode('gbk')
        with mock.patch.object(
            es_wrapper, 'candidate_encodings', return_value=['utf-8', 'ascii', 'gbk']
        ):
            entries, text = es_wrapper.decode_output(raw)
        self.assertEqual(text, 'C:\\资料\\简历.pdf')
        self.assertEqual(entries[0]['encoding'], 'gbk')

    def test_final_decoder_replaces_invalid_bytes(self):
        with mock.patch.object(
            es_wrapper, 'candidate_encodings', return_value=['utf-8', 'ascii']
        ):
            text, encoding = es_wrapper.decode_line(b'\xff')
        self.assertEqual(text, '\ufffd')
        self.assertEqual(encoding, 'utf-8-replace')

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
        self.assertEqual(command[1], '-argv')
        self.assertEqual(command[-4:], ['-max-results', '2', '-offset', '10'])


if __name__ == '__main__':
    unittest.main()
