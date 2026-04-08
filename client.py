from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

# This links to the rules we just wrote in models.py
from models import CloudSentinelAction, CloudSentinelObservation


class CloudSentinelEnv(
    EnvClient[CloudSentinelAction, CloudSentinelObservation, State]
):
    """
    Client for the Cloud Sentinel Environment.
    This acts as the bridge between the AI and the Security Server.
    """

    def _step_payload(self, action: CloudSentinelAction) -> Dict:
        """
        LAYMAN: This takes the AI's choice (like 'Encrypt Server 1') 
        and packages it into a format the server understands.
        """
        return {
            "resource_id": action.resource_id,
            "command": action.command,
        }

    def _parse_result(self, payload: Dict) -> StepResult[CloudSentinelObservation]:
        """
        LAYMAN: This takes the 'Status Report' from the server and 
        turns it into a clean observation for the AI to look at.
        """
        obs_data = payload.get("observation", {})
        
        # We rebuild the observation using our new fields
        observation = CloudSentinelObservation(
            resources=obs_data.get("resources", []),
            security_score=obs_data.get("security_score", 0.0),
            current_step=obs_data.get("current_step", 0),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        LAYMAN: Just tracking which turn we are on.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )