FROM python:3.11-slim

# Install system dependencies for building pyaudio and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only the requirements.txt file first, to cache dependencies separately
COPY requirements.gcloud.txt /app/

# Install Python dependencies, including pyaudio
RUN pip install --no-cache-dir -r requirements.gcloud.txt

# Now copy the rest of the application
COPY ./classes-temp /app
COPY . /app

# Set the environment variables for Flask
ENV FLASK_APP=000_horizon_flask.py
ENV FLASK_ENV=development

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5020"]