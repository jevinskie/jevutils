#!/usr/bin/env python3

import argparse
import functools
import math
import sys
import termios
from collections import defaultdict
from collections.abc import Callable
from string import printable, whitespace
from typing import Final, Self

import anytree
import attrs
from path import Path
from rich import print

_encoded_header_magic: Final[bytes] = b"ncFyP12 -+; return\n\x1a#{\n"


def num_non_zero_lsbytes(i: int) -> int:
    n = 0
    while i:
        i >>= 8
        n += 1
    return n


def auto_clear_cache_on_false(cache_clearing_methods, attribute_name, trigger_value=False):
    def class_decorator(cls):
        new_attribute = attrs.field(
            default=trigger_value,
            init=True,
            on_setattr=[
                clear_cache_if_false(cache_clearing_methods, attribute_name, trigger_value)
            ],
            repr=False,
        )
        setattr(cls, attribute_name, new_attribute)
        return cls

    def clear_cache_if_false(cache_clearing_methods, attribute_name, trigger_value):
        def setter(inst, attribute, value):
            if value == trigger_value:
                for method in cache_clearing_methods:
                    if hasattr(inst, method) and hasattr(getattr(inst, method), "clear_cache"):
                        getattr(getattr(inst, method), "clear_cache")(
                            inst
                        )  # Pass instance to clear_cache
            return value

        return setter

    return class_decorator


def conditional_method_cache(condition_attr):
    def decorator(func):
        cached_attr_name = f"_{func.__name__}_cache"

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, cached_attr_name):
                setattr(self, cached_attr_name, {})  # Set attribute dynamically if it doesn't exist

            cache = getattr(self, cached_attr_name)

            if getattr(self, condition_attr, False):
                if args in cache:
                    return cache[args]
                else:
                    result = func(self, *args, **kwargs)
                    cache[args] = result
                    return result
            else:
                return func(self, *args, **kwargs)

        def clear_cache(self):
            if hasattr(self, cached_attr_name):
                getattr(self, cached_attr_name).clear()

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator


@attrs.define(slots=False)
@functools.total_ordering
@auto_clear_cache_on_false(["__hash__"], "finalized")
class HuffmanNode(anytree.NodeMixin):
    weight: int = attrs.field()
    symbol: int | None = attrs.field(repr=lambda s: "None" if s is None else f"{s:#04x}")
    finalized: bool = attrs.field(default=False, repr=False)

    @property
    def left_child(self) -> Self | None:
        clen = len(self.children)
        if clen == 0:
            return None
        assert clen == 2
        return self.children[0]

    @property
    def right_child(self) -> Self | None:
        clen = len(self.children)
        if clen == 0:
            return None
        assert clen == 2
        return self.children[1]

    @property
    def left_and_right_child(self) -> tuple[Self, Self] | None:
        clen = len(self.children)
        if clen == 0:
            return None
        assert clen == 2
        return tuple(self.children)

    @left_and_right_child.setter
    def left_and_right_child(self, left_and_right: tuple[Self, Self] | None) -> None:
        if left_and_right is None:
            self.children = tuple()
            return
        self.children = left_and_right

    @functools.cache
    def get_symbol_encoding(self, symbol: int) -> list[bool]:
        assert not self.is_leaf and self.is_root
        assert 0 <= symbol <= 0xFF
        symbol_node = anytree.search.find_by_attr(self, symbol, name="symbol")
        assert isinstance(symbol_node, type(self))  # type hint
        go_right_path: list[bool] = []
        node = symbol_node
        while node.parent is not None:
            parent = node.parent
            assert isinstance(parent, type(self))  # type hint
            if parent.left_child is node:
                go_right_path.append(False)
            else:
                go_right_path.append(True)
            node = parent
        go_right_path.reverse()
        return go_right_path

    @functools.cache
    def get_symbol_nodes(self) -> list[Self]:
        assert not self.is_leaf and self.is_root
        symbol_nodes = list(anytree.search.findall(self, filter_=lambda n: n.is_leaf))
        assert isinstance(symbol_nodes, type([self]))  # type hint
        symbol_nodes.sort()
        return symbol_nodes

    @functools.cache
    def get_symbols(self) -> list[int]:
        assert not self.is_leaf and self.is_root
        symbol_nodes = self.get_symbol_nodes()
        res: list[int] = []
        for s in symbol_nodes:
            assert s.symbol is not None
            res.append(s.symbol)
        res.sort()
        return res

    @functools.cache
    def get_symbol(self, symbol: int) -> Self:
        assert not self.is_leaf and self.is_root
        symbol_node = anytree.search.find_by_attr(self, symbol, name="symbol")
        assert isinstance(symbol_node, type(self))  # type hint
        return symbol_node

    def __lt__(self, other) -> bool:
        if not isinstance(other, type(self)):
            raise NotImplementedError
        if self.weight < other.weight:
            return True
        elif self.weight > other.weight:
            return False
        if self.symbol is not None and other.symbol is not None:
            return self.symbol < other.symbol
        elif self.symbol is None and other.symbol is None:
            return False  # equal
        elif self.symbol is None and other.symbol is not None:
            return True
        elif self.symbol is not None and other.symbol is None:
            return False
        else:
            raise NotImplementedError

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            raise NotImplementedError
        if self.weight == other.weight:
            if self.symbol is None and other.symbol is None:
                return True
            elif self.symbol is not None and other.symbol is not None:
                return self.symbol == other.symbol
            else:
                return False
        else:
            return False

    @conditional_method_cache("finalized")
    def __hash__(self) -> int:
        hash_list = [self.weight, self.symbol]
        if not self.is_leaf:
            hash_list += [self.left_child, self.right_child]
        return hash(tuple(hash_list))


