# Setup handoff for Orion Sentinel: Sentinel Mirror video calls

Hi Orion. This is Claude, James's collaborator on Sentinel Mirror. James asked me to write up this setup for you to carry out on his Windows computer.

## What we're building

Sentinel Mirror (https://jameskeithharwood.com/sentinel-mirror/, repo `jkh2/sentinel-mirror`) is a single-page web app. It turns James's webcam and mic into a cartoon character (teddy bear, fox, robot, and others) that copies his face, arms and hands, and speaks with a voice changer.

The goal is for James to video call his grandkids on Facebook Messenger (in the browser at facebook.com or messenger.com, since Meta retired the desktop app in December 2025) and have them **see the cartoon and hear the cartoon voice** instead of James. Here's how the pieces connect:

```
Webcam + James's USB headset mic
        │
        ▼
Sentinel Mirror (its own Chrome window)
   ├── picture ──► OBS Window Capture ──► OBS Virtual Camera ──► Messenger camera
   └── voice  ──► "CABLE Input" (VB-Cable) ──► "CABLE Output" ──► Messenger microphone
```

OBS Studio is already installed. The VB-Cable installer is in James's **Downloads** folder.

## Ground rules

- Ask James before anything that needs administrator rights, a restart, or a change to his default audio devices. Some steps need him to click a Windows prompt.
- Don't uninstall or change anything unrelated to this setup.
- When you finish, report back to James with the checklist at the bottom, marking anything that didn't work.

---

## Step 1: Install VB-Cable

1. In `%USERPROFILE%\Downloads`, find the VB-Cable download. It's usually a zip named like `VBCABLE_Driver_Pack45.zip` (the number may differ). Extract it to its own folder, for example `%USERPROFILE%\Downloads\VBCABLE`.
2. The installer is `VBCABLE_Setup_x64.exe` (64-bit Windows). It must run **as Administrator**:
   - From an elevated shell you can try a quiet install: `VBCABLE_Setup_x64.exe -i -h`
   - If that doesn't work on this version, launch it normally as Administrator. James clicks **Yes** on the Windows prompt, then **Install Driver** in the VB-Audio window.
3. **Ask James before restarting.** VB-Audio says a restart is needed after installing.
4. After the restart, confirm the driver exists:
   ```powershell
   Get-PnpDevice -FriendlyName "*VB-Audio*" | Format-Table Status, Class, FriendlyName
   ```
   You should see **CABLE Input (VB-Audio Virtual Cable)** (playback) and **CABLE Output (VB-Audio Virtual Cable)** (recording), with Status `OK`.

## Step 2: Make sure Windows didn't switch James's default audio

Windows sometimes makes a new audio device the default. If CABLE Input becomes the default speaker, James hears nothing. If CABLE Output becomes the default mic, his apps hear nothing.

1. Check the defaults. One way:
   ```powershell
   Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser
   Get-AudioDevice -List | Format-Table Index, Default, Type, Name
   ```
2. The **default playback** device should be James's real headphones or speakers (his USB headset when it's plugged in). The **default recording** device should be his real mic. Neither should be a CABLE device.
3. If either one is a CABLE device, tell James and, with his OK, set it back (`Set-AudioDevice -Index <n>`), or have him do it in **Settings → System → Sound**.

## Step 3: A dedicated Sentinel Mirror window that never freezes

Chrome pauses windows that are completely covered, so the cartoon would freeze when the Messenger window is on top. Running the Mirror as its own Chrome instance, with background throttling turned off, fixes that. Because it gets its own profile folder, the flags apply even when James's normal Chrome is already open.

Create a desktop shortcut named **Sentinel Mirror** with:

- **Target** (adjust the chrome.exe path if Chrome lives elsewhere):
  ```
  "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%LOCALAPPDATA%\SentinelMirrorChrome" --app=https://jameskeithharwood.com/sentinel-mirror/ --window-size=1280,760 --disable-features=CalculateNativeWinOcclusion --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows
  ```
- **Start in:** `C:\Program Files\Google\Chrome\Application`

Opening it gives a clean window, with no tabs or address bar, titled **Sentinel Mirror**. The first time, James taps **Start** and allows the camera and mic. That profile remembers the permissions.

## Step 4: Set up OBS

Use whichever route works. Route A is fully automatic; Route B is a quick click-through for James.

### Route A: automatic, through OBS WebSocket (OBS 28 or newer)

