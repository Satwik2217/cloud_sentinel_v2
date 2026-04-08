from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# 1. This defines what a single Cloud Server looks like (The "Toy")
class CloudResource(BaseModel):
    id: str = Field(..., description="Unique name of the resource, e.g., 'res-0'")
    type: str = Field(..., description="Type: e.g., 'virtual_machine' or 'database'")
    is_public: bool = Field(..., description="If True, it is exposed to the internet (Dangerous)")
    is_encrypted: bool = Field(..., description="If True, the data is locked (Safe)")

# 2. This defines what the AI is allowed to DO (The "Lever")
class CloudSentinelAction(BaseModel):
    resource_id: str = Field(..., description="The ID of the resource to target")
    command: str = Field(..., description="The command: 'revoke_access', 'encrypt', or 'terminate'")

# 3. This defines what the AI SEES (The "Status Report")
class CloudSentinelObservation(BaseModel):
    resources: List[CloudResource] = Field(..., description="List of all current servers and their status")
    security_score: float = Field(..., description="Overall security score from 0.0 to 1.0")
    current_step: int = Field(..., description="The current turn number")
    done: bool = Field(..., description="True if the task is finished")
    reward: float = Field(..., description="The immediate reward for the last action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra info for the judge")