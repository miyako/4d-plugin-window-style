$style:=New object:C1471
  //$style.vibrance:=True
$style.vibrance:=New object:C1471()
  // $style.vibrance.emphasized:=False  // https://developer.apple.com/documentation/appkit/nsvisualeffectview/1644721-emphasized?language=objc
$style.vibrance.state:=1  // https://developer.apple.com/documentation/appkit/nsvisualeffectstate?language=objc
$style.vibrance.material:=3  // https://developer.apple.com/documentation/appkit/nsvisualeffectmaterial?language=objc 
$style.vibrance.blendingMode:=0  // https://developer.apple.com/documentation/appkit/nsvisualeffectblendingmode?language=objc

SET WINDOW STYLE (Current form window:C827;$style)