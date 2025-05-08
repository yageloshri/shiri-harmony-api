from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
from music21 import stream, note, chord, midi

app = FastAPI()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    input_path = f"temp_{file.filename}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    y, sr = librosa.load(input_path)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    melody = []
    for i in range(pitches.shape[1]):
        index = magnitudes[:, i].argmax()
        pitch = pitches[index, i]
        if pitch > 0:
            melody.append(librosa.hz_to_note(pitch))

    midi_stream = stream.Stream()
    for pitch_name in melody[:16]:
        try:
            n = note.Note(pitch_name)
            c = chord.Chord([n, n.transpose(4), n.transpose(7)])
            midi_stream.append(c)
        except:
            continue

    midi_fp = "output.mid"
    mf = midi.translate.streamToMidiFile(midi_stream)
    mf.open(midi_fp, 'wb')
    mf.write()
    mf.close()

    audio = AudioSegment.from_file(midi_fp, format="mid")
    mp3_fp = "output.mp3"
    audio.export(mp3_fp, format="mp3")

    os.remove(input_path)
    os.remove(midi_fp)

    return FileResponse(mp3_fp, media_type="audio/mp3", filename="harmonized.mp3")
