"""Generate tiny test clips with planted defects (Law 4). Deterministic, ffmpeg-only,
so the repo stays light — regenerate with `python tests/make_fixtures.py`.

Clips (2s, 1080×1920 to match the ad output aspect):
  th_a.mp4, th_b.mp4  — colour + tone talking-head stand-ins, healthy stereo
  mono.mp4            — MONO audio (A6: must become stereo)
  one_ear.mp4         — stereo with a SILENT right channel (issue #14 / A6)
"""
from __future__ import annotations
import subprocess
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"


def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def color_clip(path: Path, color: str, freq: int, layout: str, silent_right=False):
    a_src = f"sine=frequency={freq}:sample_rate=48000"
    filt = []
    if layout == "mono":
        a_out = ["-ac", "1"]
    elif silent_right:
        # left = tone, right = silence → a genuine one-ear defect
        filt = ["-filter_complex",
                f"[1:a]pan=stereo|c0=c0|c1=c0[full];[full]pan=stereo|c0=c0|c1=0.0*c0[a]"]
        a_out = []
    else:
        a_out = ["-ac", "2"]
    cmd = ["ffmpeg", "-y",
           "-f", "lavfi", "-i", f"color=c={color}:s=1080x1920:d=2:r=30",
           "-f", "lavfi", "-i", f"{a_src}:duration=2"]
    if filt:
        cmd += filt + ["-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"] + a_out
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
            "-shortest", str(path)]
    _run(cmd)


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    color_clip(FIX / "th_a.mp4", "0x1e6f5c", 220, "stereo")
    color_clip(FIX / "th_b.mp4", "0x8a3ffc", 330, "stereo")
    color_clip(FIX / "mono.mp4", "0xcc4422", 440, "mono")
    color_clip(FIX / "one_ear.mp4", "0x3355cc", 550, "stereo", silent_right=True)
    print(f"fixtures → {FIX}")


if __name__ == "__main__":
    main()
