from pathlib import Path
import pygame

class AudioManager:
    """Optional audio: the game remains playable when no sound files are supplied."""
    FILES = {
        "bounce": "bounce.wav",
        "hit": "brick_hit.wav",
        "destroy": "explosion.wav",
        "life": "lose_life.wav",
        "power": "powerup.wav",
        "victory": "victory.wav",
        "gameover": "game_over.wav",
        "menu": "menu.ogg",
    }

    def __init__(self, sound_dir, save_data):
        self.sound_dir = Path(sound_dir)
        self.save_data = save_data
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for key, filename in self.FILES.items():
                path = self.sound_dir / filename
                if path.exists():
                    try:
                        self.sounds[key] = pygame.mixer.Sound(str(path))
                    except pygame.error:
                        pass
        except pygame.error:
            pass
        self.apply_volumes()

    def apply_volumes(self):
        muted = self.save_data.get("muted", False)
        sfx = 0 if muted else self.save_data.get("sfx_volume", 0.65)
        for sound in self.sounds.values():
            sound.set_volume(sfx)

    def play(self, name):
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except pygame.error:
                pass

    def toggle_mute(self):
        self.save_data["muted"] = not self.save_data.get("muted", False)
        self.apply_volumes()

    def change_volume(self, key, amount):
        self.save_data[key] = min(1.0, max(0.0, self.save_data.get(key, 0.5) + amount))
        self.apply_volumes()
