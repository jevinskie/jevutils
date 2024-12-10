#undef NDEBUG
#include <assert.h>

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syslimits.h>

#define OPTPARSE_IMPLEMENTATION
#define OPTPARSE_API static
#include <optparse.h>

#define BOOLSTR(b) ((b) ? "true" : "false")

typedef void *xcselect_manpaths;

extern bool xcselect_get_developer_dir_path(char *path, int path_sz, bool *from_env_var, bool *from_command_line_tools,
                                            bool *from_default);
extern xcselect_manpaths _Nullable xcselect_get_manpaths(char const *_Nullable sdkname);
extern uint32_t xcselect_manpaths_get_num_paths(xcselect_manpaths manpaths);
extern const char *_Nullable xcselect_manpaths_get_path(xcselect_manpaths manpaths, uint32_t idx);
extern void xcselect_manpaths_free(xcselect_manpaths manpaths);
extern const char *xcselect_get_version(void);

static void print_usage(void) {
    fprintf(stderr,
            "usage: %s [-s | --sdkname NAME] [-V | --verbose] [[-p | --sdkpath] | [-d | --devpath] | [-m | --manpath] "
            "| [-v | --version] | "
            "[-h | --help]]\n",
            getprogname());
}

static void print_sdkpath(char const *_Nullable sdk) {
    printf("sdkpath: %s\n", sdk ? sdk : "(null)");
}

static void print_devpath(bool verbose) {
    char path[PATH_MAX]          = {0};
    bool from_env_var            = false;
    bool from_command_line_tools = false;
    bool from_default            = false;
    const bool res =
        xcselect_get_developer_dir_path(path, sizeof(path), &from_env_var, &from_command_line_tools, &from_default);
    if (!res) {
        if (verbose) {
            fprintf(stderr, "Failed to get the developer path.\n");
        }
        exit(2);
    }
    if (verbose) {
        printf("from_env_var: %s\n", BOOLSTR(from_env_var));
        printf("from_command_line_tools: %s\n", BOOLSTR(from_command_line_tools));
        printf("from_default: %s\n", BOOLSTR(from_default));
    }
    printf("%s\n", path);
}

static void print_manpaths(char const *_Nullable sdkname) {
    xcselect_manpaths manpaths = xcselect_get_manpaths(sdkname);
    if (!manpaths) {
        return;
    }
    const uint32_t num_paths = xcselect_manpaths_get_num_paths(manpaths);
    for (uint32_t i = 0; i < num_paths; ++i) {
        const char *man_path = xcselect_manpaths_get_path(manpaths, i);
        assert(man_path);
        printf("%s", man_path);
        if (i + 1 != num_paths) {
            printf(":");
        } else {
            printf("\n");
        }
    }
    xcselect_manpaths_free(manpaths);
}

static void print_version(void) {
    printf("xcode-select version: %s\n", xcselect_get_version());
}

int main(int argc, char **argv) {
    (void)argc; // unused

    const char *sdk     = NULL;
    const char *sdkname = "macosx";
    bool verbose        = false;
    bool do_sdkpath     = false;
    bool do_devpath     = false;
    bool do_manpath     = false;
    bool do_version     = false;

    // clang-format off
    struct optparse_long longopts[] = {{"sdkname", 's', OPTPARSE_REQUIRED},
                                       {"sdkpath", 'p', OPTPARSE_NONE},
                                       {"devpath", 'd', OPTPARSE_NONE},
                                       {"manpath", 'm', OPTPARSE_NONE},
                                       {"version", 'v', OPTPARSE_NONE},
                                       {"verbose", 'V', OPTPARSE_NONE},
                                       {"help", 'h', OPTPARSE_NONE},
                                       {0}};
    // clang-format on

    char *arg  = NULL;
    int option = -1;
    struct optparse options;

    optparse_init(&options, argv);
    while ((option = optparse_long(&options, longopts, NULL)) != -1) {
        switch (option) {
        case 's':
            sdkname = options.optarg;
            break;
        case 'p':
            do_sdkpath = true;
            break;
        case 'd':
            do_devpath = true;
            break;
        case 'm':
            do_manpath = true;
            break;
        case 'v':
            do_version = true;
            break;
        case 'V':
            verbose = true;
            break;
        case 'h':
            print_usage();
            return 0;
        default:
            fprintf(stderr, "%s: %s\n", getprogname(), options.errmsg);
            print_usage();
            return 1;
        }
    }

    if ((arg = optparse_arg(&options)) != NULL) {
        fprintf(stderr, "%s: got unknown trailing argument: '%s'\n", getprogname(), arg);
        print_usage();
        return 1;
    }

    printf("sdkname: '%s'\n", sdkname);
    printf("verbose: %s\n", BOOLSTR(verbose));
    printf("do_sdkpath: %s\n", BOOLSTR(do_sdkpath));
    printf("do_devpath: %s\n", BOOLSTR(do_devpath));
    printf("do_manpath: %s\n", BOOLSTR(do_manpath));
    printf("do_version: %s\n", BOOLSTR(do_version));

    if (do_sdkpath) {
        print_sdkpath(sdk);
    } else if (do_devpath) {
        print_devpath(verbose);
    } else if (do_manpath) {
        print_manpaths(sdkname);
    } else if (do_version) {
        print_version();
    }

    return 0;
}
