#!/usr/bin/env python3

import io
import sys
import unittest


def normalize_uuid(raw_uuid: str) -> str:
    stripped_uuid = "".join(filter(lambda c: c in "0123456789abcdefABCDEF", raw_uuid))
    if len(stripped_uuid) != 32:
        raise ValueError("Length of UUID is not 32 hex nibbles")
    # example format: AA5A6FE0-9E4C-3611-9B8D-A4D55923C105
    # 8-4-4-4-12 chars
    u = stripped_uuid
    return f"{u[0:0+8]}-{u[8:8+4]}-{u[12:12+4]}-{u[16:16+4]}-{u[20:20+12]}"


class NormalizeUUIDTest(unittest.TestCase):
    def test_strip1(self):
        self.assertEqual(
            normalize_uuid("DE/DFA0F03B6D397D85C1AE074F8BD68B"),
            "DEDFA0F0-3B6D-397D-85C1-AE074F8BD68B",
        )

    def test_roundtrip(self):
        self.assertEqual(
            normalize_uuid("AA5A6FE0-9E4C-3611-9B8D-A4D55923C105"),
            "AA5A6FE0-9E4C-3611-9B8D-A4D55923C105",
        )

    def test_length_check(self):
        with self.assertRaises(ValueError) as context:
            normalize_uuid("its duck season")
        self.assertTrue("Length of UUID is not 32 hex nibbles" in str(context.exception))


assert normalize_uuid("DE/DFA0F03B6D397D85C1AE074F8BD68B") == "DEDFA0F0-3B6D-397D-85C1-AE074F8BD68B"
assert (
    normalize_uuid("AA5A6FE0-9E4C-3611-9B8D-A4D55923C105") == "AA5A6FE0-9E4C-3611-9B8D-A4D55923C105"
)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(NormalizeUUIDTest)
test_text = io.StringIO()
runner = unittest.TextTestRunner(stream=test_text)
test_result = runner.run(suite)
if not test_result.wasSuccessful():
    print(test_text.getvalue(), file=sys.stderr)
    print("self-test failed, exiting", file=sys.stderr)
    sys.exit(-2)

if len(sys.argv) != 2:
    print("usage: macho-format-uuid.py <unformatted UUID>")
    sys.exit(-1)

print(normalize_uuid(sys.argv[1]))
