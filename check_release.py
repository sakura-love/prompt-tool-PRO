#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

path = r'e:\AIwork\Promptool\BAK\prompt-tool-PRO\release'
files = []
total_size = 0

for root, dirs, filenames in os.walk(path):
    for f in filenames:
        fp = os.path.join(root, f)
        size = os.path.getsize(fp)
        total_size += size
        rel_path = os.path.relpath(fp, path)
        files.append((rel_path, size))

print('Release Package Contents:')
print('=' * 60)
for f, s in sorted(files):
    print(f'{f:45} {s:,} bytes')
print('=' * 60)
print(f'Total: {len(files)} files, {total_size:,} bytes ({total_size/1024/1024:.2f} MB)')
print('=' * 60)
