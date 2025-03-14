#include <pthread.h>
#include <stdio.h>
#include <string.h>

int main(int argc, const char **argv, const char **envp, const char **apple) {
    size_t i;

    void *stackaddr  = pthread_get_stackaddr_np(pthread_self());
    size_t stacksize = pthread_get_stacksize_np(pthread_self());
    printf("stackaddr: %p\n", stackaddr);
    printf("stacksize: 0x%zx\n", stacksize);

    void *frameaddr = __builtin_frame_address(0);
    printf("frameaddr: %p\n", frameaddr);

    printf("argc:  %d\n", argc);
    printf("argv:  %p\n", (void *)argv);
    for (i = 0; i < (size_t)argc + 1; ++i) {
        printf("argv[%zu]  = '%s'\n", i, argv[i]);
        printf("&argv[%zu] = %p\n", i, (void *)&argv[i]);
    }

    const char **tenvp   = envp;
    const char **tapplep = apple;

    printf("envp: %p\n", (void *)envp);
    i = 0;
    do {
        const char *tenv = *tenvp;
        printf("envp[%zu]  = %p '%s'\n", i, (void *)tenv, tenv);
        printf("&envp[%zu] = %p\n", i, (void *)tenvp);
        ++i;
        ++tenvp;
    } while (*tenvp && tenvp != tapplep);

    printf("apple: %p\n", (void *)apple);
    i = 0;
    do {
        const char *tapple = *tapplep;
        printf("apple[%zu]  = %p '%s'\n", i, (void *)tapple, tapple);
        printf("&apple[%zu] = %p\n", i, (void *)tapplep);
        ++i;
        ++tapplep;
    } while (*tapplep && tapplep != stackaddr);

    const char *strp = (const char *)&tapplep[1];
    i                = 0;
    size_t slen      = 0;
    do {
        slen = strlen(strp);
        printf("%p: len: %zu '%s'\n", (void *)strp, slen, strp);
        strp += slen + 1;
    } while ((void *)strp < stackaddr);

    return 0;
}
