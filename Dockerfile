# Dockerfile (תיקון)
FROM python:3.11-slim

# התקנת תלות מערכת נדרשת: curl ו־fluidsynth
RUN apt-get update && \
    apt-get install -y curl fluidsynth && \
    apt-get clean

# התקנת ספריות פייתון
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# הורדת קובץ SoundFont
RUN curl -L -o soundfont.sf2 https://member.keymusics.com/downloads/FluidR3_GM.sf2

# העתקת קוד האפליקציה
COPY . .

# הפעלת האפליקציה
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
