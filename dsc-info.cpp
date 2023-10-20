#ifndef __APPLE__
#error dsc-info is only for Apple platforms
#endif

#include <TargetConditionals.h>
#include <cerrno>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <mach-o/dyld_images.h>
#include <mach/mach_error.h>
#include <mach/task.h>
#include <sys/fsgetpath.h>

#if TARGET_OS_MAC && !TARGET_OS_IPHONE
// This is macOS and not iOS, tvOS, or watchOS
#define IS_MACOS
#endif

static_assert(sizeof(uint64_t) == sizeof(fsid_t));
static_assert(sizeof(uint32_t) == sizeof(kern_return_t));
static_assert(sizeof(uint32_t) == sizeof(integer_t));
static_assert(sizeof(uint32_t) == sizeof(mach_port_t));

using dyld_all_image_infos_t = struct dyld_all_image_infos;

static constexpr const char *maybe_null_str(const char *str) {
    if (!str) {
        return "(null)";
    }
    return str;
}

int main(int argc, const char **argv) {
    (void)argv;
    if (argc != 1) {
        fprintf(stderr, "Usage: %s\nPrints dyld_shared_cache info\n", getprogname());
        return 1;
    }
    task_dyld_info_data_t dyld_info;
    mach_msg_type_number_t dyld_info_cnt = TASK_DYLD_INFO_COUNT;
    const auto kr =
        task_info(mach_task_self(), TASK_DYLD_INFO, (task_info_t)&dyld_info, &dyld_info_cnt);
    if (kr != KERN_SUCCESS) {
        fprintf(stderr,
                "Got Mach error: 0x%08" PRIx32
                " description: '%s' when calling task_info() for TASK_DYLD_INFO\n",
                kr, mach_error_string(kr));
        return 2;
    }
    if (dyld_info.all_image_info_format != TASK_DYLD_ALL_IMAGE_INFO_64) {
        fprintf(stderr,
                "dyld_all_image_infos format is 0x%08" PRIx32
                " and I can only handle TASK_DYLD_ALL_IMAGE_INFO_64\n",
                dyld_info.all_image_info_format);
        return 3;
    }
    const auto infos   = (dyld_all_image_infos_t *)dyld_info.all_image_info_addr;
    const auto version = infos->version;
    printf("dyld_all_image_infos address: %p\n", infos);
    printf("version: %" PRIu32 "\n", version);
    printf("infoArrayCount: %" PRIu32 "\n", infos->infoArrayCount);
    printf("infoArray: %p\n", infos->infoArray);
    printf("notification: %p\n", infos->notification);
    printf("processDetachedFromSharedRegion: %d\n", infos->processDetachedFromSharedRegion);
    if (version < 2) {
        return 0;
    }
    printf("libSystemInitialized: %d\n", infos->libSystemInitialized);
    printf("dyldImageLoadAddress: %p\n", infos->dyldImageLoadAddress);
    if (version < 3) {
        return 0;
    }
    printf("jitInfo: %p\n", infos->jitInfo);
    if (version < 5) {
        return 0;
    }
    printf("dyldVersion: %s\n", maybe_null_str(infos->dyldVersion));
    printf("errorMessage: '%s'\n", maybe_null_str(infos->errorMessage));
    printf("terminationFlags: 0x%016" PRIx64 "\n", (uint64_t)infos->terminationFlags);
    if (version < 6) {
        return 0;
    }
    printf("coreSymbolicationShmPage: %p\n", infos->coreSymbolicationShmPage);
    if (version < 7) {
        return 0;
    }
    printf("systemOrderFlag: 0x%016" PRIx64 "\n", (uint64_t)infos->systemOrderFlag);
    if (version < 8) {
        return 0;
    }
    printf("uuidArrayCount: %" PRIu64 "\n", (uint64_t)infos->uuidArrayCount);
    printf("uuidArray: %p\n", infos->uuidArray);
    for (uintptr_t i = 0; i < infos->uuidArrayCount; ++i) {
        const auto uuid_info = infos->uuidArray[i];
        printf("\t[%" PRIu64 "]\n", (uint64_t)i);
        printf("\t\timageLoadAddress: %p\n", uuid_info.imageLoadAddress);
        // example format: AA5A6FE0-9E4C-3611-9B8D-A4D55923C105
        // 4-2-2-2-6 bytes
        const auto u = uuid_info.imageUUID;
        printf("\t\timageUUID: "
               "%02hhX%02hhX%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX%02hhX%"
               "02hhX%02hhX%02hhX\n",
               u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10], u[11], u[12],
               u[13], u[14], u[15]);
    }
    if (version < 9) {
        return 0;
    }
    printf("dyldAllImageInfosAddress: %p\n", infos->dyldAllImageInfosAddress);
    if (version < 10) {
        return 0;
    }
    printf("initialImageCount: %" PRIu64 "\n", (uint64_t)infos->initialImageCount);
    if (version < 11) {
        return 0;
    }
    printf("errorKind: 0x%016" PRIx64 "\n", (uint64_t)infos->errorKind);
    printf("errorClientOfDylibPath: '%s'\n", maybe_null_str(infos->errorClientOfDylibPath));
    printf("errorTargetDylibPath: '%s'\n", maybe_null_str(infos->errorTargetDylibPath));
    printf("errorSymbol: '%s'\n", maybe_null_str(infos->errorSymbol));
    if (version < 12) {
        return 0;
    }
    printf("sharedCacheSlide: 0x%016" PRIx64 "\n", (uint64_t)infos->sharedCacheSlide);
    if (version < 13) {
        return 0;
    }
    const auto scu = infos->sharedCacheUUID;
    printf("sharedCacheUUID: "
           "%02hhX%02hhX%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX%02hhX%"
           "02hhX%02hhX%02hhX\n",
           scu[0], scu[1], scu[2], scu[3], scu[4], scu[5], scu[6], scu[7], scu[8], scu[9], scu[10],
           scu[11], scu[12], scu[13], scu[14], scu[15]);
    if (version < 15) {
        return 0;
    }
    printf("sharedCacheBaseAddress: 0x%016" PRIx64 "\n", (uint64_t)infos->sharedCacheBaseAddress);
    printf("infoArrayChangeTimestamp: %" PRIu64 "\n", infos->infoArrayChangeTimestamp);
    printf("dyldPath: '%s'\n", maybe_null_str(infos->dyldPath));
    printf("notifyPorts:\n");
    for (size_t i = 0; i < DYLD_MAX_PROCESS_INFO_NOTIFY_COUNT; ++i) {
        printf("\t[%zu]: 0x%08" PRIx32 "\n", i, infos->notifyPorts[i]);
    }
    if (version < 16) {
        return 0;
    }
    printf("compact_dyld_image_info_addr: 0x%016" PRIx64 "\n",
           (uint64_t)infos->compact_dyld_image_info_addr);
    printf("compact_dyld_image_info_size: %zu\n", infos->compact_dyld_image_info_size);
    printf("platform: 0x%08" PRIx32 "\n", infos->platform);
    if (version < 17) {
        return 0;
    }
