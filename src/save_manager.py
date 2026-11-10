import json
from pathlib import Path

class SaveManager:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {"high_score": 0, "music_volume": 0.35, "sfx_volume": 0.65, "muted": False}
        self.load()

    def load(self):
        try:
            if self.path.exists():
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data["high_score"] = max(0, int(loaded.get("high_score", 0)))
                    self.data["music_volume"] = min(1.0, max(0.0, float(loaded.get("music_volume", 0.35))))
                    self.data["sfx_volume"] = min(1.0, max(0.0, float(loaded.get("sfx_volume", 0.65))))
                    self.data["muted"] = bool(loaded.get("muted", False))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Corrupt or missing save data should never prevent the game from starting.
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=4), encoding="utf-8")
        except OSError:
            pass

    @property
    def high_score(self):
        return self.data["high_score"]

    def set_high_score(self, score):
        if score > self.data["high_score"]:
            self.data["high_score"] = int(score)
            self.save()
