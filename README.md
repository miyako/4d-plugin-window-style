![version](https://img.shields.io/badge/version-20%2B-E23089)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-window-style)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-window-style/total)

# 4D Plugin: Window Style

Customizes the appearance of a 4D process window on macOS: background color, a background picture (from a `Picture` variable or a file on disk), whether the window can be dragged by its background, a transparent/full-size-content titlebar, window opacity, whether the title text is shown, and macOS's translucent "vibrancy" effect. It drives Cocoa/AppKit APIs (`NSWindow`, `CALayer`, `NSVisualEffectView`) directly against the window you already have open in 4D.

There is exactly one exposed command, `SET WINDOW STYLE`, which takes a window reference plus a single options object — every visual effect is applied by including the corresponding key in that object.

| Command | Returns | Purpose |
|---|---|---|
| [`SET WINDOW STYLE`](#set-window-style) | (none) | Apply one or more style options to an open window |

**Platforms:** macOS only (Intel and Apple Silicon). There is no Windows implementation.

---

## Requirements & platform notes

- **macOS only.** This plugin has no `VERSIONWIN` code path at all — there is no Windows build, and none is planned as part of this plugin's design.
- **The window must already exist and be open** — pass the reference of a window 4D already created (e.g. via `Current window` or `OPEN WINDOW`). If the reference doesn't resolve to a real window, the command does nothing; no 4D error is raised.
- **All options are optional, and unknown/missing keys are simply ignored.** You can pass an object with just the one or two keys you care about — you don't need to specify every style property on every call.
- **No return value.** `SET WINDOW STYLE` is fire-and-forget: there is no way to detect success or failure from 4D. Always confirm changes visually or through your own test pass.
- **Options are applied in this order on every call:** `backgroundColor`, `backgroundImage`, `backgroundImagePath`, `movableByWindowBackground`, `titlebarAppearsTransparent`, `opaque`, `titlebarVisible`, `vibrance`. This matters if you supply more than one background-related key in the same object — see [Error handling](#error-handling--troubleshooting).

---

## SET WINDOW STYLE

### Syntax

```4d
SET WINDOW STYLE(window; options)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | Reference of the target window (e.g. the result of `Current window`) |
| `options` | Object | One or more of the style keys described below |
| Result | — | No return value |

### Options object

| Property | Type | Description |
|---|---|---|
| `backgroundColor` | Object | `{red; green; blue; alpha}`, each a number from `0` to `1`. Sets the window's background color (rendered in the Display P3 color space). Also clears any background picture set on this window by a *previous* call. |
| `backgroundImage` | Picture | Draws the picture as the window's background, behind its content. Pass an empty/undefined `Picture` to clear a previously-set background image. |
| `backgroundImagePath` | Text | Loads an image file from disk and uses it as the background, as an alternative to `backgroundImage`. If both `backgroundImage` and `backgroundImagePath` are present in the same call, `backgroundImagePath` is applied last and wins. |
| `movableByWindowBackground` | Boolean | When `true`, the user can drag the window by clicking anywhere on its background (not just the titlebar). |
| `titlebarAppearsTransparent` | Boolean | When `true`, hides the titlebar's visual bar and lets your content extend underneath it (`NSWindowStyleMaskFullSizeContentView`). See the caveat below. |
| `x` | Number | Only read when `titlebarAppearsTransparent` is present. Horizontal offset applied to the close/minimize/zoom buttons; positive moves them right. Read from the *top level* of `options`, not nested under `titlebarAppearsTransparent`. |
| `y` | Number | Only read when `titlebarAppearsTransparent` is present. Vertical offset applied to the close/minimize/zoom buttons; positive moves them down. Also top-level. |
| `opaque` | Boolean | Sets whether the window is opaque (`false` allows transparency to show through, e.g. combined with a translucent `backgroundColor` alpha). |
| `titlebarVisible` | Boolean | Shows (`true`) or hides (`false`) the title **text** specifically — see the caveat below, this does not hide the titlebar bar itself or its buttons. |
| `vibrance` | Boolean or Object | `false`/omitted object properties deactivate any active vibrancy. Pass `true` to activate with default settings, or an object `{state; material; blendingMode; emphasized}` for full control — see below. |
| `vibrance.state` | Number | Raw integer value of an AppKit `NSVisualEffectState` constant. |
| `vibrance.material` | Number | Raw integer value of an AppKit `NSVisualEffectMaterial` constant. |
| `vibrance.blendingMode` | Number | Raw integer value of an AppKit `NSVisualEffectBlendingMode` constant. |
| `vibrance.emphasized` | Boolean | Corresponds to `NSVisualEffectView.emphasized`. |

### Description

Each key in `options` is independent and optional — the plugin checks for each one individually and applies only the ones you provide, in the fixed order listed under [Requirements](#requirements--platform-notes).

**`backgroundColor`** replaces the window's `NSWindow.backgroundColor` and, as a side effect, disables and clears any layer-backed background image the window may have had from an earlier `backgroundImage`/`backgroundImagePath` call. Color components are plain `0`–`1` floats per channel, interpreted in the Display P3 color space rather than sRGB — for exact color matching against a design tool, account for this when picking values.

**`backgroundImage`** and **`backgroundImagePath`** both work by turning the window's content view into a layer-backed view and setting the picture as the layer's `contents`. This draws *behind* whatever else is on the window — form objects, controls, etc. — so it works well as a decorative backdrop but will be fully obscured by any opaque object placed over it.

**`titlebarAppearsTransparent`** is the option most likely to surprise you: turning it on switches the window into "full size content view" mode, meaning your form's content view is resized to extend up underneath the titlebar area. Existing form objects positioned near the top of the window can end up visually behind or overlapping the traffic-light buttons. The `x`/`y` offsets exist specifically to nudge the traffic lights back into a comfortable position once this happens; you'll typically need to tune these by eye for your specific window layout. Turning the option back off automatically reverses the offset direction, so you don't need to pass negated `x`/`y` values yourself to undo it.

**`titlebarVisible`** only toggles the title *text* (`NSWindow.titleVisibility`) — the titlebar bar, and the close/minimize/zoom buttons, remain exactly as they were regardless of this setting. If you want an entirely bare titlebar, combine this with `titlebarAppearsTransparent`.

**`vibrance`** adds (or removes) a full-size `NSVisualEffectView` behind the window's existing content, producing macOS's frosted-glass translucency effect. The `state`, `material`, and `blendingMode` values are passed straight through as raw integers to the corresponding AppKit enums — this plugin doesn't validate or translate them, so an out-of-range value produces whatever `NSVisualEffectView` itself does with an invalid raw value (typically it's silently clamped/ignored rather than crashing, but this isn't a documented plugin-level guarantee). Check Apple's `NSVisualEffectView` reference for the exact numeric values for `NSVisualEffectState`, `NSVisualEffectMaterial`, and `NSVisualEffectBlendingMode` on your deployment target's macOS version, since the material list in particular has grown and been partially deprecated across OS releases.

### Example

```4d
// Tinted, semi-transparent background
var $window : Integer
var $options : Object

$window:=Current window

$options:=New object
$options.backgroundColor:=New object
$options.backgroundColor.red:=0.12
$options.backgroundColor.green:=0.12
$options.backgroundColor.blue:=0.16
$options.backgroundColor.alpha:=0.92
$options.opaque:=False

SET WINDOW STYLE($window; $options)
```

```4d
// Borderless-looking, background-draggable window with a picture backdrop
var $window : Integer
var $options : Object

$window:=Current window

$options:=New object
$options.backgroundImage:=$myBackdropPicture  // a Picture variable
$options.movableByWindowBackground:=True
$options.titlebarAppearsTransparent:=True
$options.x:=4
$options.y:=2
$options.titlebarVisible:=False

SET WINDOW STYLE($window; $options)
```

```4d
// Vibrancy / frosted-glass background
var $window : Integer
var $options : Object; $vibrance : Object

$window:=Current window

$vibrance:=New object
$vibrance.material:=0  // NSVisualEffectMaterialTitlebar — check Apple's docs for the value you need
$vibrance.blendingMode:=0  // NSVisualEffectBlendingModeBehindWindow
$vibrance.state:=1  // NSVisualEffectStateActive
$vibrance.emphasized:=False

$options:=New object
$options.vibrance:=$vibrance

SET WINDOW STYLE($window; $options)

// ...later, to turn it back off:
$options:=New object
$options.vibrance:=False
SET WINDOW STYLE($window; $options)
```

---

## Error handling & troubleshooting

- **No feedback on failure.** `SET WINDOW STYLE` never raises a 4D error and has no return value. If nothing visibly changed, check the window reference and the options object's key names/types rather than expecting an error to surface.
- **An invalid or closed window reference is a silent no-op.** Nothing happens; no error, no crash.
- **An empty or entirely-unrecognized `options` object is also a silent no-op.** Double-check key spelling — there's no validation or "unknown key" warning.
- **Setting `backgroundColor` on a window that already has a background image clears the image**, since color and image share the same underlying layer. If you want both a tinted background *and* an image, set `backgroundColor` first and `backgroundImage`/`backgroundImagePath` in a later, separate call — or include both keys in the same call, since `backgroundColor` is always applied before the image keys within a single call.
- **If both `backgroundImage` and `backgroundImagePath` are supplied in the same call, `backgroundImagePath` wins** (it's applied second, unconditionally overwriting whatever `backgroundImage` set).
- **`titlebarVisible:false` does not remove the titlebar or its buttons** — only the title text. Combine with `titlebarAppearsTransparent` for a fully bare look.
- **Turning on `titlebarAppearsTransparent` can visually overlap your form content with the traffic-light buttons.** Use `x`/`y` to reposition the buttons, and expect to tune these per window/form.
- **`backgroundImagePath` expects a file-system path** — if the image doesn't load, verify the exact path string format your 4D version is passing (the plugin's internal path resolution has historically assumed a legacy HFS-style path on this code path rather than a POSIX `/`-separated one; if a POSIX path silently fails to load, this internal path-style handling is the first thing to check).
- **`vibrance` numeric fields are unvalidated raw AppKit enum values.** An unsupported value for your target macOS version won't error from the plugin — it's passed straight to Cocoa. Verify against Apple's current `NSVisualEffectView` documentation, not against values you find in older sample code.
- **Not marked thread-safe in the plugin's manifest**, but this doesn't require anything extra on the 4D side — call it like any other command; the plugin marshals its window changes to the main thread internally.

---

## Quick reference

```4d
var $w : Integer; $o : Object

$w:=Current window

// Background color + opacity
$o:=New object
$o.backgroundColor:=New object
$o.backgroundColor.red:=1; $o.backgroundColor.green:=1; $o.backgroundColor.blue:=1; $o.backgroundColor.alpha:=1
$o.opaque:=True
SET WINDOW STYLE($w; $o)

// Background image from a Picture variable
$o:=New object
$o.backgroundImage:=$myPicture
SET WINDOW STYLE($w; $o)

// Background image from a file path
$o:=New object
$o.backgroundImagePath:=$myPath
SET WINDOW STYLE($w; $o)

// Draggable, borderless-style titlebar
$o:=New object
$o.movableByWindowBackground:=True
$o.titlebarAppearsTransparent:=True
$o.x:=0; $o.y:=0
$o.titlebarVisible:=False
SET WINDOW STYLE($w; $o)

// Vibrancy on/off
$o:=New object
$o.vibrance:=True   // or an object: {state; material; blendingMode; emphasized}
SET WINDOW STYLE($w; $o)

$o:=New object
$o.vibrance:=False
SET WINDOW STYLE($w; $o)
```
