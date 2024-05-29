// Copyright (c) 2022-2024 Jevin Sweval <jevinsweval@gmail.com>
// SPDX-License-Identifier: BSD-2-Clause

// gcc -o net-privesc net-privesc.c -lcap-ng
// sudo setcap cap_net_raw,cap_net_bind_service,cap_net_broadcast,cap_bpf+eip net-privesc

#include <errno.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef __APPLE__
#include <error.h>
#else
/*
 * Copyright (C) 2015 The Android Open Source Project
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */
#include <stdarg.h>
#include <stdlib.h>
unsigned int error_message_count   = 0;
void (*error_print_progname)(void) = NULL;
int error_one_per_line             = 0;

static void __error_head() {
    ++error_message_count;

    if (error_print_progname != NULL) {
        error_print_progname();
    } else {
        fflush(stdout);
        fprintf(stderr, "%s:", getprogname());
    }
}

static void __error_tail(int status, int error) {
    if (error != 0) {
        fprintf(stderr, ": %s", strerror(error));
    }

    putc('\n', stderr);
    fflush(stderr);

    if (status != 0) {
        exit(status);
    }
}

void error(int status, int error, const char *fmt, ...) {
    __error_head();
    putc(' ', stderr);

    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);

    __error_tail(status, error);
}
#endif

#ifdef __linux__
#include <sys/prctl.h>

#include <cap-ng.h>

void add_ambcap(int ambcap) {
    int res = -1;

    capng_get_caps_process();
    res = capng_update(CAPNG_ADD, CAPNG_INHERITABLE, ambcap);
    if (res) {
        error(1, res, "couldn't add ambcap %d to inheritable set", ambcap);
    }
    capng_apply(CAPNG_SELECT_CAPS);
    res = prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, ambcap, 0, 0);
    if (res) {
        error(2, res, "couldn't add ambcap %d a.k.a. %s to ambient set", ambcap,
              capng_capability_to_name(ambcap));
    }
}
#endif

int main(int argc, char *const *argv) {
    int res = -1;

    if (argc < 2) {
        error(3, ENOENT, "must provide a binary, e.g. %s <full path to run binary>",
              dirname(strdup(argv[0])));
    }

#ifdef __linux__
// #ifdef CAP_NET_BIND_SERVICE
//     add_ambcap(CAP_NET_BIND_SERVICE);
// #endif
// #ifdef CAP_NET_BROADCAST
//     add_ambcap(CAP_NET_BROADCAST);
// #endif
#ifdef CAP_NET_ADMIN
    add_ambcap(CAP_NET_ADMIN);
#endif
#ifdef CAP_NET_RAW
    add_ambcap(CAP_NET_RAW);
#endif
// #ifdef CAP_BPF
//     add_ambcap(CAP_NET_RAW);
// #endif
#endif

#ifdef __linux__
    res = execvp(argv[1], &argv[1]);
#else
    res = execvp("sudo", &argv[1]);
#endif

    if (res) {
        error(4, errno, "bad execv of %s", argv[1]);
    }

    return 0;
}
