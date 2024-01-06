#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fmt/format.h>
#include <mach-o/fixup-chains.h>
#include <mach-o/loader.h>
#include <span>
#include <string>
#include <vector>

using lc_t = const struct load_command *;

int main(int argc, const char **argv) {
    assert(argc == 2);
    FILE *f = fopen(argv[1], "rb");
    assert(f);
    assert(!fseek(f, 0, SEEK_END));
    const uint64_t fsz = (uint64_t)ftell(f);
    fprintf(stderr, "macho size: 0x%llx\n", fsz);
    auto buf_rw = (uint8_t *)malloc(fsz);
    assert(buf_rw);
    assert(!fseek(f, 0, SEEK_SET));
    const auto sz_read = fread(buf_rw, (size_t)fsz, 1, f);
    assert(sz_read == 1);
    fclose(f);
    auto buf = (const uint8_t *const)buf_rw;

    auto mh = (const struct mach_header_64 *const)buf;
    assert(mh->magic == MH_MAGIC_64);
    assert(mh->cputype == CPU_TYPE_ARM64);
    assert(mh->cpusubtype == CPU_SUBTYPE_ARM64E);
    assert(mh->filetype == MH_FILESET);
    auto first_lc = (lc_t const)(&mh[1]);

    const struct linkedit_data_command *chained_fixups_lc = nullptr;
    lc_t cur_lc                                           = first_lc;
    for (uint32_t i = 0; i < mh->ncmds; ++i) {
        if (cur_lc->cmd == LC_DYLD_CHAINED_FIXUPS) {
            chained_fixups_lc = (const struct linkedit_data_command *)cur_lc;
            break;
        }
        cur_lc = (lc_t)((uintptr_t)cur_lc + cur_lc->cmdsize);
    }
    assert(chained_fixups_lc);

    const struct segment_command_64 *linkedit_seg = nullptr;
    cur_lc                                        = first_lc;
    for (uint32_t i = 0; i < mh->ncmds; ++i) {
        if (cur_lc->cmd == LC_SEGMENT_64) {
            auto seg = (const struct segment_command_64 *const)cur_lc;
            if (!strncmp(SEG_LINKEDIT, seg->segname, sizeof(seg->segname))) {
                linkedit_seg = seg;
                break;
            }
        }
        cur_lc = (lc_t)((uintptr_t)cur_lc + cur_lc->cmdsize);
    }
    assert(linkedit_seg);

    free((void *)buf);
    return 0;
}
