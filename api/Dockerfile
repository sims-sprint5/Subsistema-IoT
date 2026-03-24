FROM python:3.12-slim

WORKDIR /code

# Needed for optional GPIO deps on ARM (e.g. RPi.GPIO). Harmless on x86.
RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc python3-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
