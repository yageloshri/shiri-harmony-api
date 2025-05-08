from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
from music21 import stream, note, chord, midi
import subprocess
import uuid

app = FastAPI()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    try:
        # שמות קבצים זמניים עם מזהה ייחודי
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
            print("Converted to WAV:", converted_path)

        # ניתוח מלודיה עם librosa
        y, sr = librosa.load(converted_path)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        melody = []
        for i in range(pitches.shape[1]):
            index = magnitudes[:, i].argmax()
            pitch = pitches[index, i]
            if pitch > 0:
                try:
                    melody.append(librosa.hz_to_note(pitch))
                except Exception as e:
                    print("Failed to parse pitch:", pitch, e)

        # יצירת הרמוניה בסיסית
        midi_stream = stream.Stream()
        for pitch_name in melody[:16]:
            try:
                n = note.Note(pitch_name)
                c = chord.Chord([n, n.transpose(4), n.transpose(7)])
                midi_stream.append(c)
            except Exception as e:
                print("Chord generation error:", pitch_name, e)

        # יצירת קובץ MIDI
        midi_fp = f"output_{uid}.mid"
        mf = midi.translate.streamToMidiFile(midi_stream)
        mf.open(midi_fp, 'wb')
        mf.write()
        mf.close()
        print("MIDI file created:", midi_fp)

        # המרת MIDI ל-WAV באמצעות fluidsynth
        soundfont_path = "soundfont.sf2"
        wav_fp = f"output_{uid}.wav"
        result = subprocess.run(
            ["fluidsynth", "-ni", soundfont_path, midi_fp, "-F", wav_fp, "-r", "44100"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Fluidsynth error:", result.stderr)
            return {"error": "Failed to convert MIDI to WAV"}

        print("WAV file created:", wav_fp)

        # ניקוי קבצים זמניים
        os.remove(input_path)
        if converted_path != input_path:
            os.remove(converted_path)
        os.remove(midi_fp)

        # החזרת הקובץ הסופי
        return FileResponse(wav_fp, media_type="audio/wav", filename="harmonized.wav")

    except Exception as e:
        print("Exception occurred:", str(e))
        return {"error": str(e)}
