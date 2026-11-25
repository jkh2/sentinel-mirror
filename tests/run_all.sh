#!/usr/bin/env bash
# Runs every check (not the diagnostics) and exits 1 if any fail. Needs the repo served on :8765 (or MIRROR_URL)
# and tests/make_test_media.py run once.
cd "$(dirname "$0")/.." || exit 1
fails=()
run(){ echo; echo "=== $*"; if "$@"; then :; else fails+=("$*"); fi; }
run node tests/pitch_test.js
run node tests/gate_test.js
run python3 tests/arm_trust_test.py
run python3 tests/voice_test.py
run python3 tests/call_mode_test.py
run python3 tests/save_test.py
run python3 tests/render_test.py
run python3 tests/live_tracking_test.py --video tests/thumb_up.y4m --fake-face --expect-hand
echo
if [ ${#fails[@]} -eq 0 ]; then echo "ALL CHECKS PASSED"; else printf 'FAILED: %s\n' "${fails[@]}"; exit 1; fi
