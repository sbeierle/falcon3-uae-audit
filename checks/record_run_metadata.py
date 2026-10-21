"""Writes results/run_metadata.json (versions, GPU, model-file hashes). Run on the machine that produces the results.
usage: python3 -I checks/record_run_metadata.py <model folder>
"""
import hashlib, json, os, platform, subprocess, sys, datetime

def ver(mod):
    try:
        m = __import__(mod)
        return getattr(m, "__version__", "unknown")
    except Exception:
        return None

def sha(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None

def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return None

if len(sys.argv) != 2:
    sys.exit("usage: record_run_metadata.py <model folder>")
model = sys.argv[1]
weights = [f for f in os.listdir(model) if f.endswith((".safetensors", ".bin"))] if os.path.isdir(model) else []
meta = {
    "date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "torch": ver("torch"),
    "transformers": ver("transformers"),
    "nvidia_smi": run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]),
    "nvidia_smi_L": run(["nvidia-smi", "-L"]),
    "model_dir_name": os.path.basename(os.path.abspath(model)),
    "config_json_sha256": sha(os.path.join(model, "config.json")),
    "tokenizer_json_sha256": sha(os.path.join(model, "tokenizer.json")),
    "weight_files": {w: os.path.getsize(os.path.join(model, w)) for w in sorted(weights)},
    "to_fill_by_hand": ["model id + revision hash", "decoding arguments", "host type"],
}
try:
    import torch
    meta["cuda"] = torch.version.cuda
except Exception:
    meta["cuda"] = None
os.makedirs("results", exist_ok=True)
json.dump(meta, open("results/run_metadata.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps(meta, indent=2, ensure_ascii=False))
