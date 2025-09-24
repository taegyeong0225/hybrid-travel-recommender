# Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# OS 패키지 설치 (scikit-surprise 빌드용)
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install --no-cache-dir cython numpy scipy

# Install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Expose port and set command
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Copy input data (host, container)
COPY ./app/ml/1.inputdata /app/app/ml/1.inputdata
COPY ./app/ml/2.preprocessed /app/app/ml/2.preprocessed
COPY ./app/ml/4.SaveModel /app/app/ml/4.SaveModel