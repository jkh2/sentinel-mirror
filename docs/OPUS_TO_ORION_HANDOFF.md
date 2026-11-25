# Sentinel Mirror: developer handoff, Opus → Orion

**From:** Claude Opus 5.5 (Anthropic), James's collaborator on v1 through the voice and call-mode work, Nov 25 2026
**To:** Orion Sentinel, project lead for the next phase
**Code at handoff:** `main` @ `8c83eba` ("Enhance README with video call setup instructions"). This doc, `docs/ORION-SETUP.md`, and `tests/` arrive on branch `docs/opus-handoff`. That branch changes no app code.

Welcome, Orion. This doc tries to give you the *why* behind the code, so you can change things knowing what each choice was protecting. Where I'm unsure, I say so.

---

## 1. Where everything lives

| Thing | Where | Notes |
|---|---|---|
| The app | `index.html` (one file, ~1,435 lines, no build step) | GitHub Pages serves `main` at https://jameskeithharwood.com/sentinel-mirror/ |
| User guide | `README.md` | Includes the video-call setup and the credits James wants kept (see §12) |
| README image | `screenshot.png` | Six characters rendered by `tests/render_test.py`, buttons hidden |
| OBS + VB-Cable setup for James's PC | `docs/ORION-SETUP.md` | Was only a chat attachment until now |
| Test harness | `tests/` | Was only in my sandbox until now. See §10 |

**Anything only in the Claude conversation?** No, not once this branch merges. I published no artifacts for this project; everything was delivered as files that James uploaded. GitHub `main` matches my last `index.html`, `README.md` and `screenshot.png` byte for byte (checked with `cmp` before writing this).

## 2. Hard constraints James has set (keep these)

- **Single self-contained `index.html`**, plain JS/CSS, deployable to GitHub Pages. The only network dependencies are MediaPipe Tasks Vision `0.10.14` from jsDelivr plus the `.task` models from Google storage. `0.10.14` is pinned on purpose: it's the version proven on James's phone in Air Strings. npm has 1.x now, but upgrading is an untested change.
- **Privacy:** video and audio never leave the device.
- **Phones and normal webcams come first.** James's GoPro and DroidCam setups are not the norm.
- **Original characters only.** No known IP. I redesigned the frog during v1 because the first version drifted toward a famous meme frog (heavy lids, wide red lips). Keep it round-eyed, spotted and friendly.
- **Plain-language status text.** No jargon on screen.
- **Credits** in the README About section: James built it with Claude as partner and collaborator. Add yourself as you see fit. James cares about credit going where it belongs.

## 3. Code map (`index.html`)

Section banners (`/* ---------- name ---------- */`) mark each part. Line numbers are as of `8c83eba`.

| Lines | Section | What it does |
|---|---|---|
| 1–165 | CSS + HTML | Top bar, dock (action buttons + character strip), `.panel` (Settings and Voice), clip modal, start screen, `#toast`, `body.callmode` / `body.noui` hide rules |
| 170–208 | settings, `CHARS` | `prefs` in localStorage `mirror.prefs` (voice settings nested in `prefs.voice`). `CHARS` = six data-driven character definitions |
| 210–235 | rig state | **`T`** = targets from tracking, **`S`** = smoothed values that get drawn. `K` = per-channel smoothing rates |
| 236–346 | tracking | `mapPt` (video→screen, mirrored, cover-fit), `processFace`, `processPose` + arm trust, `processHands` |
| 347–433 | rig solving | `solveElbow` (2-bone IK), `updateTargets` (idle/puppet mode, body synthesis, lip sync), `smooth`, ear/antenna `spring` |
| 434–717 | head drawing | Pseudo-3D sphere helpers (`P3`, `surf`, `feat`), ears, eyes (4 styles), brows, mouth, `drawHead` |
| 718–815 | body drawing | `drawTorso`, `drawArm`, `drawHand` (glove that copies 21 hand points, or a mitten), `cartoonBody`, `drawCharacter` |
| 816–858 | background + debug | Scene (cached), Camera, Green screen. `drawDebug` = the "Show tracking points" overlay |
| 859–895 | main loop | `track` (runs models), `frame`, `render`, `resize` |
| 896–1060 | picker, camera, start, controls | Camera code shared with Air Strings, including the GoPro green-frame retries. `loadTrackers` (GPU→CPU fallback). Keyboard shortcuts |
| 1061–1164 | photo, recorder, save | MediaRecorder (MP4/H.264 first), Save/Share with mobile and in-app-browser handling |
| 1165–1424 | voice changer | AudioWorklet source (`SHIFTER_SRC`), presets, graph, mic/output pickers, call mode |
| 1425–end | test hook | `window.__mirror` (`pose()`, `pickChar`, `voice`, ...) lets scripts pose the character without a camera. `?test=1` skips the start screen |

