#!/usr/bin/env python3
"""Download *immutable verified* Bellward painting into the offline Godot art review project."""
from pathlib import Path
from urllib.request import urlopen, Request
import hashlib, struct, sys
URL = "https://d8j0ntlcm91z4.cloudfront.net/user_3KdWpuNzrU4I4JXokiW6lLNr1fO/hf_20261031_045941_970de4f4-4617-4190-a09c-3e51ea27f53c.png"
EXPECTED_SHA256 = "267cd029e3b9382a7b5202e518586f2fe85f5374871f821144444770785d0d54"
TARGET = Path(__file__).resolve().parents[1] / "assets" / "bellward_original_2688.png"

def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists() and hashlib.sha256(TARGET.read_bytes()).hexdigest() == EXPECTED_SHA256:
        print("PASS: immutable source art already downloaded; no data used")
        return 0
    try:
        with urlopen(Request(URL, headers={"User-Agent": "NinefoldTide-ArtReview/1.0"}), timeout=45) as response:
            data = response.read()
    except Exception as exc:
        print(f"Cannot reach art source: {exc}. Use the source link in README.", file=sys.stderr)
        return 2
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECTED_SHA256:
        print("REJECT: source art changed! Expected %s, received %s" % (EXPECTED_SHA256, sha), file=sys.stderr)
        return 3
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        print("REJECT: image is not PNG", file=sys.stderr)
        return 4
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (2688, 1520):
        print("REJECT: original artwork dimensions changed", file=sys.stderr)
        return 5
    TARGET.write_bytes(data)
    print("PASS: verified", width, height, "px;", len(data), "bytes", sha)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
