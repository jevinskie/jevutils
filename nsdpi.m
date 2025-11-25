#include <AppKit/NSScreen.h>
#ifndef __APPLE__
#error dsc-info is only for Apple platforms
#endif

#import <AppKit/AppKit.h>
#import <Foundation/Foundation.h>

int main() {
    int i = 0;
    for (NSScreen *screen in NSScreen.screens) {
        NSDictionary *description  = screen.deviceDescription;
        NSSize displayPixelSize    = [description[NSDeviceSize] sizeValue];
        CGSize displayPhysicalSize = CGDisplayScreenSize([description[@"NSScreenNumber"] unsignedIntValue]);
        printf("screen[%d]: %0.2f dpi\n", i, 25.4 * displayPixelSize.width / displayPhysicalSize.width);
        ++i;
    }
    return 0;
}
