# Window Style ownership audit

## Provenance and complete native inventory

Baseline: `0381474c54fc218cb9a6eb1ff92ff00b50984e7f` on `main`.
Guidance was read through the GitHub API from
`miyako/skills@e6b492fcb81e5e1a7f7db723594b420e63bf6eb9`,
`4d-skills/skills/4dplugin/SKILL.md`.
The synthetic harness is adapted, not its results copied, from
`miyako/4d-plugin-window-control-v2@fc60c3dd6f196d62948dda3536611eb9ff3594d9`.
No extra checkout, native project build or SDK replacement is involved.

Both tracked command manifests declare exactly one command,
`SET WINDOW STYLE(&L;&J)`, not thread-safe: a scalar window reference and an
options object, no text-array command parameters. Text and picture values are
inside that object. The dormant array wrapper is included, not excluded by
this manifest inventory.

Every tracked native implementation at baseline:

| Implementation | Baseline Git blob | Production membership |
|---|---|---|
| `4DPlugin-Window-Style.cpp` | `4f3feb6a5982a1d81c0b6e3a16360750d81047ea` | Xcode; legacy VS lists it but has no viable Windows implementation |
| `support/4DPlugin-JSON.cpp` | `a5122d68e881476b97332a6a4f40a7b3e3adeb3f` | Xcode; not listed in VS |
| `4D Plugin API/4DPluginAPI.c` | `62f745e91d81ef2c3c901c656ea8e175d3b173e8` | Xcode and VS |
| `Classes/ARRAY_TEXT.cpp` | `534855e0959020ce9a66cef08f8434799c174495` | Dormant; compiled by harness |
| `Classes/C_BLOB.cpp` | `27bea3172ce90e4da339991c9b318a71ea8609b2` | Dormant; compiled by harness |
| `Classes/C_LONGINT.cpp` | `005b83a4aec2c1466b8b219cb27ab845eb58de91` | Dormant; compiled by harness |
| `Classes/C_TEXT.cpp` | `45ea6432dff52b681a5c6a7cea58ad5fc15df66b` | Dormant; compiled by harness |

`Classes/` above is under `4D Plugin API/`. Baseline wrapper headers:
`ARRAY_TEXT.h` = `cf8a458fc8519b824c726a59d346c44d4c26e845`,
`C_BLOB.h` = `d181534e5a2e9bd46de492a040c1538ed81bf45a`,
`C_LONGINT.h` = `71e24df633aed7155cba1ffddc07d6a1dfc12fa9`,
`C_TEXT.h` = `6967390757db569ffcd3cfea8696bf14045cc748`,
`C_TYPES.h` = `972cf3f597a8c21881a8c9aa69bc1699455be373`.
`4DPlugin-Window-Style.h` =
`4a7d41813887caf00e327dfd104cda5b5db53f39`; JSON header =
`80aa1f1332655244c4ad4ff09197cb38dcd63912`.
All wrapper members, including Objective-C string/path members, compile in
the harness; path functions are synthetic. There is no `CPicture` class,
`createCopy` picture converter or plugin-owned collection-element helper in
this target. Their presence in another repository is not evidence here.

The bundled SDK calls itself `rev : v14`; this is not a verified upstream
release identification. The complete implementation is compiled unchanged,
including its internal string/object/collection/callback/array helpers.
Protected SDK/ABI blobs:

| File under `4D Plugin API/` | Git blob |
|---|---|
| `4DPluginAPI.h` | `528bf1d2552df08d6a8b1bc95011a9b72934ad5c` |
| `4DPluginAPI.def` | `5bbdb82fb724b6f8e307feb01d9f158b802de89d` |
| `EntryPoints.h` | `da428d5f6ca23b0a30371c7288a01d29aa3c466a` |
| `Flags.h` | `7a5a35539f27430a3fd9cb711d6b789051316471` |
| `PrivateTypes.h` | `a3098cb662cdbc43ba574fdef72a059c4c6d1cd4` |
| `PublicTypes.h` | `9ae20b001bff9128f690fff3e6c3f873b6238333` |

