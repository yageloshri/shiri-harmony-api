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
        chords = []
        for frame in chroma.T:
            idx = frame.argmax()
            chords.append(librosa.midi_to_note(idx + 36))  # מ-C3 ומעלה

        simplified = []
        for chord in chords:
            if not simplified or chord != simplified[-1]:
                simplified.append(chord)

        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)

        return JSONResponse(content={"chords": simplified[:50]})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
