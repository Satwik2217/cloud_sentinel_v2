import asyncio
import os
import textwrap
import traceback
from typing import List, Optional
from openai import OpenAI

# Try to load local .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from client import CloudSentinelEnv
from models import CloudSentinelAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/hf-inference/v1")
API_KEY = os.getenv("API_KEY", os.getenv("HF_TOKEN", "your_hf_token_here"))
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

ENV_URL = "https://satwik2217-cloud-sentinel.hf.space"
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
""").strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task}, env={env}, model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(f"[STEP] step={step} reward={reward:.2f} done={str(done).lower()} action={action}", flush=True)

def log_end(task: str, success: bool, steps: int, score: float) -> None:
    print(f"[END] task={task} score={score:.3f} steps={steps}", flush=True)

async def main():
    if not API_KEY or API_KEY == "your_hf_token_here":
        print("ERROR: API_KEY (or HF_TOKEN fallback) not found. Please check your .env file or environment.")
        return

    print(f"DEBUG: Using Base URL: {API_BASE_URL}", flush=True)
    print(f"DEBUG: Using Model: {MODEL_NAME}", flush=True)

    openai_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    tasks_to_run = ["secure-one", "secure-three", "full-hardening"]

    for current_task in tasks_to_run:
        async with CloudSentinelEnv(base_url=ENV_URL) as env:    
            log_start(task=current_task, env="cloud_sentinel", model=MODEL_NAME)
            
            steps_taken = 0
            final_score = 0.0
            
            try:
                result = await env.reset(task_id=current_task)
                
                for step in range(1, MAX_STEPS + 1):
                    obs = result.observation
                    
                    try:
                        response = openai_client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": f"Task: {current_task}. Resources: {obs.resources}"}
                            ],
                            temperature=0.1
                        )
                        if not response or not response.choices:
                            print(f"LLM Error: No choices in response: {response}", flush=True)
                            break
                        action_str = response.choices[0].message.content.strip()
                    except Exception as e:
                        print(f"LLM Error: {str(e)}", flush=True)
                        break

                    try:
                        res_id, cmd = action_str.split(":")
                        action = CloudSentinelAction(resource_id=res_id, command=cmd)
                        result = await env.step(action)
                        
                        steps_taken = step
                        final_score = result.observation.security_score
                        
                        log_step(step, action_str, result.reward, result.done, None)
                        
                        if result.done:
                            break
                    except Exception as e:
                        log_step(step, action_str, 0.0, False, str(e))

                success = final_score >= 0.05 
                log_end(current_task, success, steps_taken, final_score)

            except Exception as e:
                print(f"Task Failed: {e}", flush=True)
                log_end(current_task, False, steps_taken, 0.0)

if __name__ == "__main__":
    asyncio.run(main())