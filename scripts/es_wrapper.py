#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import locale
import subprocess
import sys
from pathlib import Path
from typing import Iterable


RESULT_LIMIT_FLAGS = {
    '-n',
    '-max-results',
}

OFFSET_FLAGS = {
    '-offset',
}


def candidate_encodings() -> list[str]:
    seen: list[str] = []

    def add(name: str | None) -> None:
        if not name:
            return
        key = name.lower()
        if key not in seen:
            seen.append(key)

    add('utf-8')
    add(locale.getpreferredencoding(False))
    add(getattr(sys.stdout, 'encoding', None))
    add('gbk')
    add('mbcs')
    add('utf-16-le')
    add('utf-16')
    return seen


def split_lines(raw: bytes) -> list[bytes]:
    raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    parts = [line for line in raw.split(b'\n') if line]
    return parts


def score_text(text: str) -> tuple[int, int]:
    replacement = text.count('\ufffd')
    mojibake_markers = sum(text.count(ch) for ch in ('�', '锟', '鈩', '銆', '鍙'))
    return (replacement + mojibake_markers, len(text))


def decode_line(raw_line: bytes) -> tuple[str, str]:
    best_text = ''
    best_encoding = 'utf-8'
    best_score = (10**9, 10**9)

    for encoding in candidate_encodings():
        try:
            text = raw_line.decode(encoding)
        except UnicodeDecodeError:
            continue
        score = score_text(text)
        if score < best_score:
            best_text = text
            best_encoding = encoding
            best_score = score
            if score[0] == 0:
                break

    if not best_text:
        best_text = raw_line.decode('utf-8', errors='replace')
        best_encoding = 'utf-8-replace'

    return best_text, best_encoding


def decode_output(raw: bytes) -> tuple[list[dict[str, str]], str]:
    entries: list[dict[str, str]] = []
    for raw_line in split_lines(raw):
        text, encoding = decode_line(raw_line)
        entries.append(
            {
                'path': text,
                'encoding': encoding,
                'path_unicode_escape': text.encode('unicode_escape').decode('ascii'),
            }
        )
    text = '\n'.join(item['path'] for item in entries)
    return entries, text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run Everything es.exe with raw-byte decoding and UTF-8-safe output.'
    )
    parser.add_argument('--es-path', default=None, help='Absolute path to es.exe')
    parser.add_argument(
        '--format',
        choices=('text', 'json', 'json-pretty'),
        default='text',
        help='Output format for decoded results.',
    )
    parser.add_argument(
        '--output-limit',
        type=int,
        default=20,
        help='Maximum number of decoded result rows to print. Use -1 for no wrapper-side limit.',
    )
    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help='Result offset to inject when es.exe args do not already contain -offset.',
    )
    parser.add_argument('es_args', nargs=argparse.REMAINDER, help='Arguments passed through to es.exe')
    return parser


def resolve_es_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return Path(__file__).resolve().parents[1] / 'bin' / 'es.exe'


def apply_output_limit(entries: list[dict[str, str]], limit: int) -> tuple[list[dict[str, str]], int]:
    total = len(entries)
    if limit < 0:
        return entries, total
    return entries[:limit], total


def has_flag(es_args: list[str], flags: set[str]) -> bool:
    for arg in es_args:
        if arg in flags:
            return True
        if any(arg.startswith(flag + '=') for flag in flags):
            return True
    return False


def has_result_limit(es_args: list[str]) -> bool:
    return has_flag(es_args, RESULT_LIMIT_FLAGS)


def has_offset(es_args: list[str]) -> bool:
    return has_flag(es_args, OFFSET_FLAGS)


def inject_result_limit(es_args: list[str], output_limit: int) -> tuple[list[str], bool]:
    if output_limit < 0 or has_result_limit(es_args):
        return es_args, False
    return [*es_args, '-max-results', str(output_limit)], True


def inject_offset(es_args: list[str], offset: int) -> tuple[list[str], bool]:
    if offset <= 0 or has_offset(es_args):
        return es_args, False
    return [*es_args, '-offset', str(offset)], True


def extract_effective_offset(es_args: list[str], fallback: int) -> int:
    for index, arg in enumerate(es_args):
        if arg == '-offset' and index + 1 < len(es_args):
            try:
                return int(es_args[index + 1])
            except ValueError:
                return fallback
        if arg.startswith('-offset='):
            try:
                return int(arg.split('=', 1)[1])
            except ValueError:
                return fallback
    return fallback


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    es_args = list(args.es_args)
    if es_args and es_args[0] == '--':
        es_args = es_args[1:]

    es_path = resolve_es_path(args.es_path)
    if not es_path.exists():
        parser.error(f'es.exe not found: {es_path}')

    effective_es_args, injected_limit = inject_result_limit(es_args, args.output_limit)
    effective_es_args, injected_offset = inject_offset(effective_es_args, args.offset)

    proc = subprocess.run(
        [str(es_path), *effective_es_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    effective_offset = extract_effective_offset(effective_es_args, args.offset)

    decoded_entries, decoded_text = decode_output(proc.stdout)
    stderr_entries, decoded_stderr = decode_output(proc.stderr)
    limited_entries, total_results = apply_output_limit(decoded_entries, args.output_limit)
    limited_text = '\n'.join(item['path'] for item in limited_entries)

    payload = {
        'command': [str(es_path), *effective_es_args],
        'exit_code': proc.returncode,
        'results': limited_entries,
        'stderr': stderr_entries,
        'result_count': total_results,
        'returned_count': len(limited_entries),
        'output_limited': args.output_limit >= 0 and total_results > len(limited_entries),
        'search_limited': injected_limit,
        'offset_injected': injected_offset,
        'output_limit': args.output_limit,
        'offset': effective_offset,
        'next_offset': (effective_offset + len(limited_entries)) if limited_entries else effective_offset,
    }

    if args.format == 'json':
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    elif args.format == 'json-pretty':
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if limited_text:
            sys.stdout.write(limited_text)
            if not limited_text.endswith('\n'):
                sys.stdout.write('\n')

    if proc.returncode != 0 and decoded_stderr:
        sys.stderr.write(decoded_stderr)
        if not decoded_stderr.endswith('\n'):
            sys.stderr.write('\n')

    return proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