The `.def` exports only `FourDPackex`; the full SDK forwards that entry to
the actual `PluginMain`, whose only command case is selector 1. No other
tracked native source exists. `include/json/` contains third-party JSON
headers; its tracked macOS/Windows libraries contain no plugin-source
ownership fix and are preserved byte-for-byte, as are all prebuilt bundles.
The tracked 4D demo methods/forms, generated trash methods and binary data
are not executed or opened by these tests.

## Source-derived contracts and changes

SDK line numbers below refer to the immutable baseline.

* `PA_CreateVariable(eVK_Unistring)` (4030) creates an owned empty string;
  `PA_SetStringVariable` (4254-4259) overwrites it by shallow assignment.
  All four JSON string setters now initialize Undefined before assigning
  their sole owned string. Their final variable cleanup remains, including
  failed property assignment. The picture setter similarly avoids losing
  its automatically allocated empty picture.
* `PA_GetObjectProperty` (637-653) explicitly requires clearing its returned
  variable. Scalar helpers now clear successful values of every tested kind,
  including mismatches. Matching object/collection helpers still hand the
  owned reference to their caller without clearing it; their wrong-kind
  results are cleared. The dispatcher releases backgroundColor/vibrance
  object handoffs after their final use.
* Private `ob_get_p` now disposes its key on missing/present paths, retains
  the matching picture using `PA_DuplicatePicture(p, 1)`, then clears the
  successful result variable. The SDK maps retain-only to engine param1=0
  (487-498). The dispatcher releases this owner after native conversion,
  including null native-image output. A failed retain is checked before
  adopting its unspecified return. The native-image creation/release pair
  and existing NSImage/layer reference handling remain intact.
* Getter and command errors are captured immediately, before kind
  normalization/adoption/cleanup. Raw failed `fType=0` is not Undefined:
  the SDK can normalize it to a string. Failed poison/zero-filled returns
  must not be interpreted or cleared. `ob_stringify` now obtains the full
  OB Copy result rather than hiding a wrong-kind owned result inside
  `PA_DuplicateObject`, checks its error/kind, then cleans its independent
  synchronous command argument and successful return at the right times.
* ARRAY_TEXT/C_BLOB own raw heap pointers with deleting destructors.
  Four named baseline copy/assignment probes produce ASan heap-use-after-free.
  Both are now noncopyable, matching the existing C_TEXT prior art. No
  production copy call was found: these are latent dormant-wrapper defects,
  not a demonstrated production window crash. The actual consumers compile.
* CBytes output replacement now allocates/copies first and releases the old
  caller handle only on success. Its injected allocation-failure case keeps
  the exact original handle, capacity, bytes and error indication.

`PA_SetStringInArray` (4933-4947) is unchanged: accepted destination requires
Unicode array kind, non-null data, index `0 <= i <= fNbElements`, non-null
descriptor. It disposes the old element and shallow-transfers the supplied
allocation. Index zero is valid in this SDK. Rejection retains caller
ownership; no post-transfer disposal is added. `PA_GetStringInArray`
(4738-4755) is borrowed. ARRAY_TEXT already copies getter content before
subsequent array mutation; normal-path transfer is retained.

Scalar C_TEXT parameter/return setters use the engine content setter,
not array descriptor transfer. Their independent copies remain independently
disposable. UTF-16 lengths/capacities are code units excluding the terminator;
CoreFoundation UTF-8 conversion reports bytes. Exact ASCII, BMP, supplementary
surrogate-pair and empty content is asserted. There is no target-specific
picture BYTES-to-CUTF16String-UNITS converter to patch.

## Reproducible evidence

Run the three commands in the README on macOS with Python standard library
and Apple Clang. No Python packages are required. Initial local provenance:
Python 3.12.12, Apple Clang 21.0.0, arm64-apple-darwin25.6.0.
The new narrowly filtered CI job uses `macos-latest`; no native release
scripts or project phases are called.

The identical final harness is compiled against immutable `git archive`
baseline and fixed actual sources, not SDK fragments or substituted wrappers.
ASan and UBSan are enabled; packed legacy SDK alignment checks alone are
disabled. LeakSanitizer is disabled on macOS, with explicit final zero
string, picture, handle, object/collection and platform owner balances
instead. Every unsafe baseline copy must name the ASan heap-use-after-free
diagnostic. Null and allocated engine empties are distinct fixtures.

