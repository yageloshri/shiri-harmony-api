from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import librosa
import os
import uuid
from pydub import AudioSegment

app = FastAPI()

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
        last_chord = None
        for i, frame in enumerate(chroma.T):
            idx = frame.argmax()
            note = librosa.midi_to_note(idx + 36)  # C3 ומעלה
            timestamp = round(float(times[i]), 2)

            if note != last_chord:
                chords.append({
                    "chord": note,
                    "time": timestamp
                })
                last_chord = note

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": chords[:50]})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
