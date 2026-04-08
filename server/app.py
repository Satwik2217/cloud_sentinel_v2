import os
from typing import Dict, List, Optional
from pydantic import BaseModel

# --- STEP 1: DEFINE TASK MODEL ---
class Task(BaseModel):
    id: str
    name: str
    description: str
    difficulty: str

# --- STEP 2: CORE OPENENV IMPORTS ---
try:
    from openenv.core.env_server.http_server import create_app
except ImportError as e:
    raise ImportError("openenv-core is required. Run 'pip install openenv-core'") from e

# --- STEP 3: PROJECT-SPECIFIC IMPORTS ---
try:
    from ..models import CloudSentinelAction, CloudSentinelObservation
    from .cloud_sentinel_environment import CloudSentinelEnvironment
except (ImportError, ModuleNotFoundError):
    from models import CloudSentinelAction, CloudSentinelObservation
    from server.cloud_sentinel_environment import CloudSentinelEnvironment

# --- STEP 4: CREATE THE APP ---
# We REMOVE 'tasks=TASKS' to fix the TypeError
app = create_app(
    CloudSentinelEnvironment,
    CloudSentinelAction,
    CloudSentinelObservation,
    env_name="cloud_sentinel",
    max_concurrent_envs=1,
)

# --- STEP 5: MANUALLY INJECT THE TASKS ENDPOINT ---
# This "forces" the API to show the 3 tasks Meta requires
TASKS_DATA = [
    {
        "id": "secure-one", 
        "name": "Secure One Server", 
        "description": "Harden at least one resource (0.2 score).", 
        "difficulty": "easy"
    },
    {
        "id": "secure-three", 
        "name": "Secure Three Servers", 
        "description": "Harden three resources (0.6 score).", 
        "difficulty": "medium"
    },
    {
        "id": "full-hardening", 
        "name": "Full Network Hardening", 
        "description": "Harden all five resources (1.0 score).", 
        "difficulty": "hard"
    }
]

@app.get("/tasks", response_model=List[Task])
async def list_tasks():
    return TASKS_DATA

@app.get("/")
async def root():
    return {"status": "Cloud Sentinel Live", "message": "Ready for Security Audit"}

def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()