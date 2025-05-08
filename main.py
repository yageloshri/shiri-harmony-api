from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import librosa
import os
import uuid
from pydub import AudioSegment
from collections import Counter

app = FastAPI()

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F',
              'F#', 'G', 'G#', 'A', 'A#', 'B']

# פונקציה לזיהוי האקורד הפשוט ביותר לפי הטונים הדומיננטיים
def estimate_chord(chroma_vector):
    threshold = 0.3 * max(chroma_vector)
    active_notes = [i for i, val in enumerate(chroma_vector) if val > threshold]
    if not active_notes:
        return "N"

    root = active_notes[0]
    intervals = [(n - root) % 12 for n in active_notes]
    intervals_set = set(intervals)

    # תבניות בסיסיות
    if intervals_set == {0, 4, 7}:
        return NOTE_NAMES[root]
    elif intervals_set == {0, 3, 7}:
        return NOTE_NAMES[root] + "m"
    elif intervals_set == {0, 4, 7, 10}:
        return NOTE_NAMES[root] + "7"
    elif intervals_set == {0, 3, 7, 10}:
        return NOTE_NAMES[root] + "m7"
    elif intervals_set == {0, 4, 7, 11}:
        return NOTE_NAMES[root] + "maj7"
    else:
        return NOTE_NAMES[root] + "?"

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
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        times = librosa.frames_to_time(range(chroma.shape[1]), sr=sr)

        chords = []
        last_chord = ""
        for i, frame in enumerate(chroma.T):
            chord = estimate_chord(frame)
            timestamp = round(float(times[i]), 2)
            if chord != last_chord:
                chords.append({"chord": chord, "time": timestamp})
                last_chord = chord

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": chords[:50]})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
