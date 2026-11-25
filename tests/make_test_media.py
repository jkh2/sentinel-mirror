"""Makes the fake mic and camera inputs the browser checks use (not a test itself).
talk.wav: speech-like 200 Hz bursts (0.4 s on, 0.2 s off) for the voice tests.
thumb_up.y4m / pose.y4m: MediaPipe's own sample images as fake camera feeds (needs ffmpeg and internet).
Run: python3 tests/make_test_media.py"""
import pathlib, subprocess, urllib.request, wave
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
sr=48000; t=np.arange(sr*6)/sr; f0=200
x=sum(np.sin(2*np.pi*f0*h*t)/h for h in range(1,7))*0.25
env=np.convolve(((t%0.6)<0.4).astype(float),np.ones(480)/480,'same')
y=(x*env*32767*0.8).astype(np.int16)
with wave.open(str(HERE/'talk.wav'),'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
for name in ['thumb_up','pose']:
    jpg=HERE/(name+'.jpg')
    if not jpg.exists(): urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-assets/'+name+'.jpg', jpg)
    subprocess.run(['ffmpeg','-loglevel','error','-y','-loop','1','-i',str(jpg),'-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white','-t','2','-r','15','-pix_fmt','yuv420p',str(HERE/(name+'.y4m'))],check=True)
print('made talk.wav, thumb_up.y4m, pose.y4m in', HERE)
