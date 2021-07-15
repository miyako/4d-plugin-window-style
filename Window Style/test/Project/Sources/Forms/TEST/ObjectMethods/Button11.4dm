$style:=New object:C1471
//$style.opaque:=True  //https://developer.apple.com/documentation/appkit/nswindow/1419086-opaque?language=objc

$style.titlebarVisible:=False:C215  //https://developer.apple.com/documentation/appkit/nswindowtitlevisibility/nswindowtitlehidden

$style.backgroundColor:=New object:C1471
$style.backgroundColor.red:=0.8
$style.backgroundColor.green:=0.1
$style.backgroundColor.blue:=0.3
$style.backgroundColor.alpha:=1

SET WINDOW STYLE(Current form window:C827; $style)