#ifdef IS_MACOS
    printf("aotInfoCount: %" PRIu32 "\n", infos->aotInfoCount);
    printf("aotInfoArray: %p\n", infos->aotInfoArray);
    for (uint32_t i = 0; i < infos->aotInfoCount; ++i) {
        const auto aot_info = infos->aotInfoArray;
        printf("\t[%" PRIu32 "]\n", i);
        printf("\t\tx86LoadAddress: %p\n", aot_info[i].x86LoadAddress);
        printf("\t\taotLoadAddress: %p\n", aot_info[i].aotLoadAddress);
        printf("\t\taotImageSize: 0x%016" PRIx64 "\n", aot_info[i].aotImageSize);
        const auto k = aot_info[i].aotImageKey;
        printf("\t\taotImageKey: "
               "%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%"
               "02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX%"
               "02hhX%02hhX%02hhX%02hhX%02hhX%02hhX\n",
               k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7], k[8], k[9], k[10], k[11], k[12],
               k[13], k[14], k[15], k[16], k[17], k[18], k[19], k[20], k[21], k[22], k[23], k[24],
               k[25], k[26], k[27], k[28], k[29], k[30], k[31]);
    }
    printf("aotInfoArrayChangeTimestamp: %" PRIu64 "\n", infos->aotInfoArrayChangeTimestamp);
    printf("aotSharedCacheBaseAddress: %p\n", (void *)infos->aotSharedCacheBaseAddress);
    const auto au = infos->aotSharedCacheUUID;
    printf("aotSharedCacheUUID: "
           "%02hhX%02hhX%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX-%02hhX%02hhX%02hhX%"
           "02hhX%02hhX%02hhX\n",
           au[0], au[1], au[2], au[3], au[4], au[5], au[6], au[7], au[8], au[9], au[10], au[11],
           au[12], au[13], au[14], au[15]);
#endif
    if (version < 18) {
        return 0;
    }
    printf("sharedCacheFSID: 0x%016" PRIx64 " (%" PRIu64 ")\n", infos->sharedCacheFSID,
           infos->sharedCacheFSID);
    printf("sharedCacheFSObjID: 0x%016" PRIx64 " (%" PRIu64 ")\n", infos->sharedCacheFSObjID,
           infos->sharedCacheFSObjID);
    char sc_path[8 * 1024]     = {};
    errno                      = 0;
    const auto fs_get_path_res = fsgetpath(
        sc_path, sizeof(sc_path), (fsid_t *)&infos->sharedCacheFSID, infos->sharedCacheFSObjID);
    if (fs_get_path_res < 0 || errno) {
        const auto e = errno;
        fprintf(stderr,
                "fsgetpath for dyld_shared_cache fsid: 0x%016" PRIx64 " (%" PRIu64
                ") obj_id: 0x%016" PRIx64 " (%" PRIu64 ") failed.\nerrno: %d a.k.a. %s\n",
                infos->sharedCacheFSID, infos->sharedCacheFSID, infos->sharedCacheFSObjID,
                infos->sharedCacheFSObjID, e, strerror(e));
        return 4;
    }
    if (fs_get_path_res >= 0 && fs_get_path_res < 2) {
        fprintf(stderr,
                "fsgetpath for dyld_shared_cache fsid: 0x%016" PRIx64 " (%" PRIu64
                ") obj_id: 0x%016" PRIx64 " (%" PRIu64 ") returned an empty path.\n",
                infos->sharedCacheFSID, infos->sharedCacheFSID, infos->sharedCacheFSObjID,
                infos->sharedCacheFSObjID);
        return 5;
    }
    printf("sharedCache path: '%s'\n", maybe_null_str(sc_path));
    return 0;
}
