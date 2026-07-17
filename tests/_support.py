from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sys
import wave
from pathlib import Path


sys.dont_write_bytecode = True


_VALID_SOURCE_MP4_8S_B64 = (
    "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAANBbW9vdgAAAGxtdmhkAAAAAAAAAAAAAAAAAAAD6AAAH0AAAQAAAQAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAmt0cmFrAAAAXHRraGQAAAADAAAAAAAAAAAAAAABAAAAAAAAH0AAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAABAAAAAABAAAAAQAAAAAAAkZWR0cwAAABxlbHN0AAAAAAAAAAEAAB9AAAAAAAABAAAAAAHjbWRpYQAAACBtZGhkAAAAAAAAAAAAAAAAAABAAAACAABVxAAAAAAALWhkbHIAAAAAAAAAAHZpZGUAAAAAAAAAAAAAAABWaWRlb0hhbmRsZXIAAAABjm1pbmYAAAAUdm1oZAAAAAEAAAAAAAAAAAAAACRkaW5mAAAAHGRyZWYAAAAAAAAAAQAAAAx1cmwgAAAAAQAAAU5zdGJsAAAAtnN0c2QAAAAAAAAAAQAAAKZhdmMxAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAABAAEABIAAAASAAAAAAAAAABFUxhdmM2Mi4yOC4xMDAgbGlieDI2NAAAAAAAAAAAAAAAGP//AAAALGF2Y0MBQsAK/+EAFWdCwAraewEQAAADABAAAAMAIPEiagEABGjOD8gAAAAQcGFzcAAAAAEAAAABAAAAFGJ0cnQAAAAAAAACpAAAAAAAAAAYc3R0cwAAAAAAAAABAAAACAAAQAAAAAAUc3RzcwAAAAAAAAABAAAAAQAAABxzdHNjAAAAAAAAAAEAAAABAAAACAAAAAEAAAA0c3RzegAAAAAAAAAAAAAACAAAAmUAAAAJAAAACQAAAAkAAAAJAAAACQAAAAkAAAAJAAAAFHN0Y28AAAAAAAAAAQAAA3EAAABidWR0YQAAAFptZXRhAAAAAAAAACFoZGxyAAAAAAAAAABtZGlyYXBwbAAAAAAAAAAAAAAAAC1pbHN0AAAAJal0b28AAAAdZGF0YQAAAAEAAAAATGF2ZjYyLjEyLjEwMAAAAAhmcmVlAAACrG1kYXQAAAJTBgX//0/cRem95tlIt5Ys2CDZI+7veDI2NCAtIGNvcmUgMTY1IHIzMjIzIDA0ODBjYjAgLSBILjI2NC9NUEVHLTQgQVZDIGNvZGVjIC0gQ29weWxlZnQgMjAwMy0yMDI1IC0gaHR0cDovL3d3dy52aWRlb2xhbi5vcmcveDI2NC5odG1sIC0gb3B0aW9uczogY2FiYWM9MCByZWY9MSBkZWJsb2NrPTA6MDowIGFuYWx5c2U9MDowIG1lPWRpYSBzdWJtZT0wIHBzeT0xIHBzeV9yZD0xLjAwOjAuMDAgbWl4ZWRfcmVmPTAgbWVfcmFuZ2U9MTYgY2hyb21hX21lPTEgdHJlbGxpcz0wIDh4OGRjdD0wIGNxbT0wIGRlYWR6b25lPTIxLDExIGZhc3RfcHNraXA9MSBjaHJvbWFfcXBfb2Zmc2V0PTAgdGhyZWFkcz0xIGxvb2thaGVhZF90aHJlYWRzPTEgc2xpY2VkX3RocmVhZHM9MCBucj0wIGRlY2ltYXRlPTEgaW50ZXJsYWNlZD0wIGJsdXJheV9jb21wYXQ9MCBjb25zdHJhaW5lZF9pbnRyYT0wIGJmcmFtZXM9MCB3ZWlnaHRwPTAga2V5aW50PTI1MCBrZXlpbnRfbWluPTEgc2NlbmVjdXQ9MCBpbnRyYV9yZWZyZXNoPTAgcmM9Y3JmIG1idHJlZT0wIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN0ZXA9NCBpcF9yYXRpbz0xLjQwIGFxPTAAgAAAAApliIQ6JigACQLgAAAABUGaIBSlAAAABUGaQBWlAAAABUGaYBWlAAAABUGagBWlAAAABUGaoBWlAAAABUGawBWlAAAABUGa4Bal"
)
VALID_SOURCE_MP4_SHA256 = hashlib.sha256(
    base64.b64decode(_VALID_SOURCE_MP4_8S_B64)
).hexdigest()


