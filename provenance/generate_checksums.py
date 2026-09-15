#!/usr/bin/env python3
"""Generate (or verify) SHA256 checksums for Homa's released model artifacts.

Gate 2 requires SHA256 checksums so organizers can confirm the downloaded
weights match what the team trained and published.

Usage:
    python provenance/generate_checksums.py            # write SHA256SUMS.txt
    python provenance/generate_checksums.py --check    # verify against it

By default it hashes every model artifact under ../model and every adapter
under ./adapters. Large binaries are streamed in chunks so memory stays flat.
"""
import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SUMS_FILE = HERE / "SHA256SUMS.txt"

# Extensions worth checksumming (weights / adapters), anywhere under the roots.
ARTIFACT_SUFFIXES = {".gguf", ".safetensors", ".bin"}
SEARCH_ROOTS = [REPO / "model", HERE / "adapters"]


def iter_artifacts():
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in ARTIFACT_SUFFIXES:
                yield path


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def rel(path):
    """Repo-relative, forward-slash path for stable, portable checksum lines."""
    return path.relative_to(REPO).as_posix()


def write_sums():
    artifacts = list(iter_artifacts())
    if not artifacts:
        print("[warn] no artifacts found under: "
              + ", ".join(str(r) for r in SEARCH_ROOTS))
        print("       build/download the model first, then re-run.")
        return 1
    lines = [f"{sha256(p)}  {rel(p)}" for p in artifacts]
    SUMS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} checksum(s) to {SUMS_FILE.relative_to(REPO)}:")
    for line in lines:
        print(f"  {line}")
    return 0


def check_sums():
    if not SUMS_FILE.exists():
        print(f"[error] {SUMS_FILE} not found; run without --check first.")
        return 1
    ok = True
    for line in SUMS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        expected, _, relpath = line.partition("  ")
        path = REPO / relpath
        if not path.exists():
            print(f"MISSING  {relpath}")
            ok = False
            continue
        actual = sha256(path)
        status = "OK" if actual == expected else "FAIL"
        if actual != expected:
            ok = False
        print(f"{status:7} {relpath}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify existing SHA256SUMS.txt instead of writing it")
    args = ap.parse_args()
    return check_sums() if args.check else write_sums()


if __name__ == "__main__":
    sys.exit(main())
