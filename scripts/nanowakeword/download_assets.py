#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WAKE_DATA_DIR = ROOT / "benchmarks/data/wake/hola_roger"
BACKGROUND_DIR = WAKE_DATA_DIR / "background_noise"
TTS_MODELS_DIR = ROOT / "NwwResourcesModel/tts_models"
PHONEMIZE_DIR = ROOT / "NwwResourcesModel/phonemize_model"

FEATURE_ASSETS = {
    "RACON_11h_v1.npy": "https://huggingface.co/datasets/arcosoph/RACON_11h_v1/resolve/main/RACON_11h_v1.npy",
    "AE29H_float32.npy": "https://huggingface.co/datasets/arcosoph/AE29H_float32/resolve/main/AE29H_float32.npy",
    "openwakeword_features_ACAV100M_2000_hrs_16bit.npy": "https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy",
}

PIPER_VOICES = {
    "es_ES-sharvard-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium",
    "es_ES-davefx-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium",
    "es_MX-ald-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium",
}

PHONEMIZER_MODEL = {
    "phonemize_m1.pt": "https://github.com/arcosoph/phonemize/releases/download/v0.2.0/phonemize_m1.pt",
}


def download(url: str, path: Path, retries: int = 5) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        print(f"skip existing: {path}")
        return path

    tmp = path.with_suffix(path.suffix + ".part")
    headers = {"User-Agent": "roger-nanowakeword-assets/1.0"}
    for attempt in range(1, retries + 1):
        try:
            print(f"download: {url} -> {path}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
            tmp.replace(path)
            return path
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if tmp.exists():
                tmp.unlink()
            if attempt == retries:
                raise RuntimeError(f"failed to download {url}: {exc}") from exc
            wait = min(30, 2**attempt)
            print(f"retry {attempt}/{retries} after error: {exc}; sleeping {wait}s")
            time.sleep(wait)
    return path


def esc50_files() -> list[str]:
    api_url = "https://api.github.com/repos/karolpiczak/ESC-50/contents/audio"
    with urllib.request.urlopen(api_url, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return sorted(item["name"] for item in data if item["name"].endswith(".wav"))


def download_esc50(max_workers: int) -> None:
    BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)
    base_url = "https://raw.githubusercontent.com/karolpiczak/ESC-50/master/audio"
    files = esc50_files()
    print(f"ESC-50 wav files: {len(files)}")

    def one(filename: str) -> None:
        download(f"{base_url}/{filename}", BACKGROUND_DIR / filename)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(one, files))


def download_feature_assets() -> None:
    for filename, url in FEATURE_ASSETS.items():
        download(url, ROOT / filename)


def download_piper_voices() -> None:
    for voice, base_url in PIPER_VOICES.items():
        download(f"{base_url}.onnx", TTS_MODELS_DIR / f"{voice}.onnx")
        download(f"{base_url}.onnx.json", TTS_MODELS_DIR / f"{voice}.onnx.json")


def download_phonemizer() -> None:
    for filename, url in PHONEMIZER_MODEL.items():
        download(url, PHONEMIZE_DIR / filename)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download local NanoWakeWord training assets for Roger.")
    parser.add_argument("--skip-esc50", action="store_true", help="Do not download ESC-50 background WAVs.")
    parser.add_argument("--workers", type=int, default=8, help="Parallel ESC-50 download workers.")
    args = parser.parse_args()

    if not args.skip_esc50:
        download_esc50(max_workers=args.workers)
    download_feature_assets()
    download_piper_voices()
    download_phonemizer()
    print("NanoWakeWord assets are ready.")


if __name__ == "__main__":
    main()
