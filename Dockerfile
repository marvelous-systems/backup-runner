FROM python:3-slim

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/src ./src
CMD [ "python", "./src/main.py" ]