class Histogram(defaultdict):
    MAX_TERM_WIDTH: Final[int] = 1024
    FALLBACK_TERM_WIDTH: Final[int] = 80
    COUNT_NUM_DIGITS: Final[int] = 5

    def __init__(self):
        super().__init__(int)

    @staticmethod
    def get_bar_width(prefix_len: int) -> int:
        try:
            _, col = termios.tcgetwinsize(sys.stdin)
        except Exception:
            col = Histogram.FALLBACK_TERM_WIDTH
        col = min(col, Histogram.MAX_TERM_WIDTH)
        col = max(col - prefix_len, 0)
        return col

    @staticmethod
    def block_str(percentage: float, width: int = 80) -> str:
        full_width = width * 8
        num_blk = int(percentage * full_width)
        full_blks = num_blk // 8
        partial_blks = num_blk % 8
        return "█" * full_blks + ("", "▏", "▎", "▍", "▌", "▋", "▊", "▉")[partial_blks]

    def ascii_histogram(
        self,
        prefix_width: int | None = None,
        width: int | None = None,
        repf: Callable[[int], str] | None = None,
    ) -> str:
        res = ""
        # sort by byte value then frequency to get stable output
        sorted_self = dict(
            sorted(sorted(self.items(), key=lambda v: v[0]), key=lambda v: v[1], reverse=True)
        )
        max_num = next(iter(sorted_self.values()))
        max_key = max(sorted_self.keys())
        rep_len = 0
        if repf is not None:
            rep_len = len(repf(max_key)) + 1  # one surrounding space on left side
        if prefix_width is None:
            max_key_bytes = math.ceil(math.ceil(math.log2(max_key)) / 8)
            if max_key_bytes == 0:
                max_key_bytes = 1
            prefix_width = 2 * max_key_bytes + rep_len
        if width is None:
            width = self.get_bar_width(prefix_width + 2 + ByteHistogram.COUNT_NUM_DIGITS + 3)
        for m, n in sorted_self.items():
            rep = ""
            if repf is not None:
                rep = f" {repf(m)}"
            res += (
                f"{m:0{2 * max_key_bytes}x}{rep} [{n:{ByteHistogram.COUNT_NUM_DIGITS}d}]: "
                + self.block_str(n / max_num, width=width)
                + "\n"
            )
        return res


class ByteHistogram(Histogram):
    def __init__(self, include_zeros: bool = False):
        super().__init__()
        if include_zeros:
            for i in range(0x100):
                self[i] = 0

    def add_bytes(self, buf: bytes) -> None:
        for b in buf:
            self[b] += 1

    @staticmethod
    def byte_rep(b: int) -> str:
        c = chr(b)
        if c in printable:
            rep = f"'{c}'"
            if c in whitespace:
                rep = "' '"
        else:
            rep = "   "
        return rep

    def ascii_histogram(
        self,
        prefix_width: int | None = None,
        width: int | None = None,
        repf: Callable[[int], str] | None = None,
    ) -> str:
        assert all([0 <= b <= 0xFF for b in self.keys()])
        if repf is None:
            repf = self.byte_rep
        return super().ascii_histogram(prefix_width=prefix_width, width=width, repf=repf)


