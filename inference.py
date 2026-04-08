import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI

# Try to load local .env file for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from client import CloudSentinelEnv
from models import CloudSentinelAction

# --- MANDATORY CONFIGURATION (Part 5 & 6) ---
# These defaults allow it to work locally, but OS envs take priority for the judge.
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "dummy_token")

# For Phase 2, we target the Hard task by default
TASK_NAME = "full-hardening"
MAX_STEPS = 10

SYSTEM_PROMPT = textwrap.dedent("""
    You are a Cloud Security Agent. Your mission is to secure all servers.
    A server is secure only if: is_public=False AND is_encrypted=True.
    
    Available Actions:
    1. 'revoke_access' (sets is_public to False)
    2. 'encrypt' (sets is_encrypted to True)
    
    Response Format: resource_id:command (e.g., res-0:encrypt)
    Rules: Reply with ONLY the action string. No prose, no explanations.
    Rule 1: You must ONLY output ONE action per turn.
    Rule 2: The format must be exactly 'resource_id:command'.
    Rule 3: Do NOT list multiple servers. Do NOT provide explanations.
    
    Example valid response: res-0:encrypt
""").strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def main():
    # 1. Initialize the OpenAI Client pointing to the HF Router
    openai_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    # 2. Connect to the Security Environment
    # Note: Inside the HF Space, the env is usually at localhost:8000
    async with CloudSentinelEnv(base_url="https://satwik2217-cloud-sentinel.hf.space") as env:    
        log_start(task=TASK_NAME, env="cloud_sentinel", model=MODEL_NAME)
        
        rewards = []
        steps_taken = 0
        final_score = 0.0
        
        try:
            result = await env.reset()
            
            for step in range(1, MAX_STEPS + 1):
                obs = result.observation
                
                # Call the LLM to decide the next security move
                response = openai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Current Security State: {obs.resources}"}
                    ],
                    temperature=0.1
                )
                action_str = response.choices[0].message.content.strip()
                
                # Execute the move
                try:
                    res_id, cmd = action_str.split(":")
                    action = CloudSentinelAction(resource_id=res_id, command=cmd)
                    result = await env.step(action)
                    
                    reward = result.reward or 0.0
                    rewards.append(reward)
                    steps_taken = step
                    final_score = result.observation.security_score
                    
                    log_step(step, action_str, reward, result.done, None)
                    
                    if result.done:
                        break
                except Exception as e:
                    log_step(step, action_str, 0.0, False, str(e))

            success = final_score >= 1.0
            log_end(success, steps_taken, final_score, rewards)

        except Exception as e:
            log_end(False, steps_taken, 0.0, rewards)

if __name__ == "__main__":
    asyncio.run(main())