TARGETS := dump-fixups net-privesc byte-histogram env-var-path-search basenice find-macho

ifeq ($(shell uname -s),Darwin)
TARGETS += nsdpi dsc-info jevxcselect fsgetpath-util xnu-arm64-dump-tsd xnu-dump-image-activation-stack
endif

C_CXX_FLAGS := -g -Wall -Wextra -Wpedantic -Wno-nullability-extension -Wno-gnu-statement-expression-from-macro-expansion -I 3rdparty/optparse-wrapper
C_FLAGS := $(C_CXX_FLAGS) -std=gnu2x
OBJC_FLAGS := $(C_FLAGS) -fobjc-arc
CXX_FLAGS := $(C_CXX_FLAGS) -std=gnu++2b

all: $(TARGETS)

.PHONY: clean-targets clean-compile-commands clean compile_commands.json scan

clean-targets:
	rm -rf *.dSYM/
	rm -f $(TARGETS)

clean-compile-commands:
	rm -f compile_commands.json

clean: clean-targets clean-compile-commands

compile_commands.json:
	bear -- $(MAKE) -B -f $(MAKEFILE_LIST) RUNNING_BEAR=1
	$(MAKE) -f $(MAKEFILE_LIST) clean-targets

scan:
	scan-build -V $(MAKE) -B -f $(MAKEFILE_LIST)

%: %.c
	$(CC) -o $@ $^ $(C_FLAGS)

%: %.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS)

%: %.m
	$(CC) -o $@ $^ $(OBJC_FLAGS) -framework Foundation

nsdpi: nsdpi.m
	$(CC) -o $@ $^ $(OBJC_FLAGS) -framework Foundation -framework AppKit

dsc-info: dsc-info.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS) -arch x86_64 -arch arm64 -arch arm64e

dump-fixups: dump-fixups.cpp
	env PKG_CONFIG_PATH="$(shell brew --prefix)/opt/fmt/pkgconfig" $(CXX) -o $@ $^ $(CXX_FLAGS) $(shell pkg-config pkg-config --libs fmt --cflags)

ifneq ($(shell uname -s),Darwin)
NET_PRIVESC_C_FLAGS = $(C_FLAGS) -lcap-ng
NET_PRIVESC_GROUP = tcpdump
NET_PRIVESC_SETCAP = sudo setcap cap_net_bind_service,cap_net_broadcast,cap_net_admin,cap_net_raw,cap_sys_admin,cap_bpf+eip $@
else
NET_PRIVESC_C_FLAGS = $(C_FLAGS)
NET_PRIVESC_GROUP = admin
NET_PRIVESC_SETCAP =
endif

net-privesc: net-privesc.c
	rm -f $@
	$(CC) -o $@ $^ $(NET_PRIVESC_C_FLAGS)
ifneq ($(RUNNING_BEAR),1)
	sudo chown root:$(NET_PRIVESC_GROUP) $@
	sudo chmod u+s $@
	sudo chmod g+s $@
	$(NET_PRIVESC_SETCAP)
	sudo -k
endif

jevxcselect: jevxcselect.c
	$(CC) -o $@ $^ $(C_FLAGS) -lxcselect

find-macho: find-macho.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS) -O3 -I 3rdparty/thread-pool/include

xnu-dump-image-activation-stack: xnu-dump-image-activation-stack.c
	$(CC) -o $@ $^ $(C_FLAGS)
