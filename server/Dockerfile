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

# 7. Open the door for the Judge (Port 8000)
EXPOSE 8000

# 8. THE CRITICAL FIX: Match the Ping Address (Compliance Part 7)
# We changed this from '/health' to '/' to match our app.py
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 9. Start the 'Receptionist'
# We use the module path so Python finds 'server.app' correctly
CMD ["python", "-m", "server.app"]