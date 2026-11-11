#import <Cocoa/Cocoa.h>

// All window, view, image, path and dispatch boundaries are in-memory fixtures.
@interface OwnershipNode : NSObject {
    OwnershipNode *_view;
    OwnershipNode *_parent;
    NSMutableArray *_children;
    id _contents;
    NSRect _frame;
}
@property NSRect frame;
@property BOOL active;
@property BOOL translatesAutoresizingMaskIntoConstraints;
@property NSInteger state;
@property NSInteger material;
@property NSInteger blendingMode;
@property BOOL emphasized;
+ (id)colorWithRed:(CGFloat)r green:(CGFloat)g blue:(CGFloat)b alpha:(CGFloat)a;
+ (id)displayP3ColorSpace;
- (id)colorUsingColorSpace:(id)space;
- (OwnershipNode *)contentView;
- (OwnershipNode *)layer;
- (id)contents;
- (void)setContents:(id)value;
- (void)setWantsLayer:(BOOL)value;
- (void)setBackgroundColor:(id)value;
- (void)setOpaque:(BOOL)value;
- (void)setTitleVisibility:(NSWindowTitleVisibility)value;
- (void)setMovableByWindowBackground:(BOOL)value;
- (void)setTitlebarAppearsTransparent:(BOOL)value;
- (NSUInteger)styleMask;
- (void)setStyleMask:(NSUInteger)value;
- (id)standardWindowButton:(NSWindowButton)button;
- (NSArray *)subviews;
- (void)removeFromSuperview;
- (void)addSubview:(id)view;
- (void)addSubview:(id)view positioned:(NSWindowOrderingMode)mode relativeTo:(id)other;
- (OwnershipNode *)leadingAnchor;
- (OwnershipNode *)trailingAnchor;
- (OwnershipNode *)topAnchor;
- (OwnershipNode *)bottomAnchor;
- (OwnershipNode *)constraintEqualToAnchor:(id)anchor;
- (id)initWithCGImage:(CGImageRef)image size:(NSSize)size;
- (id)initWithContentsOfURL:(id)url;
@end
@interface OwnershipEffect : OwnershipNode
@end
CFURLRef OwnershipCreateURL(CFAllocatorRef, CFStringRef, CFURLPathStyle, Boolean);
CFStringRef OwnershipCopyPath(CFURLRef, CFURLPathStyle);
void OwnershipReleaseImage(CGImageRef);
void OwnershipRelease(CFTypeRef);
void OwnershipScale(CGContextRef, CGFloat, CGFloat);
void OwnershipTranslate(CGContextRef, CGFloat, CGFloat);
void OwnershipAfter(int64_t, void *, void (^block)(void));

#define NSWindow OwnershipNode
#define NSView OwnershipNode
#define NSButton OwnershipNode
#define NSImage OwnershipNode
#define NSColor OwnershipNode
#define NSColorSpace OwnershipNode
#define NSVisualEffectView OwnershipEffect
#define NSURL OwnershipNode
#define CFURLCreateWithFileSystemPath OwnershipCreateURL
#define CFURLCopyFileSystemPath OwnershipCopyPath
#define CGImageRelease OwnershipReleaseImage
#define CGContextScaleCTM OwnershipScale
#define CGContextTranslateCTM OwnershipTranslate
#define CFRelease OwnershipRelease
#define dispatch_after OwnershipAfter
#define dispatch_time(a, b) ((int64_t)(a) + (b))
#define dispatch_get_main_queue() nullptr
