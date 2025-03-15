#include <pthread.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/param.h>
#include <sys/types.h>

int main(int argc, const char **argv, const char **envp, const char **apple) {
    size_t i;
    bool got_null;

    void *stackaddr  = pthread_get_stackaddr_np(pthread_self());
    size_t stacksize = pthread_get_stacksize_np(pthread_self());
    printf("stackaddr: %p\n", stackaddr);
    printf("stacksize: 0x%zx\n", stacksize);

    void *frameaddr = __builtin_frame_address(0);
    printf("frameaddr: %p\n", frameaddr);

    printf("argc:  %d\n", argc);

    printf("argv: %p\n", (void *)argv);
    i                  = 0;
    got_null           = false;
    const char **targp = argv;
    do {
        const char *targ = *targp;
        printf("argv[%zu]  = %p '%s'\n", i, (void *)targ, targ);
        printf("&argv[%zu] = %p\n", i, (void *)targp);
        ++i;
        ++targp;
        got_null = !targ;
    } while (!got_null);

    printf("envp: %p\n", (void *)envp);
    i                  = 0;
    got_null           = false;
    const char **tenvp = envp;
    do {
        const char *tenv = *tenvp;
        printf("envp[%zu]  = %p '%s'\n", i, (void *)tenv, tenv);
        printf("&envp[%zu] = %p\n", i, (void *)tenvp);
        ++i;
        ++tenvp;
        got_null = !tenv;
    } while (!got_null);

    printf("apple: %p\n", (void *)apple);
    i                    = 0;
    got_null             = false;
    const char **tapplep = apple;
    do {
        const char *tapple = *tapplep;
        printf("apple[%zu]  = %p '%s'\n", i, (void *)tapple, tapple);
        printf("&apple[%zu] = %p\n", i, (void *)tapplep);
        ++i;
        ++tapplep;
        got_null = !tapple;
    } while (!got_null);

    const char *strp            = (const char *)roundup((uintptr_t)tapplep, 16);
    uintptr_t apple_str_padding = (uintptr_t)strp - (uintptr_t)tapplep;
    printf("padding between apple array pointers and string area: %zu\n", apple_str_padding);
    printf("string area: %p\n", (void *)strp);
    i           = 0;
    size_t slen = 0;
    do {
        slen = strlen(strp);
        printf("%p: len: %zu '%s'\n", (void *)strp, slen, strp);
        strp += slen + 1;
    } while ((void *)strp < stackaddr);

    return 0;
}
