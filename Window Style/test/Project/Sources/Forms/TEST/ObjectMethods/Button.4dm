$style:=New object:C1471
$style.opaque:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419086-opaque?language=objc
$style.titlebarAppearsTransparent:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419167-titlebarappearstransparent?language=objc
$style.movableByWindowBackground:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419072-movablebywindowbackground?language=objc
$style.backgroundColor:=New object:C1471
$style.backgroundColor.red:=0.8
$style.backgroundColor.green:=0.1
$style.backgroundColor.blue:=0.3
$style.backgroundColor.alpha:=1  //

SET WINDOW STYLE(Current form window:C827; $style)