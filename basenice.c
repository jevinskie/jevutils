#include <ctype.h>
#include <locale.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

uint8_t print_enc_tbl[0x80] = {
    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '\x54', '\x4e', '#',    '#',
    '\x52', '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',
    '#',    '#',    '#',    '#',    '#',    '#',    '\x53', '\x45', '\x51', '\x48', '\x44', '\x50', '\x41',
    '\x71', '\x6c', '\x72', '\x4f', '\x58', '\x63', '\x6d', '\x64', '\x46', '#',    '#',    '#',    '#',
    '#',    '#',    '#',    '#',    '#',    '#',    '\x6f', '\x70', '\x76', '\x75', '\x56', '\x57', '\x61',
    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',
    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',
    '\x62', '\x73', '\x42', '\x43', '\x5f', '\x74', '#',    '#',    '#',    '#',    '#',    '#',    '#',
    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',    '#',
    '#',    '#',    '#',    '#',    '#',    '#',    '\x69', '\x49', '\x6a', '\x77', '#'};

static char nibble_to_ascii_hex(const uint8_t chr) {
    if (chr <= 9) {
        return chr + '0';
    } else if (chr >= 0xA && chr <= 0xF) {
        return chr - 0xA + 'a';
    } else {
        __builtin_unreachable();
    }
}

static int do_enc(void) {
    int pc;
    for (pc = getchar_unlocked(); pc != EOF; pc = getchar_unlocked()) {
        if (isalnum(pc) && pc != '_') {
            putchar_unlocked(pc);
        } else if (pc == '_') {
            putchar_unlocked(pc);
            putchar_unlocked(pc);
        } else {
            if (isprint(pc) || pc == '\t' || pc == '\n' || pc == '\r') {
                putchar_unlocked('_');
                putchar_unlocked(print_enc_tbl[pc]);
            } else {
                putchar_unlocked('_');
                putchar_unlocked('x');
                putchar_unlocked(nibble_to_ascii_hex((pc >> 4) & 0xF));
                putchar_unlocked(nibble_to_ascii_hex(pc & 0xF));
            }
        }
    }
    return 0;
}

static int do_dec(void) {
    return 0;
}

int main(int argc, const char **argv) {
    if (argc != 2) {
        return -1;
    }
    setlocale(LC_ALL, "C");
    if (!strcmp(argv[1], "enc")) {
        return do_enc();
    } else if (!strcmp(argv[1], "dec")) {
        return do_dec();
    }
    return -1;
}