class HuffmanCoder:
    byte_hist: ByteHistogram | None
    byte_root: HuffmanNode | None
    symbol_hist: Histogram | None
    symbol_root: HuffmanNode | None

    def __init__(
        self,
        buf: bytes | None = None,
        byte_hist: ByteHistogram | None = None,
        symbol_hist: Histogram | None = None,
    ):
        if not any((buf, byte_hist, symbol_hist)):
            raise ValueError(
                "One of (but not both) buf or byte_hist or (byte_hist & symbol_hist) must not be None"
            )
        if all((buf, byte_hist)):
            raise ValueError("Both buf and byte_hist can't both be non-None")
        if buf is not None or byte_hist is not None:
            if buf is not None:
                self.byte_root, self.byte_hist = self.create_tree_from_bytes(buf)
            elif byte_hist is not None:
                self.byte_hist = byte_hist
                self.byte_root = self.create_tree_from_histogram(byte_hist)
        if symbol_hist is not None:
            self.symbol_hist = symbol_hist
            self.symbol_root = self.create_tree_from_histogram(symbol_hist)

    def create_tree_from_histogram(self, hist: Histogram) -> HuffmanNode:
        trees = [HuffmanNode(hist[b], b) for b in hist.keys()]
        num_leafs = len(trees)
        trees.sort()
        for i in range(num_leafs - 1):
            left, right = trees[i : i + 2]
            parent = HuffmanNode(left.weight + right.weight, None)
            parent.left_and_right_child = (left, right)
            trees[i + 1] = parent
            for j in range(i + 1, num_leafs - 1):
                if trees[j + 1].weight > trees[j].weight:
                    break
                trees[j : j + 2] = (trees[j + 1], trees[j])
        root_node = trees[-1]
        for n in anytree.iterators.preorderiter.PreOrderIter(root_node):
            n.finalized = True
        return root_node

    def create_tree_from_bytes(self, in_buf: bytes) -> tuple[HuffmanNode, ByteHistogram]:
        byte_hist = ByteHistogram()
        byte_hist.add_bytes(in_buf)
        return self.create_tree_from_histogram(byte_hist), byte_hist


def has_encoded_header_magic(buf: bytes) -> bool:
    try:
        return buf.index(_encoded_header_magic) == 0
    except ValueError:
        return False


def encode_header(in_buf: bytes) -> tuple[bytes, Histogram]:
    hdr = bytearray()
    hdr += _encoded_header_magic
    symbol_hist = Histogram()
    for i, ib in enumerate(in_buf):
        # we are supposed to have only one EoT, the one we generate
        if ib == 0x04:
            raise ValueError(
                f"Got End of Transmission (EoT a.k.a. 0x04) in input stream at byte {i}."
            )
        if ib == 0x0D:  # skip carriage returns
            continue
        symbol_hist[ib] += 1
    symbol_hist[0x04] += 1  # for the EoT we stick on the end
    for symbol_idx in range(0x100):
        if symbol_idx not in symbol_hist.keys():
            freq = 0
        else:
            freq = symbol_hist[symbol_idx]
        freq_enc_len = num_non_zero_lsbytes(freq)
        hdr.append(freq_enc_len)
        for i in range(freq_enc_len):
            # symbol freq goes out LSByte first
            hdr.append(freq & 0xFF)
            freq >>= 8
    return bytes(hdr), symbol_hist


def encode_data(in_buf: bytes, symbol_hist: Histogram) -> bytes:
    buf = bytearray()
    coder = HuffmanCoder(symbol_hist=symbol_hist)
    symbol_root = coder.symbol_root
    assert symbol_root is not None
    bit_counter = 0
    ob = 0
    in_buf += b"\x04"
    eot_idx = len(in_buf) - 1
    for i, ib in enumerate(in_buf):
        # we are supposed to have only one EoT, the one we generate
        if ib == 0x04 and i != eot_idx:
            raise ValueError(
                f"Got End of Transmission (EoT a.k.a. 0x04) in input stream at byte {i}."
            )
        if ib == 0x0D:  # skip carriage returns
            continue
        symbol_encoding = symbol_root.get_symbol_encoding(ib)
        for bit in symbol_encoding:
            ob = (bit << 7) | (ob >> 1)
            bit_counter += 1
            if bit_counter == 8:
                buf.append(ob)
                bit_counter = 0
                ob = 0
    if bit_counter != 0:
        buf.append(ob >> (8 - bit_counter))
        buf.append(bit_counter)
    else:
        buf.append(0x08)
    buf += b"}\n"
    return bytes(buf)


