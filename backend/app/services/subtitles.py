from __future__ import annotations

import re
from typing import Optional

import httpx
from yt_dlp import YoutubeDL


def _choose_caption_track(info_dict: dict, language_code: str) -> Optional[str]:
    subtitles = info_dict.get("subtitles") or {}
    auto = info_dict.get("automatic_captions") or {}

    def pick_best(tracks):
        if not tracks:
            return None
        for t in tracks:
            if t.get("ext") == "vtt":
                return t.get("url")
        return tracks[0].get("url")

    # 1) Try requested language (human first, then auto)
    tracks = subtitles.get(language_code) or []
    if not tracks:
        tracks = auto.get(language_code) or []
    url = pick_best(tracks)
    if url:
        return url

    # 2) Try common English variants if not already en
    if language_code.lower() not in {"en", "en-us", "en-gb"}:
        for lc in ("en", "en-US", "en-GB"):
            url = pick_best(subtitles.get(lc) or []) or pick_best(auto.get(lc) or [])
            if url:
                return url

    # 3) Try any human subtitle in any language
    for lc, tr in subtitles.items():
        url = pick_best(tr)
        if url:
            return url

    # 4) Finally, try any auto caption in any language
    for lc, tr in auto.items():
        url = pick_best(tr)
        if url:
            return url

    return None


def _vtt_to_text(vtt_content: str) -> str:
    # Remove WEBVTT header and notes
    lines = []
    for line in vtt_content.splitlines():
        if not line or line.startswith("WEBVTT"):
            continue
        # Skip cue timings like 00:00:01.000 --> 00:00:02.000
        if re.search(r"\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}", line):
            continue
        # Skip cue identifiers (numeric or alphanumeric lines without spaces)
        if re.match(r"^[A-Za-z0-9_-]+$", line):
            continue
        # Remove HTML tags if any
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    return " ".join(lines)


def get_video_info(youtube_url: str) -> dict:
    """Extract video title and other metadata from YouTube URL"""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
    
    return {
        "title": info.get("title", "Unknown Title"),
        "url": youtube_url,
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", "Unknown"),
        "view_count": info.get("view_count", 0)
    }


def get_subtitles_text(youtube_url: str, language_code: str = "en") -> str:
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    caption_url = _choose_caption_track(info, language_code)
    if not caption_url:
        raise ValueError("No subtitles or auto-captions available for this video.")

    # Use a longer timeout for subtitle download
    with httpx.Client(timeout=60) as client:
        resp = client.get(caption_url)
        resp.raise_for_status()
        content = resp.text

    # Convert to plain text if VTT, otherwise return raw
    if caption_url.endswith(".vtt") or "\nWEBVTT" in content[:16]:
        return _vtt_to_text(content)
    return content