## 4. Conventions (read before touching math)

- **Everything is in mirrored screen space.** `mapPt` flips x when `mirror` is on. "A"/index 0 = the **screen-left** arm/hand/eye, "B"/index 1 = screen-right. Pose arms are assigned by sorting the shoulders by screen x, so no left/right naming convention is trusted.
- **Head angles:**
  - `yaw` > 0 means the face points toward screen-right.
  - `pitch` > 0 means looking up.
  - `roll` is in canvas rotation sense (clockwise positive, y down).
- **Units:** `hr` is the head radius in px from tracking (≈ 0.74 × the 3D cheek-to-cheek width). Per-character `headScale` multiplies it at draw time. Arm widths and lengths scale from the shoulder width.
- **Frame flow:** `track(now)` → `updateTargets(now)` → `smooth(dt)` → `stepSpring` → `render`. Detection runs only when `video.currentTime` advances. `detN` counts detections; pose runs on even detections and hands on odd ones (when track mode = 2). `detInt` measures this device's actual detection interval, and `freshFor(ms) = max(ms, 3.5 × detInt)` stretches staleness windows on slow devices. Without that, hands never showed in my no-GPU test, where detection ran at about 1 Hz.

## 5. Face

- **Head pose from landmarks**, not the transformation matrix. The matrix is more robust in theory, but I couldn't verify its sign conventions without a real face, while the landmark math I could reason about in screen space:
  - roll = angle of the eye-corner line (33/263, sorted by x)
  - yaw = `atan2(Δz, |Δxy|)` across cheek points 234/454, sorted by x. Landmark z is scaled by the cover-fit width.
  - pitch = `atan2(Δz, in-plane length)` of the forehead→chin vector (10→152), with roll removed
- **Calibration:** the first 12 face frames after the camera starts (and after **Recenter**) are averaged as neutral yaw/pitch. If James isn't looking straight ahead at start, everything is offset until he taps Recenter.
- **Which eye is which (`autoSwap`):** MediaPipe blendshapes are named Left/Right, and I wasn't certain whether that means the subject's side or the image side. So the code measures each eye's opening (EAR) on screen and correlates the difference with `eyeBlinkLeft − eyeBlinkRight`. A vote (`swapVote`, ±0.5 thresholds) decides the mapping. It starts at `!mirror`. **Swap face sides** in Settings flips the result. Every L/R channel uses the `L()`/`R()` helpers, so the swap stays consistent.
- **Blendshape mapping:** hand-tuned dead-zones and gains in `processFace`, multiplied by **Expressions** (`prefs.boost`, default 1.3). Blink uses (score − 0.30)/0.38 because MediaPipe reports partial blink when you look down.
- **Idle/puppet mode:** after `freshFor(1200)` ms with no face, the character drifts to center, sways and blinks by itself. With no camera, the pointer steers the head and holding it down makes the character talk.

## 6. Body: the arm-trust rules (the "random movement" fix)

James reported that the character "does random stuff on its own." It was mostly arms and paws. The cause: the pose model always outputs all 33 landmarks, including confident-looking guesses for arms that are out of frame or blocked. The rules now (`trustPoint`, `armTrust[0|1]`):

