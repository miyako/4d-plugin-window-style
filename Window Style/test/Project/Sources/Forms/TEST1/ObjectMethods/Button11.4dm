$style:=New object:C1471
//$style.opaque:=True  //https://developer.apple.com/documentation/appkit/nswindow/1419086-opaque?language=objc

$style.titlebarVisible:=False:C215  //https://developer.apple.com/documentation/appkit/nswindowtitlevisibility/nswindowtitlehidden
$style.titlebarAppearsTransparent:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419167-titlebarappearstransparent?language=objc

SET WINDOW STYLE(Current form window:C827; $style)