def decode_header(in_buf: bytes) -> tuple[int, int, ByteHistogram, Histogram]:
    first_newline_idx = in_buf.index(b"\n")
    second_newline_idx = in_buf.index(b"\n", first_newline_idx + 1)
    in_buf = in_buf[second_newline_idx + 1 :]
    byte_hist = ByteHistogram()
    symbol_hist = Histogram()
    buf_idx = 0
    decoded_len = 0
    for symbol_idx in range(0x100):
        num_symbol_freq_bytes = in_buf[buf_idx]
        buf_idx += 1
        symbol_freq = 0
        if num_symbol_freq_bytes:
            for i in range(num_symbol_freq_bytes):
                # symbol freq comes in LSByte first
                symbol_freq |= in_buf[buf_idx + i] << (i * 8)
            byte_hist[symbol_idx] = symbol_freq
            symbol_hist[symbol_idx] = symbol_freq
        else:
            pass
        buf_idx += num_symbol_freq_bytes
        if symbol_idx == 0x04:  # 1 EoT always added
            assert symbol_freq == 1
            decoded_len -= symbol_freq
        decoded_len += symbol_freq
    return second_newline_idx + 1 + buf_idx, decoded_len, byte_hist, symbol_hist


def decode_data(in_buf: bytes, coder: HuffmanCoder) -> bytes:
    out_buf = bytearray()
    byte_root = coder.byte_root
    assert byte_root is not None
    node = byte_root
    assert node is not None
    symbol_root = coder.symbol_root
    assert symbol_root is not None
    symbol_node = symbol_root
    assert symbol_node is not None
    symbol_len = 8
    got_eot = False
    # FIXME: account for b"}\n" at encoded EOF
    for i, symbol_code in enumerate(in_buf):
        for j in range(symbol_len):
            symbol_code_bit = bool(symbol_code & 1)
            if not symbol_code_bit:
                next_node = symbol_node.left_child
                assert next_node is not None
                symbol_node = next_node
            else:
                next_node = symbol_node.right_child
                assert next_node is not None
                symbol_node = next_node
            if symbol_node.is_leaf:
                assert symbol_node.symbol is not None and 0 <= symbol_node.symbol <= 0xFF
                if symbol_node.symbol == 0x04:
                    print(
                        f"got EoT at bit {j} of byte {i} a.k.a. {i:#x} "
                        + f"out of {len(in_buf)} a.k.a. {len(in_buf):#x}"
                    )
                    got_eot = True
                    break
                out_buf.append(symbol_node.symbol)
                symbol_node = symbol_root
            symbol_code >>= 1
        if got_eot:
            break
    return bytes(out_buf)


