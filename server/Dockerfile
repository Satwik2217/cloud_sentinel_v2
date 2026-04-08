# 1. Use a lightweight Python 'Base' (Compliance Part 5)
FROM python:3.10-slim

# 2. Set the workspace
WORKDIR /app

# 3. Install 'curl' for the Judge's Ping (Compliance Part 7)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 4. Copy the ingredients list 
# (Note: We use '.' because 'openenv push' moves this to the root where requirements.txt lives)
COPY requirements.txt .

# 5. Install our Security Tools
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy all the code files
COPY . .

# 7. Use the port HF expects (Defaulting to 7860)
EXPOSE 7860

# 8. Updated Healthcheck to check the dynamic port
# We use 7860 here because it's the standard HF port
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# 9. Start the 'Receptionist' with a dynamic port
# We use the environment variable PORT if available, else 7860
CMD uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-7860}