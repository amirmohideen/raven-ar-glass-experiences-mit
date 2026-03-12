# Raven Resonance AR Glass Experiences

This repository contains 2 AR glass experiences I built using the Raven SDK during MIT Reality Hack 2026.

## Projects

### 1. Snake Game
A recreation of the classic Nokia Snake game for Raven Resonance AR Glasses.

![Snake Game_Demo](assets/snake_game.gif)

**Controls**
- Move with eye gaze
- Blink twice to play or pause

### 2. Fireworks Experience
A simple interactive AR fireworks experience for Raven Glass.

![Snake Game_Demo](assets/fireworks_experience.gif)

**Controls**
- Blink twice to launch fireworks

## Why this repo exists

At MIT Reality Hack, Raven Resonance claimed that even beginners could set up and deploy experiences to Raven Glass in under 10 minutes.

After trying the SDK myself, I found the workflow surprisingly fast and approachable, especially compared to the usual friction involved in deploying to XR devices for the first time.

## Tech stack

- Python
- Raven SDK
- Claude Opus for rapid prototyping

## Repo structure

- `snake_game/` contains the Snake project
- `fireworks_experience/` contains the Fireworks project
- `assets/` contains demo media used in the README

## Demo

Add GIFs or screenshots here.

## Getting started

Clone the repository

    git clone https://github.com/amirmohideen/raven-ar-glass-experiences-mit.git
    cd raven-ar-glass-experiences-mit

Create a virtual environment

    python -m venv venv
    source venv/bin/activate

Install the Raven Framework

    git clone https://github.com/RavenResonance/raven-framework.git
    cd raven-framework
    pip install -e .
    cd ..

Run the Snake demo

    cd snake_game
    python main.py

------------------------------------------------------------------------

## Notes

The applications run in simulator mode by default. Deploying to real
Raven Glass devices requires valid `app_id` and `app_key` credentials.

Refer to the official Raven Framework documentation for full setup and
deployment details.

https://github.com/RavenResonance/raven-framework

------------------------------------------------------------------------

## Credits

Created by Amir Mohideen Basheer Khan

Thanks to the Raven Resonance team for building tools that significantly
lower the barrier to AR development.