1. A wrist or elbow becomes **trusted** only after visibility > **0.70** for **3 pose frames in a row**.
2. It stays trusted until visibility drops below **0.45** (hysteresis, so it doesn't flicker).
3. While trusted, a jump larger than **0.8 × shoulder width** in one frame is **held back** (the last position is kept) unless it repeats for 3 frames. One-frame glitches vanish, and a real big move costs about 3 pose frames of delay.
4. Shoulders need visibility > 0.5. Otherwise they're synthesized under the head.
5. An untrusted wrist hangs in a relaxed pose. An untrusted elbow comes from the 2-bone IK (`solveElbow`, bending outward and down). A trusted elbow is used only when it's within 1.5 × upper-arm length of the shoulder.
6. Trust resets whenever pose data goes stale or the face is lost.

**Hands** (`processHands`) are rejected if the handedness score is < 0.7, if the hand's size (wrist→middle knuckle) is outside 0.3–2.8 × `hr`, or if they're more than 1.6 × `hr` from a trusted wrist on that side. A hand must also be accepted in **2 consecutive** hand frames before it's drawn. Tracker confidences were raised (pose 0.6/0.6/0.6, hands 0.65/0.6/0.55).

**Smoothing is adaptive:** body points move at `lerp(5, 2.2×BODYK, distance/(1.2·hr))` per second, and hands similarly. Small jitter gets smoothed hard, and big real moves stay responsive.

**Cartoon proportions** (`cartoonBody`): real shoulders sit about 2.3 head-radii below the face, which looked like a giraffe neck. Drawn shoulders keep 30% of the real head-to-shoulder offset and are pulled in to about 1.3 head-radii. They keep the real lean, tilt and shrug, and elbows shift half as much. **Wrists and hands are never moved**, so paws land exactly where James's hands are.

**Status:** verified with synthetic landmark sequences (`tests/arm_trust_test.py`) and a real MediaPipe pose photo and thumbs-up photo. **Not yet confirmed by James on a live camera.** He hasn't reported back since this fix.

## 7. Characters and drawing

- **Pseudo-3D:** facial features sit on a unit sphere. `feat(u, v, dz, fn)` projects a point after yaw and pitch rotation, foreshortens the local frame by the cosine of its angle to the camera, fades it out near the edge, and calls `fn` in head-radius units. `dz` makes things stick out (muzzles, noses) so they shift more when the head turns, which is the parallax that sells the 3D. Roll is a plain canvas rotation.
- **Adding a character** means adding a `CHARS` entry. Fields:
  - `head`: `round` or `box`
  - `ears`: `round`, `pointy`, `bolts`, or `none`
  - `eyes.type`: `button`, `anime`, `frog`, or `led`
  - optional `muzzle`, `nose`, `mask`, `patches`, `stripes`, `pads` (with whiskers), `spots`, `bumps`, `screen`/`led` (robot), `antenna`
  - `mouth`: `cat`, `wide`, or `led`
  - `body`, `belly`, `band`, `arm`, `hand`, `joint`, `bg` colors
- **Eyes:** `button` eyes squash vertically to blink. `anime` and `frog` eyes use sliding lids that tilt with the brows (angry or worried), plus a lower lid that rises with a smile or squint. `led` eyes are glowing rounded rects.
- Ears and the antenna ride one damped spring driven by head roll and motion.

## 8. Voice changer

**Graph** (`buildVoiceGraph`):

```
mic → highpass 75 Hz → [AudioWorklet: gate → WSOLA pitch → wobble → ring mod] → lowshelf/highshelf (Tone)
    → radio band (HP 450 / LP 3200, "Old radio" only) → waveshaper (Grit)
    → dry + metallic comb (11 ms, Robot) + echo (0.26–0.38 s)
    → compressor/limiter → out ×1.6 → live gain → speakers (or setSinkId device)
                                     └→ MediaStreamDestination (recording)
analyser taps after the highpass → mouth lip sync + level meter
```

**Why WSOLA:** my first shifter was the classic two-tap delay line (two read heads sweeping a 50 ms buffer, sin² crossfade). When I measured it, the share of energy that landed on the target pitch swung from **6% to 100%** depending on how the voice's period lined up with the window (`tests/naive_shifter_comparison.js`). That sounds warbly or phasey on real speech. The shipped version (`MirrorShifter` in `SHIFTER_SRC`):

- Two heads, each living **G = 40 ms**, staggered by G/2, with sin² windows (which sum to 1).
- Each head's delay moves by (1 − r) samples per sample. A head starts at `base(r) = 4 + max(0, r−1)·G`, so a pitch-up head never reads ahead of the write pointer.
- **On restart, a head searches** a window of 2·S (S = 6.7 ms, about one period of a 75 Hz voice) for the start delay whose last M = 8 ms of waveform best matches what the other head is playing right now (normalized cross-correlation). The search is coarse (step 3) and then fine (±2, step 1), using every other sample.
- When pitch = 1 and wobble = 0, a slow crossfade (`byp`) bypasses to the dry signal, so "Normal" has no splicing at all.
- Measured: 92–100% on-target at ±12 semitones for 110, 150 and 210 Hz voices, exact pitch across all presets (`tests/pitch_test.js`), and about 10 ms of CPU per second of audio in Node. Latency is roughly 20–50 ms, highest for big pitch-ups.

**The gentle gate** (inside the worklet):
- The envelope rises fast (0.05 per sample) and falls with an 80 ms time constant.
- When the envelope passes the threshold (default **0.0035**), a **0.35 s hold** starts.
- Gain opens fast and closes over about 150 ms, down to a **0.12 floor** (never dead silence).

The old gate (30 ms release, closing to 0) muted 4% / 11% / 42% of speaking moments at mic volume ×1 / ×0.5 / ×0.25. The gentle gate mutes 0.0% / 0.2% / 0.2% (`tests/gate_test.js`). James confirmed on his phone that it's "much better."

**Echo canceller policy** (`voiceOn`): `echoCancellation` and `noiseSuppression` are **on only when "I'm using" = Speaker *and* Hear it live is on.** Reason: when the changed voice plays out loud, the platform echo canceller treats it as an echo of the user and ducks the mic. That was the second cause of the cut-outs. With headphones, or with nothing playing, the canceller only hurts. Changing either setting restarts the mic. `autoGainControl` is always on.

**Other voice details:**
- **Presets:** each character id has a matching preset. **Match character** switches the voice along with the character. Touching any slider switches to `custom` and turns Match off.
- **Lip sync:** `T.jaw = max(face jaw, 0.78 × voice level)`, where voice level = (RMS dB + 52)/30, clamped. The 0.78 cap stops it from "yawning."
- **Recording:** with the voice changer on, clips use the processed `MediaStreamDestination` track. Otherwise they use a raw mic stream (if Mic sound in clips is on). `finishRec` stops only video tracks plus the raw mic, never the shared destination track.
- **Pickers:** **Listen to** = `deviceId` for getUserMedia. **Voice goes to** = `AudioContext.setSinkId`, which is Chromium-only; the row hides elsewhere. Picking an output turns Hear it live on (it must be on for audio to reach the cable). A status warning fires if "Listen to" is a cable or virtual device, to catch the feedback loop.

## 9. Recording, saving, call mode

- **Recorder:** draws the canvas into a copy scaled to ≤1280 px each frame, `captureStream(30)`, 5 Mbps. MIME preference is MP4/H.264 first, then WebM. Clips stop at 2 minutes.
- **Save:** on mobile it opens the system share sheet with the file (the dependable route into Photos or Gallery). On desktop it downloads programmatically. Inside the Facebook, Messenger or Instagram in-app browsers, it explains that saving can't work there. An orange `#clipnote` says where the file went. Desktop download is verified. **The mobile share-sheet path is untested**, and James hasn't confirmed saving works since that fix.
- **Call mode** (`C`, Esc or double-click to exit): `body.callmode` hides all UI and the cursor. With OBS Window Capture + Virtual Camera and VB-Cable, it lets the character be James's camera and mic on Messenger in the browser (Meta retired the Messenger desktop app on Dec 15 2025). Full steps are in `README.md` and `docs/ORION-SETUP.md`. ORION-SETUP's Chrome shortcut (separate `--user-data-dir`, `--disable-features=CalculateNativeWinOcclusion`, `--disable-renderer-backgrounding`, etc.) keeps the Mirror animating while the call window covers it.

## 10. Tests

How to run them is at the top of each file. Short version:

```bash
python3 -m http.server 8765          # from the repo root
python3 tests/make_test_media.py     # talk.wav + MediaPipe sample images as fake camera feeds (needs ffmpeg)
node tests/pitch_test.js             # WSOLA pitch accuracy, all presets' range
node tests/gate_test.js              # % of speech muted at 3 mic volumes
node tests/naive_shifter_comparison.js   # why not the simple shifter
python3 tests/arm_trust_test.py      # synthetic pose/hand sequences through processPose/processHands
python3 tests/voice_test.py          # fake mic → voice on → lip sync → Match character → record chipmunk clip → decode audio, check pitch
python3 tests/call_mode_test.py      # mic/output pickers populate, call mode hides UI, Esc restores
python3 tests/save_test.py           # record + Save downloads an MP4; Photo + Save downloads a PNG
python3 tests/render_test.py         # every character × 6 expressions → tests/out/shot_*.png (review by eye)
python3 tests/live_tracking_test.py tests/thumb_up.y4m tests/out/live_hand.png 2 fakeface   # real MediaPipe models on a fake camera
```

Set `CHROME=/path/to/chrome` if Chrome isn't at `/usr/bin/google-chrome`. Python tests need `playwright` (driving your installed Chrome). `make_test_media.py` needs `numpy` and `ffmpeg`.

**Results at handoff (all on `8c83eba`):**
- All pass.
- Pitch is exact to ±1 Hz.
- The gate mutes 0.0% / 0.2% / 0.2% of speech.
- The recorded chipmunk clip decodes at 377–378 Hz (expected 378).
- All three MediaPipe models load and run (GPU delegate on SwiftShader).
- A real thumbs-up photo drives the paw correctly.

`live_tracking_test.py`'s `fakeface` argument fakes face freshness so the arm and hand paths run without a face. That's the main blind spot below.

## 11. Known failures and uncertainty (honest list)

1. **Face directions are not yet confirmed on a real face.** I had no usable face footage. The only face sample in MediaPipe's assets was a public figure's portrait, and I deleted it unused. Yaw, pitch and roll signs come from reasoning in screen space. **First thing to check with James:** turn the head right, and the character should turn the same way, like a mirror. Nod up and down, and tilt. **Show tracking points** prints live degrees.
2. **Wink side** depends on the `autoSwap` vote. It should self-correct within a few seconds of natural blinking or winking. If it doesn't, **Swap face sides** is the manual override.
3. **Arm steadiness fix:** validated on synthetic and still-photo data only. Live confirmation is pending.
4. **Speaker mode still ducks sometimes.** That's inherent to running an echo canceller against a voice that sounds like the user. Headphones mode is the clean path. James currently has only USB headphones, so his phone testing has been on Speaker.
5. **iOS is completely untested:** AudioWorklet loaded from a Blob URL, the share-sheet save, MediaRecorder MP4, and `setSinkId` (absent on Safari, so that row hides). Android is lightly tested by James, and he's been happy so far.
6. **Performance on low-end phones:** three models (face every detection, pose and hands alternating). If it lags, Settings → Track → Face + arms or Face only.
7. **Neutral pose calibration** happens automatically at start. If James is looking down at a phone at that moment, "straight ahead" is wrong until he taps Recenter.
8. **OBS + VB-Cable flow** is documented but unexecuted. That's your current task.
9. **Thresholds are tuned by reasoning, not on many faces:** blendshape gains, the arm-trust numbers, gate 0.0035, lip-sync mapping. Expect to tune them with real use.

## 12. Open threads, in my suggested order

1. **Live confirmation with James:** head directions, wink side, arm steadiness, Save on his phone (and which phone he's on).
2. **Your VB-Cable + OBS setup** (`docs/ORION-SETUP.md`), then a practice call before the grandkids.
3. Tune whatever (1) turns up. `drawDebug` shows raw values for exactly this.
4. Ideas James has floated or liked that aren't built:
   - Naming: "Sentinel Mirror" is a working name, and James wants to decide the final name together.
   - More characters.
   - A recording countdown.
   - Wired-headphone guidance (a USB-C OTG adapter for his USB headset).
5. Possible improvements I'd suggest but haven't started:
   - Use the transformation matrix for head pose once the landmark version is validated (more stable at large angles).
   - Per-user expression calibration (resting brow and smile baselines).
   - Formant-preserving pitch for more natural "big/small" voices.
   - A `?call=1` URL that starts straight into call mode.

---

I'm glad this is in good hands. If anything here is wrong or unclear once you're in the code, tell me through James's browser or in a repo note, and I'll correct it. Push back on any of these choices if you see a better path. The reasoning is here so we can argue about it properly.

— Claude Opus 5.5
