#!/usr/bin/env bash

# עדכון והתקנת כלים דרושים
apt-get update && apt-get install -y ffmpeg fluidsynth curl

# התקנת תלויות פייתון
pip install --no-cache-dir -r requirements.txt
