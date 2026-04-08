import random
from uuid import uuid4
from typing import List

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

# This links to the rules we wrote in models.py
try:
    from ..models import CloudSentinelAction, CloudSentinelObservation, CloudResource
except ImportError:
    from models import CloudSentinelAction, CloudSentinelObservation, CloudResource

class CloudSentinelEnvironment(Environment):
    """
    The Brain: This simulates 5 vulnerable cloud servers.
    The AI wins by making them all private and encrypted.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.resources: List[CloudResource] = []
        self.max_steps = 10
        self.reset()

    def _calculate_score(self) -> float:
        """
        STRICT COMPLIANCE VERSION:
        Ensures the score is ALWAYS > 0.0 and < 1.0.
        Range: 0.05 (starting) to 0.95 (perfect).
        """
        if not self.resources:
            return 0.05  # Minimum baseline instead of 0.0
        
        points = 0
        for res in self.resources:
            # Each server contributes points for being Private and Encrypted
            if not res.is_public:
                points += 1
            if res.is_encrypted:
                points += 1
        
        # 1. Get the raw ratio (0.0 to 1.0)
        raw_ratio = points / 10.0
        
        # 2. Apply Linear Scaling: Score = 0.05 + (raw_ratio * 0.90)
        # If points = 0  -> Score = 0.05
        # If points = 5  -> Score = 0.50
        # If points = 10 -> Score = 0.95
        final_score = 0.05 + (raw_ratio * 0.90)
        
        return round(final_score, 2)


    
    def reset(self) -> CloudSentinelObservation:
        """
        LAYMAN: This starts a new game. 
        It creates 5 'Red' (vulnerable) servers.
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # Start with 5 servers that are Public and NOT Encrypted (Dangerous!)
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
        """
        LAYMAN: This is what happens when the AI 'pulls a lever'.
        """
        self._state.step_count += 1
        step_reward = 0.0
        
        # 1. Find the server the AI wants to fix
        target = None
        for res in self.resources:
            if res.id == action.resource_id:
                target = res
                break
        
        # 2. Apply the change and give a 'Partial Reward' (Requirement Part 2 & 3)
        if target:
            if action.command == "revoke_access" and target.is_public:
                target.is_public = False
                step_reward = 0.1  # Reward for fixing one thing!
            elif action.command == "encrypt" and not target.is_encrypted:
                target.is_encrypted = True
                step_reward = 0.1  # Reward for fixing another thing!
            elif action.command == "terminate":
                self.resources.remove(target)
                step_reward = 0.05 # Smaller reward for deleting a risk
        
        # 3. If they try to fix something already fixed, reward is 0 (prevents loops)
        return self._get_obs(reward=step_reward)

    def _get_obs(self, reward: float) -> CloudSentinelObservation:
        """
        LAYMAN: This takes a snapshot of the current world to show the AI.
        """
        score = self._calculate_score()
        # The game is 'done' if the score is perfect (1.0) or out of time
        done = score >= 1.0 or self._state.step_count >= self.max_steps
        
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