def real_main(args) -> int:
    assert args.in_file is not None
    in_buf = open(args.in_file, "rb").read()
    if args.histogram:
        hist = ByteHistogram()
        hist.add_bytes(in_buf)
        print(hist.ascii_histogram())
    elif args.dot:
        coder = HuffmanCoder(buf=in_buf)
    elif args.write_header:
        assert args.out_file is not None
        hdr_buf, _ = encode_header(in_buf)
        open(args.out_file, "wb").write(hdr_buf)
    elif args.read_header:
        data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
        encoded_len = len(in_buf) - data_idx
        print("Symbol histogram:")
        print(symbol_hist.ascii_histogram())
        print("Byte histogram:")
        print(byte_hist.ascii_histogram())
        print(
            f"Data start offset: {data_idx} a.k.a. {data_idx:#x} "
            + f"encoded len: {encoded_len} a.k.a. {encoded_len:#x} "
            + f"decoded len: {decoded_len} a.k.a {decoded_len:#x}"
        )
        HuffmanCoder(byte_hist=byte_hist, symbol_hist=symbol_hist)
    elif args.tree:
        data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
        encoded_len = len(in_buf) - data_idx
        print(
            f"Data start offset: {data_idx} a.k.a. {data_idx:#x} "
            + f"encoded len: {encoded_len} a.k.a. {encoded_len:#x} "
            + f"decoded len: {decoded_len} a.k.a {decoded_len:#x}"
        )
        coder = HuffmanCoder(byte_hist=byte_hist, symbol_hist=symbol_hist)
        assert coder.symbol_root is not None
        print(str(anytree.RenderTree(coder.symbol_root)) + "\n")
    elif args.flat:
        data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
        encoded_len = len(in_buf) - data_idx
        print(
            f"Data start offset: {data_idx} a.k.a. {data_idx:#x} "
            + f"encoded len: {encoded_len} a.k.a. {encoded_len:#x} "
            + f"decoded len: {decoded_len} a.k.a {decoded_len:#x}"
        )
        coder = HuffmanCoder(byte_hist=byte_hist, symbol_hist=symbol_hist)
        assert coder.symbol_root is not None
        sorted_leaf_nodes = sorted(
            anytree.search.findall(coder.symbol_root, filter_=lambda n: n.is_leaf)
        )
        for n in sorted_leaf_nodes:
            print(n)
    elif args.preorder:
        data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
        encoded_len = len(in_buf) - data_idx
        print(
            f"Data start offset: {data_idx} a.k.a. {data_idx:#x} "
            + f"encoded len: {encoded_len} a.k.a. {encoded_len:#x} "
            + f"decoded len: {decoded_len} a.k.a {decoded_len:#x}"
        )
        coder = HuffmanCoder(byte_hist=byte_hist, symbol_hist=symbol_hist)
        assert coder.symbol_root is not None
        preorder_leaf_nodes = anytree.iterators.preorderiter.PreOrderIter(
            coder.symbol_root, filter_=lambda n: n.is_leaf
        )
        for n in preorder_leaf_nodes:
            print(n)
    elif args.buffer:
        if has_encoded_header_magic(in_buf):
            data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
        else:
            _, symbol_hist = encode_header(in_buf)
        coder = HuffmanCoder(symbol_hist=symbol_hist)
        assert coder.symbol_root is not None
        defined_symbols = coder.symbol_root.get_symbols()
        for i in range(0x100):
            if i in defined_symbols:
                coding = coder.symbol_root.get_symbol_encoding(i)
                # symbol_node = coder.symbol_root.get_symbol(i)
                coding_str = "".join(["0" if not b else "1" for b in coding])
                # print(
                #     f"[{i:#04x}] symbol: {i:#010x} weight: {symbol_node.weight:#010x} buf: '{coding_str}'"
                # )
                print(f"[{i:#04x}] buf: '{coding_str}'")
            else:
                # print(f"[{i:#04x}] symbol: 0x00000000 weight: 0x00000000 buf: ''")
                print(f"[{i:#04x}] buf: ''")
    else:
        assert args.out_file is not None
        if has_encoded_header_magic(in_buf):
            data_idx, decoded_len, byte_hist, symbol_hist = decode_header(in_buf)
            encoded_len = len(in_buf) - data_idx
            print(
                f"Data start offset: {data_idx} a.k.a. {data_idx:#x} "
                + f"encoded len: {encoded_len} a.k.a. {encoded_len:#x} "
                + f"decoded len: {decoded_len} a.k.a {decoded_len:#x}"
            )
            coder = HuffmanCoder(byte_hist=byte_hist, symbol_hist=symbol_hist)
            out_buf = decode_data(in_buf[data_idx:], coder)
            print(f"out_buf len: {len(out_buf)} a.k.a {len(out_buf):#x}")
            open(args.out_file, "wb").write(out_buf)
        else:
            assert args.out_file is not None
            hdr_buf, symbol_hist = encode_header(in_buf)
            data_buf = encode_data(in_buf, symbol_hist)
            open(args.out_file, "wb").write(hdr_buf + data_buf)
    return 0


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="questa-tcl-huffman-util.py")
    parser.add_argument("-i", "--in-file", required=True, type=Path, help="Input path")
    parser.add_argument("-o", "--out-file", type=Path, help="Output path")
    parser.add_argument(
        "-H", "--histogram", action="store_true", help="Print a byte histogram of the input file"
    )
    parser.add_argument(
        "-d", "--dot", action="store_true", help="Generate a dot file of the Huffman tree"
    )
    parser.add_argument("-I", "--write-header", action="store_true", help="Write header")
    parser.add_argument("-D", "--read-header", action="store_true", help="Read header")
    parser.add_argument("-T", "--tree", action="store_true", help="Dump Huffman tree")
    parser.add_argument(
        "-F",
        "--flat",
        action="store_true",
        help="Dump Huffman tree leaf nodes in flat, sorted order",
    )
    parser.add_argument(
        "-p", "--preorder", action="store_true", help="Dump Huffman tree leaf nodes pre-ordered"
    )
    parser.add_argument("-b", "--buffer", action="store_true", help="Dump Huffman tree buffer")

    return parser


def main() -> int:
    return real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    sys.exit(main())
