// clang -o nsdpi nsdpi.m -framework Foundation -framework AppKit

#import <AppKit/AppKit.h>
#import <Foundation/Foundation.h>

int main() {
    NSScreen *screen          = NSScreen.mainScreen;
    NSDictionary *description = screen.deviceDescription;
    NSSize displayPixelSize   = [description[NSDeviceSize] sizeValue];
    CGSize displayPhysicalSize =
        CGDisplayScreenSize([description[@"NSScreenNumber"] unsignedIntValue]);
    printf("%0.2f\n", 25.4 * displayPixelSize.width / displayPhysicalSize.width);
    return 0;
}