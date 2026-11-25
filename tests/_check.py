"""Tiny shared helper: print each check as PASS/FAIL and exit nonzero if any failed."""
import sys
_fails = []
def check(ok, label, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + label + (f'  ({detail})' if detail != '' else ''))
    if not ok: _fails.append(label)
    return ok
def finish():
    if _fails:
        print(f'\n{len(_fails)} check(s) FAILED: ' + '; '.join(_fails)); sys.exit(1)
    print('\nAll checks passed.')
def page_errors(logs):
    """Real problems only. Ignored: the missing favicon (a harmless 404 on a local server) and MediaPipe's own
    informational logs, which it prints through console.error (e.g. "INFO: Created TensorFlow Lite XNNPACK delegate")."""
    noise = ('favicon', 'status of 404', 'INFO:', 'XNNPACK', 'gl_context', 'Graph successfully')
    return [l for l in logs if not any(n in l for n in noise)]
