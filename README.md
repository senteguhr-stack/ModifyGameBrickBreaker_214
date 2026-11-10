# AMBATUBALL — Modern Neon Arcade

Brick Breaker desktop game made with Python + Pygame.

## Features
- Neon arcade presentation and menu
- Paddle + ball Brick Breaker gameplay
- Photo bricks with normal/damaged image states
- HP-based bricks, score, lives, combo
- Particle burst effects
- Random power-ups: Big Paddle, Multi Ball, Slow, Fire, Extra Life, Magnet
- Five-stage progression with a boss encounter on level 5
- Pause, settings, high score JSON save
- Optional replaceable sound assets

## Requirements
- Python 3.10+
- Pygame 2.6.1+

## Run
Open a terminal in the project folder:

```bash
python -m venv venv
```

Windows:
```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source venv/bin/activate
```

Install and run:
```bash
python -m pip install -r requirements.txt
python main.py
```

## Controls
- Left / Right arrows or A / D: move paddle
- Space: launch ball
- ESC: pause / resume
- Settings: Left/Right changes SFX, Up/Down changes music level, M toggles mute

## Replace the photo bricks
Replace these files while keeping the same names:
- `assets/images/ucup.png` — normal photo
- `assets/images/ucup_damaged.png` — damaged photo

The game automatically crops and scales the images to fit each brick. Use photos you have permission to use.

## Optional audio
Place audio files in `assets/sounds/`:
- `bounce.wav`
- `brick_hit.wav` — custom impact sound supplied for AMBATUBALL
- `explosion.wav`
- `lose_life.wav`
- `powerup.wav`
- `victory.wav`
- `game_over.wav`
- `menu.ogg`

The game works without these files. The music volume setting is stored for future background-music integration; add a `menu.ogg` file when ready.

## Save data
High score and settings are stored in `data/highscore.json`.

