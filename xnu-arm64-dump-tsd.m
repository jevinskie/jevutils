#include <sys/qos.h>
#undef NDEBUG
#import <Foundation/Foundation.h>
#include <assert.h>
#import <dispatch/dispatch.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef __arm64__
#error bad arch, arm64 only
#endif

#define TSD_SZ 256

#define tsd_get_base()                              \
    ({                                              \
        uintptr_t tsd;                              \
        __asm__("mrs %0, TPIDRRO_EL0" : "=r"(tsd)); \
        (void **)tsd;                               \
    })

static __attribute__((always_inline)) void **_os_tsd_get_base(void) {
    uintptr_t tsd;
    __asm__("mrs %0, TPIDRRO_EL0" : "=r"(tsd));

    return (void **)tsd;
}

static void dump_tsd(void) {
    void **tsd_base = tsd_get_base();
    printf("tsd => %p\n", (void *)tsd_base);
    for (int i = 0; i < TSD_SZ; ++i) {
        printf("tsd[%3d]: %p\n", i, tsd_base[i]);
    }
}

int main(void) {
    @autoreleasepool {
        dump_tsd();
        NSLog(@"\n\n\nNOW LIBDISPATCH\n\n\n");
        dispatch_queue_attr_t a =
            dispatch_queue_attr_make_with_qos_class(DISPATCH_QUEUE_CONCURRENT, QOS_CLASS_USER_INTERACTIVE, 100);
        assert(a);
        a = dispatch_queue_attr_make_with_autorelease_frequency(a, DISPATCH_AUTORELEASE_FREQUENCY_WORK_ITEM);
        dispatch_queue_t q =
            dispatch_queue_create_with_target("test_q", a, dispatch_get_global_queue(QOS_CLASS_USER_INTERACTIVE, 0));
        assert(q);
        dispatch_sync(q, ^{
            dump_tsd();
            exit(0);
        });
        dispatch_main();
    }
    return 0;
}
