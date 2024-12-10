TARGETS := fsgetpath-util dump-fixups net-privesc byte-histogram env-var-path-search

ifeq ($(shell uname -s),Darwin)
TARGETS += nsdpi dsc-info jevxcselect
endif

C_CXX_FLAGS := -Wall -Wextra -Wpedantic
C_FLAGS := $(C_CXX_FLAGS) -std=gnu2x
OBJC_FLAGS := $(C_FLAGS) -fobjc-arc
CXX_FLAGS := $(C_CXX_FLAGS) -std=gnu++2b

all: $(TARGETS)


.PHONY: clean

clean:
	rm -rf *.dSYM/
	rm -f $(TARGETS)

%: %.c
	$(CC) -o $@ $^ $(C_FLAGS)

%: %.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS)

%: %.m
	$(CC) -o $@ $^ $(OBJC_FLAGS) -framework Foundation

nsdpi: nsdpi.m
	$(CC) -o $@ $^ $(OBJC_FLAGS) -framework Foundation -framework AppKit

fsgetpath-util: fsgetpath-util.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS)

dsc-info: dsc-info.cpp
	$(CXX) -o $@ $^ $(CXX_FLAGS) -arch x86_64 -arch arm64 -arch arm64e

dump-fixups: dump-fixups.cpp
	env PKG_CONFIG_PATH="$(shell brew --prefix)/opt/fmt/pkgconfig" $(CXX) -o $@ $^ $(CXX_FLAGS) $(shell pkg-config pkg-config --libs fmt --cflags)

ifneq ($(shell uname -s),Darwin)
NET_PRIVESC_C_FLAGS = $(C_FLAGS) -lcap-ng
NET_PRIVESC_GROUP = tcpdump
NET_PRIVESC_SETCAP = sudo setcap cap_net_bind_service,cap_net_broadcast,cap_net_admin,cap_net_raw,cap_sys_admin,cap_bpf+eip $@
else
NET_PRIVESC_GROUP = wheel
NET_PRIVESC_SETCAP =
endif

net-privesc: net-privesc.c
	$(CC) -o $@ $^ $(NET_PRIVESC_C_FLAGS)
	sudo chown root:$(NET_PRIVESC_GROUP) $@
	sudo chmod u+s $@
	sudo chmod g+s $@
	$(NET_PRIVESC_SETCAP)

byte-histogram: byte-histogram.c
	$(CC) -o $@ $^ $(C_FLAGS)

jevxcselect: jevxcselect.c
	$(CC) -o $@ $^ $(C_FLAGS) -lxcselect
