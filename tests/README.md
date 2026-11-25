# Sentinel Mirror tests

Two kinds of scripts live here. Every script prints its raw measurements first.

- **Checks** also print `PASS`/`FAIL` for each criterion and **exit 1 if any fail**.
- **Diagnostics** only print measurements, for a human to read. They never fail.

Each check's criteria are written in its docstring. All the checks have been mutation-tested: deliberately breaking the
code they guard makes them fail (see the handoff doc).

| Script | Kind | Covers |
|---|---|---|
| `pitch_test.js` | check (portable, Node only) | WSOLA pitch accuracy at ±12 semitones, level kept, silence stays silent |
| `gate_test.js` | check (portable, Node only) | the gentle gate mutes ≤ 1% of speech at three mic volumes |
| `arm_trust_test.py` | check (browser) | arm and hand trust rules on synthetic tracker frames |
| `voice_test.py` | check (browser) | voice on, lip sync, Match character, recorded clip carries the shifted pitch |
| `call_mode_test.py` | check (browser) | mic and output pickers, Call mode hides everything, Esc restores |
| `save_test.py` | check (browser) | desktop Save downloads the clip and the photo (the phone share sheet is not testable here) |
| `render_test.py` | check + visual review | all 36 character × expression renders actually draw; **looks** are reviewed by eye in `tests/out/` |
| `live_tracking_test.py` | smoke check (browser) | the real MediaPipe models load and run on a fake camera; a hand reaches the character. **Face tracking is not covered** (no usable face sample) |
| `naive_shifter_comparison.js` | diagnostic | why the simple delay-line shifter was dropped |
| `make_test_media.py` | helper | makes `talk.wav` and the fake camera feeds |

## Running

```bash
python3 -m http.server 8765            # from the repo root, in its own terminal
python3 tests/make_test_media.py       # once (needs numpy, ffmpeg, internet)
bash tests/run_all.sh                  # every check; exits 1 if any fail
node tests/pitch_test.js               # or run any one script by itself
```

The browser checks need Python `playwright` and drive your installed Chrome. Set `CHROME=/path/to/chrome` if it isn't at
`/usr/bin/google-chrome`, and `MIRROR_URL` to test a different server.
