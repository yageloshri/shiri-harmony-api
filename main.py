from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import librosa
import os
import uuid
from pydub import AudioSegment
from collections import Counter

app = FastAPI()

# המרת ערכי chroma לאקורדים פשוטים
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def guess_chord(chroma_vector):
    top_notes = chroma_vector.argsort()[-3:][::-1]  # שלושת הצלילים החזקים ביותר
    top_notes.sort()
    root = top_notes[0]
    third = (root + 4) % 12  # מז׳ורי ברירת מחדל
    fifth = (root + 7) % 12

    if third in top_notes and fifth in top_notes:
        return NOTE_NAMES[root]
    elif (root + 3) % 12 in top_notes:  # מינור
        return NOTE_NAMES[root] + 'm'
    return NOTE_NAMES[root] + '?'  # לא ברור מספיק

@app.post("/chords")
async def detect_chords(file: UploadFile = File(...)):
    try:
        uid = uuid.uuid4().hex
        input_path = f"input_{uid}_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        converted_path = input_path
        if not input_path.lower().endswith(".wav"):
            audio = AudioSegment.from_file(input_path)
            converted_path = f"converted_{uid}.wav"
            audio.export(converted_path, format="wav")

        y, sr = librosa.load(converted_path)
        hop_length = sr  # קפיצה של שנייה שלמה
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

        chords = []
        for i, frame in enumerate(chroma.T):
            chord = guess_chord(frame)
            time = round(i * (hop_length / sr), 2)
            if not chords or chords[-1]['chord'] != chord:
                chords.append({"chord": chord, "time": time})

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": chords})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