| Named leaf group | Baseline leaves | Expected baseline failures | Passing controls |
|---|---:|---:|---:|
| Four string setters, including rejected property assignment | 40 | 20 | 20 |
| Picture setter, including rejected property assignment | 3 | 3 | 0 |
| `get-a` | 16 | 11 | 5 |
| `get-b` | 16 | 10 | 6 |
| `get-n` | 16 | 10 | 6 |
| `get-c` | 16 | 8 | 8 |
| `get-o` | 16 | 8 | 8 |
| Stringify/copy command success, wrong kind, error and failed argument allocation | 23 | 10 | 13 |
| Actual repeated dispatcher | 28 | 22 | 6 |
| Array transfer/rejection/churn and all four wrappers | 16 | 0 | 16 |
| Handle allocation/resize failure predicates | 1 | 0 | 1 |
| Caller blob handle preserved on allocation failure | 1 | 1 | 0 |
| Copy traits | 1 | 1 | 0 |
| Four baseline-only unsafe copy/assignment probes | 4 | 4 | 0 |
| Missing/null inputs and non-string setter controls | 3 | 0 | 3 |
| **Total** | **200** | **108** | **92** |

Fixed: **196/196 leaves pass**, excluding only the four deliberately unsafe
baseline-copy probes. Six additional preservation tests check the complete
native inventory, both manifests, all other baseline files, SDK/ABI and
build memberships, existing automation, and the exact minimal new workflow.

Dispatcher fixtures cover successful/mismatched strings, pictures, objects,
collections, booleans and numbers; poison/raw-zero getter errors; retain
failure; null native-image creation; absent options, window and properties;
and synthetic path/image conversion. Each dispatcher leaf repeats three
times. Engine callbacks reject every unexpected selector. Objective-C
window/view/color/image classes, path conversion, native picture resources,
drawing calls and asynchronous dispatch are replaced before compilation.
Dynamic imports are gated before execution: unexpected UI classes,
graphics/path/event/dispatch and process/file/network entry points fail.
Ordinary NSString/NSArray/NSPredicate and CFString conversions are in-memory.
Synthetic view containment retains its children and layer content.

## Limits and concretely deferred contracts

This is not a real 4D host, native Windows ABI validation, Cocoa rendering or
a Windows crash reproduction. Windows helper branches receive an additional
syntax-only compile with rejecting converter stubs; the actual window
dispatcher is macOS-only and is never represented as a Windows implementation.
No real UI/settings, input capture/injection, private user data, image files,
4D demo database, signing credentials or platform state are accessed.
The synchronous synthetic dispatch cannot validate asynchronous window
lifetime or real visual-effect positioning semantics.

The public command still returns nothing, keeps its existing catch/default
behavior and does not add a worker throw, error channel or success report.
Missing/wrong-kind scalar getters retain their original default/output
conventions; `ob_get_a` still returns existence, not conversion success.
On failed SDK return, the unspecified value is not cleaned as if owned.
Existing lack of user-facing error reporting and cleanup calls overwriting
last-error remain explicit limitations, not a new success-shaped API.

SDK OOM is **not certified** by successful fixture runs.
`PA_ResizeArray` (4564-4612) can dispose truncated elements and then change
`fNbElements` even if handle resize fails. ARRAY_TEXT depends on that metadata;
safe transactional shrink/grow behavior requires a verified engine/SDK
contract, not a guessed metadata rollback. Initial Unicode array creation
also performs lock/unlock after allocation, which can overwrite the error.
These SDK failure-preservation cases are deferred without SDK/header edits.
The harness tests the underlying failed handle allocation/resize predicates,
not safe ARRAY_TEXT behavior after those SDK failures. No pointer/reference
constructor metadata has been invented. Legacy C++ allocator exceptions and
unspecified engine allocation returns are not made reliable by this patch.

Existing Bump/Build workflows are manual-only. Native shell scripts and the
Xcode Deployment phase can sign, package, notarize and publish; the audit does
not execute them, dispatch/rerun them or alter them. Projects, resources,
manifests, version metadata, libraries and tracked binaries remain unchanged.
