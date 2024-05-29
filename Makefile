TARGETS := fsgetpath-util dsc-info nsdpi dump-fixups net-privesc

ifeq ($(shell uname -s),Darwin)
TARGETS += nsdpi dsc-info
endif

C_CXX_FLAGS := -Wall -Wextra
C_FLAGS := $(C_CXX_FLAGS) -std=gnu17
OBJC_FLAGS := $(C_FLAGS) -fobjc-arc
CXX_FLAGS := $(C_CXX_FLAGS) -std=gnu++20

all: $(TARGETS)


.PHONY: clean

clean:
	rm -rf *.dSYM/
	rm -f $(TARGETS)

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
endif

net-privesc: net-privesc.c
	$(CC) -o $@ $^ $(NET_PRIVESC_C_FLAGS)
	sudo chown root:root $@
	sudo chmod u+s $@
	sudo chmod g+s $@
