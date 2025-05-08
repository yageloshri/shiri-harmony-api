from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import uuid
import librosa
import numpy as np
from pydub import AudioSegment

app = FastAPI()

# מיפוי מספרי של כרומה לאקורדים בסיסיים (C, C#, D...)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F',
              'F#', 'G', 'G#', 'A', 'A#', 'B']

def detect_chord_from_chroma_vector(vector):
    """נבחר את האקורד עם הערך הגבוה ביותר"""
    root_index = np.argmax(vector)
    return NOTE_NAMES[root_index]

@app.post("/chords")
async def detect_chords(file: UploadFile = File(...)):
    try:
        # שמירת קובץ זמני
        uid = uuid.uuid4().hex
        input_path = f"input_{uid}_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # המרה ל-WAV אם צריך
        converted_path = input_path
        if not input_path.lower().endswith(".wav"):
            audio = AudioSegment.from_file(input_path)
            converted_path = f"converted_{uid}.wav"
            audio.export(converted_path, format="wav")

        # טעינה עם librosa
        y, sr = librosa.load(converted_path)
        hop_length = 512
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

        # זיהוי אקורדים גולמי
        chords_raw = []
        for i, frame in enumerate(chroma.T):
            chord = detect_chord_from_chroma_vector(frame)
            time = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)
            chords_raw.append({"chord": chord, "time": round(time, 2)})

        # סינון כפילויות והוספת זמנים
        filtered = []
        for i, curr in enumerate(chords_raw):
            if i == 0 or curr["chord"] != chords_raw[i-1]["chord"]:
                filtered.append(curr)

        final_chords = []
        for i in range(len(filtered)):
            start = filtered[i]["time"]
            end = filtered[i+1]["time"] if i+1 < len(filtered) else round(librosa.get_duration(y=y, sr=sr), 2)
            final_chords.append({
                "chord": filtered[i]["chord"],
                "start": start,
                "end": end
            })

        # ניקוי
        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": final_chords})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
