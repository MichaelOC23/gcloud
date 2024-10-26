FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only the requirements.txt file first, to cache dependencies separately
COPY requirements.personal-finance.txt /app/

# Install Python dependencies and cache the result
RUN pip install --no-cache-dir -r requirements.personal-finance.txt

# Now copy the rest of the application
COPY . /app
COPY ./classes-temp/ /app


# Expose port
EXPOSE 5050

# Run Streamlit app
CMD ["streamlit", "run", "app-personal-finance.py", "--server.port=5050", "--server.address=0.0.0.0"]
