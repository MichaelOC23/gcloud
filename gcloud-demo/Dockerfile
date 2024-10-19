FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only the requirements.txt file first, to cache dependencies separately
COPY requirements.gmtc.txt /app/

# Install Python dependencies, including pyaudio
RUN pip install --no-cache-dir -r requirements.gmtc.txt

# Now copy the rest of the application
COPY . /app

ENV STREAMLIT_THEME_BASE=dark
ENV STREAMLIT_LOGO_URL=https://firebasestorage.googleapis.com/v0/b/toolsexplorationfirebase.appspot.com/o/assets%2Flogo-white-gray.svg?alt=media&token=acaa8687-e6ff-42a7-a693-34b34cceefd6
ENV STREAMLIT_ICON_URL=https://firebasestorage.googleapis.com/v0/b/toolsexplorationfirebase.appspot.com/o/assets%2Ficon-white-gray.svg?alt=media&token=5550bb55-23c1-4151-9f35-642a3083f1d0
ENV STREAMLIT_PAGE_ICON=https://firebasestorage.googleapis.com/v0/b/toolsexplorationfirebase.appspot.com/o/assets%2Fpage-icon.svg?alt=media&token=5ecd156a-0371-442f-938e-2f3a3510b344



# Expose port
EXPOSE 8080

# Run Streamlit app
CMD ["streamlit", "run", "app_gmtc.py", "--server.port=8080", "--server.address=0.0.0.0"]
