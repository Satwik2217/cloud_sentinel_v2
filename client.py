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
    """

    def _step_payload(self, action: CloudSentinelAction) -> Dict:
        return {
            "resource_id": action.resource_id,
            "command": action.command,
        }

    def _parse_result(self, payload: Dict) -> StepResult[CloudSentinelObservation]:
        obs_data = payload.get("observation", {})
        
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
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )