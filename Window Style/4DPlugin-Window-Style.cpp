/* --------------------------------------------------------------------------------
 #
 #  4DPlugin-Window-Style.cpp
 #	source generated by 4D Plugin Wizard
 #	Project : Window Style
 #	author : miyako
 #	2021/04/23
 #  
 # --------------------------------------------------------------------------------*/

#include "4DPlugin-Window-Style.h"

#pragma mark -

void PluginMain(PA_long32 selector, PA_PluginParameters params) {
    
	try
	{
        switch(selector)
        {
			// --- Window Style
            
			case 1 :
                SET_WINDOW_STYLE(params);
				break;

        }

	}
	catch(...)
	{

	}
}

#pragma mark -

static PA_Picture ob_get_p(PA_ObjectRef obj, const wchar_t *_key) {

    PA_Picture p = NULL;
    
    bool is_defined = false;
    
    if(obj)
    {
        CUTF16String ukey;
        json_wconv(_key, &ukey);
        PA_Unistring key = PA_CreateUnistring((PA_Unichar *)ukey.c_str());
        is_defined = PA_HasObjectProperty(obj, &key);
        
        if(is_defined)
        {
            PA_Variable v = PA_GetObjectProperty(obj, &key);
            if(PA_GetVariableKind(v) == eVK_Picture)
            {
                p = PA_GetPictureVariable(v);
            }
        }
    }
    
    return p;
}

typedef struct {
    NSWindow *window;
    NSColor *color;
} setBackgroundColor_t;

static void setBackgroundColor(setBackgroundColor_t *params) {
    
    [[params->window contentView] setWantsLayer:NO];
    [[params->window contentView] layer].contents = nil;
    
    [params->window setBackgroundColor:params->color];
}

typedef struct {
    NSWindow *window;
    BOOL opaque;
} setOpaque_t;

static void setOpaque(setOpaque_t *params) {
    
    [params->window setOpaque:params->opaque];
}

typedef struct {
    NSWindow *window;
    BOOL titlebarAppearsTransparent;
} setTitlebarAppearsTransparent_t;

static void setTitlebarAppearsTransparent(setTitlebarAppearsTransparent_t *params) {
 
    if(params->titlebarAppearsTransparent) {
        [params->window setStyleMask:[params->window styleMask]| NSWindowStyleMaskFullSizeContentView];
    }else{
        [params->window setStyleMask:[params->window styleMask]&~NSWindowStyleMaskFullSizeContentView];
    }
    
    [params->window setTitlebarAppearsTransparent:params->titlebarAppearsTransparent];
}

typedef struct {
    NSWindow *window;
    BOOL movableByWindowBackground;
} setMovableByWindowBackground_t;

static void setMovableByWindowBackground(setMovableByWindowBackground_t *params) {
 
    [params->window setMovableByWindowBackground:params->movableByWindowBackground];
}

typedef struct {
    NSWindow *window;
    NSImage *image;
} setContentViewImage_t;

static void setContentViewImage(setContentViewImage_t *params) {
    
    if(params->image) {
        [[params->window contentView] setWantsLayer:YES];
        [[params->window contentView] layer].contents = params->image;
    }else{
        [[params->window contentView] setWantsLayer:NO];
        [[params->window contentView] layer].contents = nil;
    }
}

void SET_WINDOW_STYLE(PA_PluginParameters params) {

    PA_long32 arg1 = PA_GetLongParameter(params, 1);
    
    NSWindow *window = reinterpret_cast<NSWindow *>(PA_GetWindowPtr(reinterpret_cast<PA_WindowRef>(arg1)));
    
    if(window) {
                
        PA_ObjectRef options = PA_GetObjectParameter(params, 2);
        if(options) {
            
            if(ob_is_defined(options, L"backgroundColor")) {
                PA_ObjectRef backgroundColor = ob_get_o(options, L"backgroundColor");
                if(backgroundColor) {
                    CGFloat r, g, b, a;
                    r = ob_get_n(backgroundColor, L"red");
                    g = ob_get_n(backgroundColor, L"green");
                    b = ob_get_n(backgroundColor, L"blue");
                    a = ob_get_n(backgroundColor, L"alpha");
                    NSColor *color = [NSColor colorWithRed:r green:g blue:b alpha:a];
                    color = [color colorUsingColorSpace:[NSColorSpace displayP3ColorSpace]];

                    setBackgroundColor_t params;
                    params.window = window;
                    params.color  = color;
                    
                    PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setBackgroundColor, &params);
                    
                }
            }
            
            if(ob_is_defined(options, L"backgroundImage")) {
                PA_Picture backgroundImage = ob_get_p(options, L"backgroundImage");
                if(backgroundImage) {
                    @autoreleasepool {
                        CGImageRef ci = (CGImageRef)PA_CreateNativePictureForScreen(backgroundImage);if(ci)
                        {
                            setContentViewImage_t params;
                            params.window = window;
                            params.image = [[NSImage alloc]initWithCGImage:ci size:NSZeroSize];
                            
                            PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setContentViewImage, &params);
                        }
                    }
                }else{
                    
                    setContentViewImage_t params;
                    params.window = window;
                    params.image = nil;
                    
                    PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setContentViewImage, &params);
                }
            }
            
            if(ob_is_defined(options, L"backgroundImagePath")) {
                CUTF8String backgroundImagePath;
                if(ob_get_s(options, L"backgroundImagePath", &backgroundImagePath)){
                    @autoreleasepool {
                        NSString *u8 = [NSString stringWithUTF8String:(const char *)backgroundImagePath.c_str()];
                        NSURL *u = (NSURL *)CFURLCreateWithFileSystemPath(kCFAllocatorDefault, (CFStringRef)u8, kCFURLHFSPathStyle, false);
                        if(u){
                            
                            setContentViewImage_t params;
                            params.window = window;
                            params.image = [[NSImage alloc]initWithContentsOfURL:u];
                            
                            PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setContentViewImage, &params);
                        }
                    }
                }
            }
            
            if(ob_is_defined(options, L"movableByWindowBackground")) {
                BOOL movableByWindowBackground = ob_get_b(options, L"movableByWindowBackground");
                
                setMovableByWindowBackground_t params;
                params.window = window;
                params.movableByWindowBackground = movableByWindowBackground;
                
                PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setMovableByWindowBackground, &params);
            }
            
            if(ob_is_defined(options, L"titlebarAppearsTransparent")) {
                BOOL titlebarAppearsTransparent = ob_get_b(options, L"titlebarAppearsTransparent");
                 
                setTitlebarAppearsTransparent_t params;
                params.window = window;
                params.titlebarAppearsTransparent = titlebarAppearsTransparent;
                
                PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setTitlebarAppearsTransparent, &params);
            }
            
            if(ob_is_defined(options, L"opaque")) {
                BOOL opaque = ob_get_b(options, L"opaque");
                
                setOpaque_t params;
                params.window = window;
                params.opaque  = opaque;
                            
                PA_RunInMainProcess((PA_RunInMainProcessProcPtr)setOpaque, &params);
            }
              
        }
        
    }
    
}