1. James enables it in OBS: **Tools → WebSocket Server Settings → Enable WebSocket server**. He shares the port (default 4455) and password with you.
2. Open the Sentinel Mirror window from Step 3, so OBS can see it.
3. Using `obsws-python` (`pip install obsws-python`) or a similar client:
   - Create a scene named **Sentinel Mirror**.
   - Add an input named **Mirror Window** of kind `window_capture` to that scene.
   - Get the exact value for its `window` setting with `GetInputPropertiesListPropertyItems(inputName="Mirror Window", propertyName="window")`. Choose the item whose name starts with `[chrome.exe]: Sentinel Mirror`, then set it with `SetInputSettings`. Using the list's own value avoids guessing the format.
   - Set the capture method to **Windows 10 (1903 and up)** (Windows Graphics Capture). Chrome windows often show black with the older method. If you're unsure of the settings key, read `GetInputSettings` after setting it in the OBS window once.
   - Make the picture fill the frame: `SetSceneItemTransform` with `boundsType: OBS_BOUNDS_SCALE_INNER` and the bounds set to the canvas size (`GetVideoSettings`). Or have James right-click the source → **Transform → Fit to screen**.
   - Make **Sentinel Mirror** the current program scene.
4. If the canvas isn't 1280×720 or 1920×1080, suggest 1280×720 to James (**Settings → Video**). It's a good size for calls.

### Route B: manual, for James in OBS

1. Open the Sentinel Mirror window (Step 3).
2. In OBS, under **Scenes**, click **+** and name it **Sentinel Mirror**.
3. Under **Sources**, click **+** → **Window Capture**, name it **Mirror Window**, and pick **[chrome.exe]: Sentinel Mirror**. Set **Capture Method** to **Windows 10 (1903 and up)**. Uncheck **Capture Cursor**.
4. Right-click the source → **Transform → Fit to screen**.

### Then, either way: a one-click "Mirror Camera" shortcut

Create a desktop shortcut named **Mirror Camera** that opens OBS on that scene with the virtual camera already running:

- **Target:**
  ```
  "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --scene "Sentinel Mirror" --startvirtualcam --minimize-to-tray
  ```
- **Start in:** `C:\Program Files\obs-studio\bin\64bit` (OBS won't start correctly without this.)

The first time the virtual camera starts, Windows may ask for permission. James clicks **Yes**.

## Step 5: Test it together with James

1. James puts on his USB headset.
2. He opens **Sentinel Mirror** (desktop shortcut), taps **Start**, picks a character, and taps **🎙 Voice**. In the Voice panel:
   - **Listen to:** his real headset mic (not CABLE)
   - **I'm using:** Headphones
   - **Voice goes to:** CABLE Input (VB-Audio Virtual Cable)
   - **Hear it live:** on
3. He taps **📺 Call mode**, so only the character shows.
4. He opens **Mirror Camera** (desktop shortcut).
5. In his normal Chrome, he opens a test page such as https://webcamtests.com or https://www.onlinemictest.com:
   - Camera: **OBS Virtual Camera** should show the cartoon, moving with him.
   - Mic: **CABLE Output (VB-Audio Virtual Cable)** should pick up the cartoon voice as he talks.
6. For a real call, he opens Messenger at facebook.com or messenger.com, starts a video call, and in the call's settings picks:
   - **Camera:** OBS Virtual Camera
   - **Microphone:** CABLE Output (VB-Audio Virtual Cable)
   - **Speaker:** his headset

   If the call has no device menu, set them in Chrome: **Settings → Privacy and security → Site settings → Camera** and **Microphone**.

## If something goes wrong

| Problem | Likely fix |
|---|---|
| OBS shows a black window | Capture method → **Windows 10 (1903 and up)**. Make sure the Mirror window isn't minimized (covered is fine with the Step 3 shortcut, but minimized is not). |
| Cartoon freezes when the call window is on top | The Mirror wasn't opened from the Step 3 shortcut, or normal Chrome was already running with the Mirror inside it. Close it and reopen from the shortcut. |
| They hear James's normal voice | Messenger is using the real mic. Pick **CABLE Output** in the call or in Chrome's site settings. |
| They hear nothing | In the Mirror's Voice panel, **Voice goes to** must be **CABLE Input** and **Hear it live** must be on. |
| James hears nothing at all on his computer | Windows made CABLE Input the default speaker. Set his headset or speakers back as the default (Step 2). |
| "OBS Virtual Camera" missing in Chrome | Start the virtual camera in OBS first, then reload the Messenger page. |

## Report back to James

- [ ] VB-Cable installed, CABLE Input and CABLE Output present
- [ ] Default playback and recording devices are still his real devices
- [ ] **Sentinel Mirror** desktop shortcut created (separate Chrome instance, no throttling)
- [ ] OBS scene **Sentinel Mirror** with **Mirror Window** capture, fit to screen
- [ ] **Mirror Camera** desktop shortcut created (starts the virtual camera)
- [ ] Test page shows the cartoon on OBS Virtual Camera
- [ ] Test page hears the cartoon voice on CABLE Output

Thank you, Orion. Once this works, James can make the grandkids laugh with a talking teddy bear. Questions about how the Mirror app works can go back to James and me.
