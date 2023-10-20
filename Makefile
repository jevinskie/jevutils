TARGETS := fsgetpath-util

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
	$(CXX) -o $@ $^ $(CXX_FLAGS)
