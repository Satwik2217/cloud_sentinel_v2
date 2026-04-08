import random
from uuid import uuid4
from typing import List, Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import CloudSentinelAction, CloudSentinelObservation, CloudResource
except ImportError:
    from models import CloudSentinelAction, CloudSentinelObservation, CloudResource

class CloudSentinelEnvironment(Environment):
    """
    Simulates 5 cloud servers for security hardening.
    The objective is to make them private and encrypted.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.resources: List[CloudResource] = []
        self.max_steps = 10
        self.reset()

    def _calculate_score(self) -> float:
        """
        Calculates the security score between 0.05 and 0.95.
        """
        if not self.resources:
            return 0.05
        
        points = 0
        for res in self.resources:
            if not res.is_public:
                points += 1
            if res.is_encrypted:
                points += 1
        
        raw_ratio = points / 10.0
        final_score = 0.05 + (raw_ratio * 0.90)
        
        return round(final_score, 2)


    
    def reset(self, task_id: Optional[str] = None) -> CloudSentinelObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        self.resources = [
            CloudResource(
                id=f"res-{i}", 
                type="server", 
                is_public=True, 
                is_encrypted=False
            ) for i in range(5)
        ]
        
        return self._get_obs(reward=0.0)

    def step(self, action: CloudSentinelAction) -> CloudSentinelObservation:
        self._state.step_count += 1
        step_reward = 0.0
        
        target = None
        for res in self.resources:
            if res.id == action.resource_id:
                target = res
                break
        
        if target:
            if action.command == "revoke_access" and target.is_public:
                target.is_public = False
                step_reward = 0.1
            elif action.command == "encrypt" and not target.is_encrypted:
                target.is_encrypted = True
                step_reward = 0.1
            elif action.command == "terminate":
                self.resources.remove(target)
                step_reward = 0.05
        
        return self._get_obs(reward=step_reward)

    def _get_obs(self, reward: float) -> CloudSentinelObservation:
        score = self._calculate_score()
        done = score >= 0.95 or self._state.step_count >= self.max_steps
        
        return CloudSentinelObservation(
            resources=[res.model_copy() for res in self.resources],
            security_score=score,
            current_step=self._state.step_count,
            done=done,
            reward=reward,
            metadata={"total_score_pct": f"{score*100}%"}
        )

    @property
    def state(self) -> State:
        return self._state