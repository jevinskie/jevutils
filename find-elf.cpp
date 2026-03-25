#undef NDEBUG
#include <cassert>

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

void check_elf(const fs::path &file_path, std::vector<fs::path> &elfs, std::mutex &elfs_mutex) {
    const auto fd = ::open(file_path.c_str(), O_RDONLY);
    assert(fd >= 0);
    struct stat st;
    assert(!::fstat(fd, &st));
    const auto sz = static_cast<size_t>(st.st_size);
    if (sz < 4) {
        assert(!::close(fd));
        return;
    }

    uint8_t ident[4];
    assert(4 == ::read(fd, ident, sizeof(ident)));
    assert(!::close(fd));

    const bool has_elf_magic = ident[0] == 0x7f && ident[1] == 'E' && ident[2] == 'L' && ident[3] == 'F';
    if (!has_elf_magic) {
        return;
    }

    {
        std::lock_guard lock{elfs_mutex};
        elfs.push_back(file_path);
    }
}

template <BS::opt_t OptFlags>
void search_directory(const fs::path &root, std::vector<fs::path> &elfs, std::mutex &elfs_mutex,
                      BS::thread_pool<OptFlags> &pool) {
    for (const auto &entry : std::filesystem::recursive_directory_iterator(root)) {
        if (!entry.is_regular_file()) {
            continue;
        }
        const auto &file_path = entry.path();
        pool.detach_task([file_path, &elfs, &elfs_mutex] {
            check_elf(file_path, elfs, elfs_mutex);
        });
    }
    pool.wait();
}

int main(int argc, const char **argv) {
    if (argc != 2) {
        fprintf(::stderr, "usage: find-elf <path to directory to search>\n");
        return -1;
    }
    const auto dir_path = fs::path{argv[1]};
    std::mutex elfs_mutex;
    std::vector<fs::path> elfs;
    BS::thread_pool tp;
    search_directory(dir_path, elfs, elfs_mutex, tp);
    const auto num_elf = elfs.size();
    for (size_t i = 0; i < num_elf; ++i) {
        printf("%s\n", elfs[i].c_str());
    }
    return 0;
}
