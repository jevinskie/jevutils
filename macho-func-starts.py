#!/usr/bin/env python2

import sys

import lief

binary = lief.parse(sys.argv[1])

assert binary.format == lief.EXE_FORMATS.MACHO

funcs = binary.function_starts.functions

if binary.abstract.header.is_32:
	fmt_str = '{:08x}'
else:
	fmt_str = '{:016x}'

for func in funcs:
	print(fmt_str.format(int(func)))
