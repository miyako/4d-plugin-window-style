$style:=New object:C1471
$style.opaque:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419086-opaque?language=objc
$style.titlebarAppearsTransparent:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419167-titlebarappearstransparent?language=objc
$style.movableByWindowBackground:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419072-movablebywindowbackground?language=objc

$path:=Folder:C1567(fk resources folder:K87:11).file("test.png").platformPath

READ PICTURE FILE:C678($path; $image)

$style.backgroundImage:=$image

SET WINDOW STYLE(Current form window:C827; $style)