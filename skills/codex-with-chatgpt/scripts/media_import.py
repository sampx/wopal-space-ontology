#!/usr/bin/env python3
"""c2c media import — fallback channel for browser-downloaded assets.

Validates file signatures, SVG safety, size limits, and copies to a new
workspace-relative path (never overwrites). Returns JSON with sha256.

Ported from codex-with-chatgpt src/media/import.ts (MIT, XiaoDuoYa).
No external dependencies.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

MAX_MEDIA_BYTES = 512 * 1024 * 1024  # 512 MiB
MAX_SVG_BYTES = 10 * 1024 * 1024       # 10 MiB

MEDIA_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".mov": "video/quicktime",
    ".mp4": "video/mp4",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webm": "video/webm",
    ".webp": "image/webp",
}

SVG_UNSAFE_RE = re.compile(
    r"<(?:script|foreignObject|iframe|object|embed)\b"
    r"|\son[a-z]+\s*="
    r"|(?:href|src)\s*=\s*[\"']\s*(?:https?:|//|javascript:|data:text/html)"
    r"|url\(\s*[\"']?(?:https?:|//|data:)"
    r"|@import\b"
    r"|<!ENTITY\b",
    re.IGNORECASE,
)


def check_signature(header: bytes, ext: str) -> bool:
    if ext == ".png":
        return header[:8] == b"\x89PNG\r\n\x1a\n"
    if ext in (".jpg", ".jpeg"):
        return header[0] == 0xFF and header[1] == 0xD8 and header[2] == 0xFF
    if ext == ".gif":
        return header[:6] in (b"GIF87a", b"GIF89a")
    if ext == ".webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if ext == ".webm":
        return header[:4] == b"\x1a\x45\xdf\xa3"
    if ext in (".mp4", ".mov"):
        return header[4:8] == b"ftyp"
    return False


def check_svg(text: str) -> None:
    if not re.match(r"^\s*(?:<\?xml[^>]*>\s*)?<svg\b", text, re.IGNORECASE):
        raise ValueError("Downloaded file is not an SVG document")
    if SVG_UNSAFE_RE.search(text):
        raise ValueError("SVG contains active or externally loaded content")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def import_media(source: str, dest_rel: str, workspace_root: str) -> dict:
    src = os.path.realpath(source)
    stat = os.stat(src)
    if not os.path.isfile(src):
        raise ValueError("Media source must be a regular file")
    if stat.st_size == 0 or stat.st_size > MAX_MEDIA_BYTES:
        raise ValueError(f"Media source must be between 1 byte and 512 MiB (got {stat.st_size})")

    dest_rel = dest_rel.lstrip("/")
    if dest_rel.endswith("/"):
        raise ValueError("A project-relative destination file is required")
    ext = os.path.splitext(dest_rel)[1].lower()
    if ext not in MEDIA_TYPES:
        raise ValueError(f"Unsupported media destination type: {ext or 'none'}")

    ws = Path(workspace_root).resolve()
    dest_abs = ws / dest_rel
    # Path escape check
    try:
        dest_abs.relative_to(ws)
    except ValueError:
        raise ValueError("Destination path escapes workspace root")
    if dest_abs.exists():
        raise ValueError(f"Destination already exists: {dest_rel}")

    dest_abs.parent.mkdir(parents=True, exist_ok=True)

    if ext == ".svg":
        with open(src, "r", encoding="utf-8") as f:
            text = f.read()
        if len(text.encode("utf-8")) > MAX_SVG_BYTES:
            raise ValueError("SVG exceeds the 10 MiB validation limit")
        check_svg(text)
    else:
        with open(src, "rb") as f:
            header = f.read(16)
        if not check_signature(header, ext):
            raise ValueError(f"Downloaded media content does not match {ext}")

    # COPYFILE_EXCL equivalent: fail if destination appears between check and copy
    fd = os.open(str(dest_abs), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    os.close(fd)
    shutil.copy2(src, str(dest_abs))

    return {
        "sourcePath": src,
        "destinationPath": dest_rel,
        "mediaType": MEDIA_TYPES[ext],
        "sizeBytes": stat.st_size,
        "sha256": sha256_file(str(dest_abs)),
    }


def main():
    ap = argparse.ArgumentParser(description="c2c media import (fallback channel)")
    ap.add_argument("--source", required=True, help="downloaded file path")
    ap.add_argument("--dest", required=True, help="workspace-relative destination path")
    ap.add_argument("--workspace-root", required=True, help="workspace root directory")
    args = ap.parse_args()
    try:
        result = import_media(args.source, args.dest, args.workspace_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, OSError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
