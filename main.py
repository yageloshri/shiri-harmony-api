from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import librosa
import os
import uuid
from pydub import AudioSegment
from collections import defaultdict

app = FastAPI()

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def classify_chord(notes):
    """מזהה אקורד על בסיס שלישייה פשוטה"""
    if len(notes) < 3:
        return None

    notes = sorted(set([librosa.note_to_midi(n) % 12 for n in notes]))  # ignore octave
    for root in notes:
        third = (root + 4) % 12
        minor_third = (root + 3) % 12
        fifth = (root + 7) % 12

        if third in notes and fifth in notes:
            return f"{NOTE_NAMES[root]}maj"
        elif minor_third in notes and fifth in notes:
            return f"{NOTE_NAMES[root]}min"

    return None

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
        times = librosa.frames_to_time(range(chroma.shape[1]), sr=sr)

        chords = []
        last_chord = ""
        last_time = 0.0
        current_notes = []

        for i, frame in enumerate(chroma.T):
            active_notes = [NOTE_NAMES[j] for j, val in enumerate(frame) if val > 0.3]
            if not active_notes:
                continue

            chord = classify_chord(active_notes) or active_notes[0]
            chord = chord.replace("?", "")  # מנקה סימן שאלה

            time = float(times[i])
            if chord != last_chord or (time - last_time) > 1.5:
                chords.append({"chord": chord, "time": round(time, 2)})
                last_chord = chord
                last_time = time

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": chords})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
