#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <locale.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <wchar.h>

#undef NDEBUG
#include <assert.h>

#define FALLBACK_TERM_WIDTH 80
#define MAX_TERM_WIDTH      1024
#define COUNT_NUM_DIGITS    5
#define STR(x)              #x
#define XSTR(x)             STR(x)

static uint8_t *slurp_file(const char *path, size_t *sz_ptr) {
    if (!path) {
        fprintf(stderr, "slurp_file provided with NULL path. WTF am I supposed to open!?\n");
        exit(2);
    }
    if (!sz_ptr) {
        fprintf(stderr, "slurp_file provided with NULL sz_ptr. You really probably want the size...\n");
        exit(3);
    }
    errno    = 0;
    FILE *fh = fopen(path, "rb");
    if (!fh) {
        const int fopen_errno = errno;
        fprintf(stderr, "Couldn't open '%s' for slurping. errno: %d a.k.a. %s\n", path, fopen_errno,
                strerror(fopen_errno));
        exit(4);
    }
    errno                   = 0;
    const int fseek_end_res = fseek(fh, 0, SEEK_END);
    if (fseek_end_res) {
        const int fseek_end_errno = errno;
        fprintf(stderr, "Couldn't seek to end of '%s' for slurping. errno: %d a.k.a. %s\n", path, fseek_end_errno,
                strerror(fseek_end_errno));
        exit(5);
    }
    errno                = 0;
    const long ftell_res = ftell(fh);
    if (ftell_res < 0) {
        const int ftell_errno = errno;
        fprintf(stderr, "Couldn't ftell on '%s' for slurping. errno: %d a.k.a. %s\n", path, ftell_errno,
                strerror(ftell_errno));
        exit(6);
    }
    errno = 0;
    rewind(fh);
    const int rewind_errno = errno;
    if (rewind_errno) {
        fprintf(stderr, "Couldn't rewind on '%s' for slurping. errno: %d a.k.a. %s\n", path, rewind_errno,
                strerror(rewind_errno));
        exit(7);
    }
    const size_t sz = (size_t)ftell_res;
    errno           = 0;
    uint8_t *buf    = malloc(sz);
    if (!buf) {
        const int malloc_errno = errno;
        fprintf(stderr, "Couldn't malloc buffer of size %zu for '%s' for slurping. errno: %d a.k.a. %s\n", sz, path,
                malloc_errno, strerror(malloc_errno));
        exit(8);
    }
    errno                  = 0;
    const size_t fread_res = fread(buf, sz, 1, fh);
    if (fread_res != 1) {
        const int fread_errno  = errno;
        const char *feof_str   = feof(fh) ? "IS_EOF" : "NOT_EOF";
        const char *ferror_str = ferror(fh) ? "IS_FERROR" : "NO_FERROR";
        fprintf(stderr,
                "Couldn't read size %zu from '%s' for slurping. feof: %s ferror: %s errno: %d "
                "a.k.a. %s\n",
                sz, path, feof_str, ferror_str, fread_errno, strerror(fread_errno));
        free(buf);
        exit(9);
    }
    errno                = 0;
    const int fclose_res = fclose(fh);
    if (fclose_res) {
        const int fclose_errno = errno;
        const char *fclose_str = fclose_res ? "IS_EOF" : "IS_ZERO";
        fprintf(stderr, "Couldn't fclose(fh) of '%s' for slurping!? fclose res: %s errno: %d a.k.a. %s\n", path,
                fclose_str, fclose_errno, strerror(fclose_errno));
        free(buf);
        exit(10);
    }
    *sz_ptr = sz;
    return buf;
}

static uint32_t get_term_width(void) {
    struct winsize w = {0};
    if (ioctl(fileno(stdout), TIOCGWINSZ, &w)) {
        return FALLBACK_TERM_WIDTH;
    }
    if (!w.ws_col) {
        return FALLBACK_TERM_WIDTH;
    }
    return w.ws_col > MAX_TERM_WIDTH ? MAX_TERM_WIDTH : (uint32_t)w.ws_col;
}

static void render_block_str(wchar_t *buf, double percentage, uint32_t width) {
    assert(buf);
    const uint32_t full_width            = width * 8;
    const uint32_t num_blk               = percentage * full_width;
    const uint32_t full_blks             = num_blk / 8;
    const uint32_t partial_blks          = num_blk % 8;
    static const wchar_t partial_chars[] = {L'▏', L'▎', L'▍', L'▌', L'▋', L'▊', L'▉'};
    uint32_t i;
    for (i = 0; i < full_blks; ++i) {
        buf[i] = L'█';
    }
    if (partial_blks > 0) {
        buf[i++] = partial_chars[partial_blks - 1];
    }
    buf[i++] = L'\0';
}

static void display_byte_histogram(const char *const path) {
    size_t sz                   = 0;
    const uint8_t *buf          = slurp_file(path, &sz);
    uint64_t byte_counts[0x100] = {0};
    for (size_t i = 0; i < sz; ++i) {
        ++byte_counts[buf[i]];
    }
    free((void *)buf);
    uint64_t max_count = 0;
    for (int i = 0; i < 0x100; ++i) {
        if (byte_counts[i] > max_count) {
            max_count = byte_counts[i];
        }
    }
    const uint32_t term_width = get_term_width();
    const uint32_t prefix_len = 2 + 1 + 3 + 2 + COUNT_NUM_DIGITS + 3;
    const uint32_t bar_width  = term_width <= prefix_len ? 0 : term_width - prefix_len;
    wchar_t bar_buf[MAX_TERM_WIDTH + 1];
    char print_char_buf[4]        = {'\'', '-', '\'', '\0'};
    const char *nonprint_char_buf = "   ";
    for (int i = 0; i < 0x100; ++i) {
        render_block_str(bar_buf, (double)byte_counts[i] / max_count, bar_width);
        const char *char_buf;
        if (isprint(i) && i < 0x80) {
            print_char_buf[1] = (char)i;
            char_buf          = print_char_buf;
        } else {
            char_buf = nonprint_char_buf;
        }
        wprintf(L"%02hhx %s [%" XSTR(COUNT_NUM_DIGITS) PRIu64 "]: %ls\n", i, char_buf, byte_counts[i], bar_buf);
    }
}

int main(int argc, const char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: byte-histogram <FILE>\n");
        return 1;
    }
    assert(setlocale(LC_ALL, "en_US.UTF-8"));
    display_byte_histogram(argv[1]);
    return 0;
}
