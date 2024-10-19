FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only the requirements.txt file first, to cache dependencies separately
COPY requirements.gmtc.txt /app/

# Install Python dependencies, including pyaudio
RUN pip install --no-cache-dir -r requirements.gmtc.txt

# Now copy the rest of the application
COPY . /app

# Expose port
EXPOSE 8080

# Run Streamlit app
CMD ["streamlit", "run", "app_gmtc.py", "--server.port=8080", "--server.address=0.0.0.0"]
