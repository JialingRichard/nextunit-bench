"""python -m nextunit.data fetch DATASET --raw RAW_ROOT --downloads DIR [--route official|mirror]
   python -m nextunit.data verify-raw DATASET [DATASET ...] --raw RAW_ROOT
   python -m nextunit.data build DATASET --raw RAW_ROOT --prepared PREPARED_ROOT [--copy-raw]
   python -m nextunit.data verify DATASET [DATASET ...] --prepared PREPARED_ROOT"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import definition
from . import download, prepare


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.data')
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build', help="convert one dataset's raw files into prepared data")
    b.add_argument('dataset', choices=definition.datasets())
    b.add_argument('--raw', type=Path, required=True)
    b.add_argument('--prepared', type=Path, required=True)
    b.add_argument('--copy-raw', action='store_true', help='copy pass-through raw files instead of hard-linking them')
    f = sub.add_parser('fetch', help='download and lay out the raw files of one dataset')
    f.add_argument('dataset', choices=definition.datasets())
    f.add_argument('--raw', type=Path, required=True)
    f.add_argument('--downloads', type=Path, required=True)
    f.add_argument('--route', help='use only this route (e.g. mirror)')
    r = sub.add_parser('verify-raw', help='check the raw files a converter reads against the shipped checksums')
    r.add_argument('datasets', nargs='+', choices=definition.datasets())
    r.add_argument('--raw', type=Path, required=True)
    v = sub.add_parser('verify', help='check prepared data against the shipped checksums')
    v.add_argument('datasets', nargs='+', choices=definition.datasets())
    v.add_argument('--prepared', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'fetch':
        try:
            print(json.dumps({'dataset': args.dataset, 'route': download.acquire(args.dataset, args.raw, args.downloads, args.route)}))
        except download.DownloadError as error:
            print(str(error))
            return 2
        result = download.verify_raw(args.dataset, args.raw)
        print(json.dumps({k: (v[:5] if isinstance(v, list) else v) for k, v in result.items()}))
        return 0 if result['ok'] else 1
    if args.command == 'verify-raw':
        ok = True
        for dataset in args.datasets:
            result = download.verify_raw(dataset, args.raw)
            ok &= result['ok']
            print(json.dumps({k: (v[:5] if isinstance(v, list) else v) for k, v in result.items()}))
        return 0 if ok else 1
    if args.command == 'build':
        print(prepare.build(args.dataset, args.raw, args.prepared, link_raw=not args.copy_raw))
        return 0
    ok = True
    for dataset in args.datasets:
        result = prepare.verify(dataset, args.prepared)
        ok &= result['ok']
        print(json.dumps({k: (v[:5] if isinstance(v, list) else v) for k, v in result.items()}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
