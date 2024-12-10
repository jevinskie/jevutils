#undef NDEBUG
#include <assert.h>

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

static void print_usage(void) {
    fprintf(stderr, "usage: jevxcselect [-sdkpath [sdk]] \n");
}

int main(int argc, const char **argv) {
    if (argc != 1) {
        print_usage();
        return 1;
    }
    return 0;
}