def write_valid_source_mp4(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(_VALID_SOURCE_MP4_8S_B64))


def write_valid_wav(
    path: Path,
    *,
    duration_sec: float = 8.0,
    sample_rate_hz: int = 48000,
    channels: int = 2,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = round(duration_sec * sample_rate_hz)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate_hz)
        handle.writeframes(b"\0\0" * channels * frame_count)


def write_source_voice_separation_fixture(
    root: Path,
    source_sha256: str,
    *,
    duration_sec: float = 8.0,
) -> None:
    source_audio = root / "10_analysis" / "audio" / "full_source_audio.wav"
    vocals = root / "10_analysis" / "audio" / "vocals.wav"
    write_valid_wav(source_audio, duration_sec=duration_sec)
    write_valid_wav(vocals, duration_sec=duration_sec)
    source_audio_sha256 = hashlib.sha256(source_audio.read_bytes()).hexdigest()
    vocals_sha256 = hashlib.sha256(vocals.read_bytes()).hexdigest()
    manifest = {
        "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "source_fingerprint_sha256": source_sha256,
        "separation_engine": "demucs",
        "separation_model": "htdemucs",
        "separation_scope": "FULL_SOURCE_AUDIO",
        "source_audio_path": "10_analysis/audio/full_source_audio.wav",
        "source_audio_sha256": source_audio_sha256,
        "demucs_input_sha256": source_audio_sha256,
        "vocals_path": "10_analysis/audio/vocals.wav",
        "vocals_sha256": vocals_sha256,
        "source_duration_sec": duration_sec,
        "source_audio_duration_sec": duration_sec,
        "vocals_duration_sec": duration_sec,
        "duration_tolerance_sec": 0.25,
        "sample_rate_hz": 48000,
        "channels": 2,
        "source_voice_music_removed": True,
        "q_segment_source": "10_analysis/audio/vocals.wav",
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    manifest_path = root / "10_analysis" / "source_voice_separation.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_vmake_clean_source_fixture(
    root: Path,
    source_sha256: str,
    *,
    source_url: str = "https://www.youtube.com/shorts/fixture123",
    video_id: str = "fixture123",
    job_id: str = "fixture-vmake-job",
    duration_sec: float = 8.0,
) -> None:
    source = root / "00_source" / "source.mp4"
    if not source.exists():
        write_valid_source_mp4(source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha256:
        raise AssertionError("source_sha256 must match the source fixture")
    clean = root / "00_source" / "clean_source.mp4"
    write_valid_source_mp4(clean)
    manifest = {
        "gate_name": "VMAKE_CLEAN_SOURCE_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "provider": "vmake.ai",
        "provider_page": "https://vmake.ai/video-watermark-remover/upload",
        "provider_operation": "video_watermark_remover_auto",
        "requested_source_url": source_url,
        "requested_video_id": video_id,
        "source_fingerprint_sha256": source_sha256,
        "analysis_video_path": "00_source/source.mp4",
        "analysis_source_role": "original_source_only",
        "clean_visual_path": "00_source/clean_source.mp4",
        "clean_visual_sha256": hashlib.sha256(clean.read_bytes()).hexdigest(),
        "production_visual_role": "vmake_clean_visual",
        "vmake_job_id": job_id,
        "downloaded_filename": f"File_from_link_-_{job_id}.mp4",
        "download_method": "browser_download",
        "rights_confirmed": True,
        "confirmation_source": "user",
        "source_duration_sec": duration_sec,
        "clean_duration_sec": duration_sec,
        "duration_tolerance_sec": 0.5,
        "source_width": 16,
        "source_height": 16,
        "clean_width": 16,
        "clean_height": 16,
        "embedded_audio_policy": "muted_always",
        "source_voice_policy": "separate_demucs_q_only",
        "no_vocals_used": False,
        "created_by": "register_vmake_clean_source.py",
    }
    path = root / "10_analysis" / "vmake_clean_source.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_source_module_no_bytecode(module_name: str, path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
