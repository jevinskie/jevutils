#undef NDEBUG
#include <cassert>

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <filesystem>
#include <mutex>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

#include "BS_thread_pool.hpp"

namespace fs = std::filesystem;

void check_macho(const fs::path &file_path, std::vector<fs::path> &machos, std::mutex &machos_mutex) {
    const auto fd = ::open(file_path.c_str(), O_RDONLY);
    assert(fd >= 0);
    struct stat st;
    assert(!::fstat(fd, &st));
    const auto sz = static_cast<size_t>(st.st_size);
    if (sz < 4) {
        assert(!::close(fd));
        return;
    }
    uint32_t magic;
    assert(4 == ::read(fd, &magic, sizeof(magic)));
    assert(!::close(fd));
    bool is_macho = false;
    // one of the seven endians
    is_macho |= magic == 0xfeedface; // 32-bit
    is_macho |= magic == 0xfeedfacf; // 64-bit
    is_macho |= magic == 0xcafebabe; // 32-bit fat
    is_macho |= magic == 0xcafebabf; // 64-bit fat
    // the other of the seven endians
    is_macho |= magic == 0xcefaedfe; // 32-bit
    is_macho |= magic == 0xcffaedfe; // 64-bit
    is_macho |= magic == 0xbebafeca; // 32-bit fat
    is_macho |= magic == 0xbfbafeca; // 64-bit fat
    if (!is_macho) {
        return;
    }
    {
        std::lock_guard lock{machos_mutex};
        machos.push_back(file_path);
    }
}

template <BS::opt_t OptFlags>
void search_directory(const fs::path &root, std::vector<fs::path> &machos, std::mutex &machos_mutex,
                      BS::thread_pool<OptFlags> &pool) {
    for (const auto &entry : std::filesystem::recursive_directory_iterator(root)) {
        if (!entry.is_regular_file()) {
            continue;
        }
        const auto &file_path = entry.path();
        pool.detach_task([file_path, &machos, &machos_mutex] {
            check_macho(file_path, machos, machos_mutex);
        });
    }
    pool.wait();
}

int main(int argc, const char **argv) {
    if (argc != 2) {
        fprintf(::stderr, "usage: find-macho <path to directory to search>\n");
        return -1;
    }
    const auto dir_path = fs::path{argv[1]};
    std::mutex machos_mutex;
    std::vector<fs::path> machos;
    BS::thread_pool tp;
    search_directory(dir_path, machos, machos_mutex, tp);
    const auto num_macho = machos.size();
    for (size_t i = 0; i < num_macho; ++i) {
        printf("%s\n", machos[i].c_str());
    }
    return 0;
}
