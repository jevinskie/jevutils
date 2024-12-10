#include <cerrno>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/fsgetpath.h>

static_assert(sizeof(uint64_t) == sizeof(fsid_t));

int main(int argc, const char **argv) {
    if (argc != 3) {
        fprintf(stderr,
                "Usage: %s <64-bit fsid in 0x-prefixed hex or decimal> <64-bit obj_id in "
                "0x-prefixed hex or decimal>\nPrints the path given an fsid and obj_id\n",
                getprogname());
        return 1;
    }
    uint64_t fsid = {};
    if (1 != sscanf(argv[1], "0x%" PRIx64, &fsid)) {
        if (1 != sscanf(argv[1], "%" PRIu64, &fsid)) {
            fprintf(stderr, "Error: failed to parse '%s' as a 64-bit 0x-prefixed hex or decimal fsid\n", argv[1]);
            return 2;
        }
    }
    uint64_t obj_id = {};
    if (1 != sscanf(argv[2], "0x%" PRIx64, &obj_id)) {
        if (1 != sscanf(argv[2], "%" PRIu64, &obj_id)) {
            fprintf(stderr, "Error: failed to parse '%s' as a 64-bit 0x-prefixed hex or decimal obj_id\n", argv[2]);
            return 3;
        }
    }
    char path[8 * 1024] = {};
    errno               = 0;
    const auto res      = fsgetpath(path, sizeof(path), (fsid_t *)&fsid, obj_id);
    if (res < 0 || errno) {
        fprintf(stderr, "fsgetpath for fsid: 0x%016" PRIx64 " obj_id: 0x%016" PRIx64 " failed.\nerrno: %d a.k.a. %s\n",
                fsid, obj_id, errno, strerror(errno));
        return 4;
    }
    if (res >= 0 && res < 2) {
        fprintf(stderr, "fsgetpath for fsid: 0x%016" PRIx64 " obj_id: 0x%016" PRIx64 " returned an empty path.\n", fsid,
                obj_id);
        return 5;
    }
    printf("fsgetpath for fsid: 0x%016" PRIx64 " (%" PRIu64 ") and obj_id 0x%016" PRIx64 " (%" PRIu64 ") => %s\n", fsid,
           fsid, obj_id, obj_id, path);
    return 0;
}
