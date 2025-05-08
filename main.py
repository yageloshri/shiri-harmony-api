from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
from music21 import stream, note, chord, midi
import subprocess

app = FastAPI()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    input_path = f"temp_{file.filename}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # המרה ל-WAV אם הקובץ אינו בפורמט WAV
    converted_path = input_path
    if not input_path.lower().endswith(".wav"):
        audio = AudioSegment.from_file(input_path)
        converted_path = input_path.rsplit(".", 1)[0] + ".wav"
        audio.export(converted_path, format="wav")

    # עיבוד אודיו עם librosa
    y, sr = librosa.load(converted_path)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    melody = []
    for i in range(pitches.shape[1]):
        index = magnitudes[:, i].argmax()
        pitch = pitches[index, i]
