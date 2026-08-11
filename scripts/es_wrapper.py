#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import locale
import subprocess
import sys
from pathlib import Path
from typing import Iterable


RESULT_LIMIT_FLAGS = {'-n', '-max-results'}
OFFSET_FLAGS = {'-offset'}


def candidate_encodings() -> list[str]:
    """Return a small, deterministic decoder fallback list."""
    encodings: list[str] = []

    def add(name: str | None) -> None:
        if name and name.lower() not in {item.lower() for item in encodings}:
            encodings.append(name)

    add('utf-8')
    add(locale.getpreferredencoding(False))
    add('mbcs')
    add('gbk')
    return encodings


def split_lines(raw: bytes) -> list[bytes]:
    normalized = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return [line for line in normalized.split(b'\n') if line]


def decode_line(raw_line: bytes) -> tuple[str, str]:
    for encoding in candidate_encodings():
        try:
            return raw_line.decode(encoding), encoding
        except (LookupError, UnicodeDecodeError):
            continue
    return raw_line.decode('utf-8', errors='replace'), 'utf-8-replace'


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
    return entries, '\n'.join(item['path'] for item in entries)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run Everything es.exe with bounded, Unicode-safe output.'
    )
    parser.add_argument('--es-path', help='Path to es.exe (defaults to this Skill bundled copy).')
    parser.add_argument(
        '--format',
        choices=('text', 'json', 'json-pretty'),
        default='text',
        help='Output format for decoded stdout.',
    )
    parser.add_argument(
        '--output-limit',
        type=int,
        default=20,
        help='Maximum result rows. Use -1 for unrestricted output.',
    )
    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help='Result offset when ES arguments do not already include one.',
    )
    parser.add_argument('es_args', nargs=argparse.REMAINDER, help='Arguments passed to es.exe')
    return parser


def resolve_es_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return Path(__file__).resolve().parents[1] / 'bin' / 'es.exe'


def has_flag(es_args: list[str], flags: set[str]) -> bool:
    lowered_flags = {flag.lower() for flag in flags}
    for arg in es_args:
        lowered = arg.lower()
        if lowered in lowered_flags:
            return True
        if any(lowered.startswith(flag + '=') for flag in lowered_flags):
            return True
    return False


def ensure_argv(es_args: list[str]) -> list[str]:
    return ['-argv', *(arg for arg in es_args if arg.lower() != '-argv')]


def inject_result_limit(es_args: list[str], output_limit: int) -> tuple[list[str], bool]:
    if output_limit < 0 or has_flag(es_args, RESULT_LIMIT_FLAGS):
        return es_args, False
    return [*es_args, '-max-results', str(output_limit)], True


def inject_offset(es_args: list[str], offset: int) -> tuple[list[str], bool]:
    if offset <= 0 or has_flag(es_args, OFFSET_FLAGS):
        return es_args, False
    return [*es_args, '-offset', str(offset)], True


def extract_effective_offset(es_args: list[str], fallback: int) -> int:
    for index, arg in enumerate(es_args):
        lowered = arg.lower()
        if lowered == '-offset' and index + 1 < len(es_args):
            try:
                return int(es_args[index + 1])
            except ValueError:
                return fallback
        if lowered.startswith('-offset='):
            try:
                return int(arg.split('=', 1)[1])
            except ValueError:
                return fallback
    return fallback


def apply_output_limit(
    entries: list[dict[str, str]], limit: int
) -> tuple[list[dict[str, str]], int]:
    total = len(entries)
    if limit < 0:
        return entries, total
    return entries[:limit], total


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.output_limit < -1:
        parser.error('--output-limit must be -1 or greater')
    if args.offset < 0:
        parser.error('--offset must be zero or greater')

    es_args = list(args.es_args)
    if es_args and es_args[0] == '--':
        es_args = es_args[1:]

    es_path = resolve_es_path(args.es_path)
    if not es_path.is_file():
        parser.error(f'es.exe not found: {es_path}')

    effective_args = ensure_argv(es_args)
    effective_args, limit_injected = inject_result_limit(effective_args, args.output_limit)
    effective_args, offset_injected = inject_offset(effective_args, args.offset)

    try:
        process = subprocess.run(
            [str(es_path), *effective_args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        parser.error(f'failed to run es.exe: {exc}')

    entries, _ = decode_output(process.stdout)
    stderr_entries, decoded_stderr = decode_output(process.stderr)
    limited_entries, result_count = apply_output_limit(entries, args.output_limit)
    limited_text = '\n'.join(item['path'] for item in limited_entries)
    effective_offset = extract_effective_offset(effective_args, args.offset)

    payload = {
        'command': [str(es_path), *effective_args],
        'exit_code': process.returncode,
        'results': limited_entries,
        'stderr': stderr_entries,
        'result_count': result_count,
        'returned_count': len(limited_entries),
        'output_limited': args.output_limit >= 0 and result_count > len(limited_entries),
        'search_limited': limit_injected,
        'offset_injected': offset_injected,
        'output_limit': args.output_limit,
        'offset': effective_offset,
        'next_offset': effective_offset + len(limited_entries),
    }

    if args.format == 'json':
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    elif args.format == 'json-pretty':
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    elif limited_text:
        sys.stdout.write(limited_text + ('\n' if not limited_text.endswith('\n') else ''))

    if process.returncode != 0 and decoded_stderr:
        sys.stderr.write(decoded_stderr + ('\n' if not decoded_stderr.endswith('\n') else ''))
    return process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
