FROM python:3.10-slim

WORKDIR /app

COPY requirement.txt .

RUN pip install --upgrade pip && \
    pip install --default-timeout=300 -r requirement.txt

COPY . .

# Create a user and switch to it
RUN adduser --disabled-password celeryuser
USER celeryuser


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
