from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import librosa
import os
import uuid
from pydub import AudioSegment
import numpy as np

app = FastAPI()

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

CHORD_PATTERNS = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    '7': [0, 4, 7, 10],
}

def detect_chord(chroma_vector):
    """Try to match chroma vector to known chord pattern"""
    threshold = 0.2
    active_notes = [i for i, x in enumerate(chroma_vector) if x > threshold]

    for root in active_notes:
        for chord_name, intervals in CHORD_PATTERNS.items():
            expected = [(root + interval) % 12 for interval in intervals]
            if all(note in active_notes for note in expected):
                return f"{NOTE_NAMES[root]}{chord_name}"
    if active_notes:
        return NOTE_NAMES[active_notes[0]]
    return "N/A"

@app.post("/chords")
async def detect_chords(file: UploadFile = File(...)):
    try:
        uid = uuid.uuid4().hex
        input_path = f"input_{uid}_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # המרה ל-WAV
        converted_path = input_path
        if not input_path.lower().endswith(".wav"):
            audio = AudioSegment.from_file(input_path)
            converted_path = f"converted_{uid}.wav"
            audio.export(converted_path, format="wav")

        y, sr = librosa.load(converted_path)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

        chords = []
        for frame in chroma.T:
            chord = detect_chord(frame)
            chords.append(chord)

        # הסרה של כפילויות רצופות
        simplified = []
        for chord in chords:
            if not simplified or chord != simplified[-1]:
                simplified.append(chord)

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": simplified[:50]})

    except Exception as e:
        print("❌ Error:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)
