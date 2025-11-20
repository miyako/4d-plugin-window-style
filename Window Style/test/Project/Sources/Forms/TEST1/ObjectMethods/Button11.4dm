$style:=New object:C1471
//$style.opaque:=True  //https://developer.apple.com/documentation/appkit/nswindow/1419086-opaque?language=objc

Form:C1466.isHidden:=Not:C34(Bool:C1537(Form:C1466.isHidden))

If (Bool:C1537(Form:C1466.isHidden))
	
	$style.titlebarVisible:=False:C215  //https://developer.apple.com/documentation/appkit/nswindowtitlevisibility/nswindowtitlehidden
	$style.titlebarAppearsTransparent:=True:C214  //https://developer.apple.com/documentation/appkit/nswindow/1419167-titlebarappearstransparent?language=objc
	$style.x:=6
	$style.y:=6
	
Else 
	
	$style.titlebarVisible:=True:C214  //https://developer.apple.com/documentation/appkit/nswindowtitlevisibility/nswindowtitlehidden
	$style.titlebarAppearsTransparent:=False:C215  //https://developer.apple.com/documentation/appkit/nswindow/1419167-titlebarappearstransparent?language=objc
	$style.x:=-6
	$style.y:=-6
	
End if 

SET WINDOW STYLE(Current form window:C827; $style)