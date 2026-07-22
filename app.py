import os
import uuid
import json
import shutil
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_VIDEO = {"mp4", "mov", "mkv", "avi", "webm", "m4v"}
ALLOWED_AUDIO = {"mp3", "wav", "m4a", "aac", "ogg"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024


def ext_ok(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def run_cmd(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-4000:])
    return proc.stdout


def ffmpeg_exists():
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def media_duration(path):
    out = run_cmd([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ])
    return float(out.strip())


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def transcribe_to_srt(video_path, srt_path, model_size="small", language="vi"):
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError(
            "Chưa cài faster-whisper. Hãy chạy: pip install -r requirements.txt"
        ) from exc

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(video_path), language=language or None, vad_filter=True, beam_size=5
    )
    lines = []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        if not text:
            continue
        lines.append(str(i))
        lines.append(f"{srt_time(seg.start)} --> {srt_time(seg.end)}")
        lines.append(text)
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    return getattr(info, "language", language)


def escape_filter_path(path):
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def build_video(job_id, video_path, music_path, options):
    output_path = OUTPUT_DIR / f"{job_id}_final.mp4"
    srt_path = OUTPUT_DIR / f"{job_id}.srt"

    start = max(0.0, float(options.get("start", 0) or 0))
    end_raw = options.get("end")
    end = float(end_raw) if end_raw not in (None, "") else None
    speed = min(2.0, max(0.5, float(options.get("speed", 1) or 1)))
    ratio = options.get("ratio", "original")
    flip = options.get("flip") == "true"
    mute_original = options.get("mute_original") == "true"
    add_subtitles = options.get("add_subtitles") == "true"
    watermark = (options.get("watermark") or "").strip()
    subtitle_size = int(options.get("subtitle_size", 18) or 18)
    model_size = options.get("model_size", "small")
    language = options.get("language", "vi")

    duration = media_duration(video_path)
    if end is None or end <= 0 or end > duration:
        end = duration
    if end <= start:
        raise RuntimeError("Thời gian kết thúc phải lớn hơn thời gian bắt đầu.")

    filter_parts = []
    if ratio == "9:16":
        filter_parts += ["scale=1080:1920:force_original_aspect_ratio=increase", "crop=1080:1920"]
    elif ratio == "1:1":
        filter_parts += ["scale=1080:1080:force_original_aspect_ratio=increase", "crop=1080:1080"]
    elif ratio == "16:9":
        filter_parts += ["scale=1920:1080:force_original_aspect_ratio=increase", "crop=1920:1080"]

    if flip:
        filter_parts.append("hflip")
    if speed != 1:
        filter_parts.append(f"setpts=PTS/{speed}")

    if add_subtitles:
        transcribe_to_srt(video_path, srt_path, model_size=model_size, language=language)
        srt_escaped = escape_filter_path(srt_path)
        style = f"FontSize={subtitle_size},Outline=2,Shadow=1,Alignment=2,MarginV=45"
        filter_parts.append(f"subtitles='{srt_escaped}':force_style='{style}'")

    if watermark:
        safe = watermark.replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            "drawtext=text='{}':x=w-tw-30:y=30:fontsize=28:fontcolor=white@0.85:"
            "box=1:boxcolor=black@0.35:boxborderw=10".format(safe)
        )

    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", str(video_path)]
    if music_path:
        cmd += ["-stream_loop", "-1", "-i", str(music_path)]

    if filter_parts:
        cmd += ["-vf", ",".join(filter_parts)]

    if music_path:
        if mute_original:
            cmd += ["-map", "0:v:0", "-map", "1:a:0", "-shortest"]
        else:
            # Mix original audio and music softly.
            cmd += [
                "-filter_complex",
                "[0:a]volume=1.0[a0];[1:a]volume=0.22[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v:0", "-map", "[a]", "-shortest"
            ]
    elif mute_original:
        cmd += ["-an"]

    if speed != 1 and not mute_original and not music_path:
        # Audio tempo supports 0.5-2.0.
        cmd += ["-af", f"atempo={speed}"]

    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output_path)
    ]
    run_cmd(cmd)
    return output_path, srt_path if srt_path.exists() else None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True, "ffmpeg": ffmpeg_exists()})


@app.post("/process")
def process_video():
    if not ffmpeg_exists():
        return jsonify({"ok": False, "error": "Máy chưa cài FFmpeg."}), 500

    video = request.files.get("video")
    music = request.files.get("music")
    if not video or not video.filename:
        return jsonify({"ok": False, "error": "Vui lòng chọn video."}), 400
    if not ext_ok(video.filename, ALLOWED_VIDEO):
        return jsonify({"ok": False, "error": "Định dạng video không được hỗ trợ."}), 400
    if music and music.filename and not ext_ok(music.filename, ALLOWED_AUDIO):
        return jsonify({"ok": False, "error": "Định dạng nhạc không được hỗ trợ."}), 400

    job_id = uuid.uuid4().hex[:12]
    video_path = UPLOAD_DIR / f"{job_id}_{secure_filename(video.filename)}"
    video.save(video_path)
    music_path = None
    if music and music.filename:
        music_path = UPLOAD_DIR / f"{job_id}_{secure_filename(music.filename)}"
        music.save(music_path)

    try:
        output_path, srt_path = build_video(job_id, video_path, music_path, request.form)
        return jsonify({
            "ok": True,
            "video_url": f"/download/{output_path.name}",
            "subtitle_url": f"/download/{srt_path.name}" if srt_path else None
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/download/<path:filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
