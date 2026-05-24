#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

REAL_NEGATIVE = Path("benchmarks/data/wake/hola_roger/real_negative")
REAL_POSITIVE_VARIANTS = Path("benchmarks/data/wake/hola_roger/real_positive_variants")

# record_real_samples.py used a 7-prompt cycle before the homophone fix:
# 5 = "hola royer", 6 = "ola roger". In Spanish these are acceptable wake
# pronunciations, so they must not remain labeled as negatives.
HOMOPHONE_PROMPT_POSITIONS = {5, 6}
PROMPT_CYCLE_LEN = 7


def is_homophone_negative(index: int) -> bool:
    return ((index - 1) % PROMPT_CYCLE_LEN) + 1 in HOMOPHONE_PROMPT_POSITIONS


def relabel() -> list[tuple[Path, Path]]:
    REAL_POSITIVE_VARIANTS.mkdir(parents=True, exist_ok=True)
    moved: list[tuple[Path, Path]] = []
    for path in sorted(REAL_NEGATIVE.glob("negative_*.wav")):
        try:
            index = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        if not is_homophone_negative(index):
            continue
        dest = REAL_POSITIVE_VARIANTS / f"wake_variant_{index:03d}.wav"
        shutil.move(str(path), str(dest))
        moved.append((path, dest))
    return moved


def main() -> int:
    moved = relabel()
    if not moved:
        print("No homophone negatives found to relabel.")
        return 0
    for src, dest in moved:
        print(f"{src} -> {dest}")
    print(f"Relabeled {len(moved)} homophone clips as positive variants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
