# 1. השתמש בתמונה מבוססת פייתון
FROM python:3.11-slim

# 2. התקן תלות במערכות כמו fluidsynth
RUN apt-get update && \
    apt-get install -y fluidsynth ffmpeg && \
    apt-get clean

# 3. העתק קבצי הקוד שלך
WORKDIR /app
COPY . .

# 4. התקן תלות פייתון
RUN pip install --no-cache-dir -r requirements.txt

# 5. הורד SoundFont (או תעלה ידנית לריפו שלך)
RUN curl -L -o soundfont.sf2 https://member.keymusics.com/downloads/FluidR3_GM.sf2

# 6. הפעל את השרת
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
