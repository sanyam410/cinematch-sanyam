FROM python:3.11-slim

WORKDIR /app
ENV HF_HOME=/tmp/hf_cache

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
CMD ["python", "App.py"]
