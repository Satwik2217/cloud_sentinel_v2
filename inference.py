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

# --- MANDATORY CONFIGURATION ---
# 1. Use the standard OpenAI-compatible endpoint for Hugging Face
# The Router URL is typically https://router.huggingface.co/v1
API_BASE_URL = "https://router.huggingface.co/v1"

# 2. Use a supported model name. Qwen 2.5 is excellent for this task.
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

HF_TOKEN = os.getenv("HF_TOKEN")
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
    # URGENT: Must print exactly: [START] task=TASK_ID, env=ENV_NAME, model=MODEL_NAME
    print(f"[START] task={task}, env={env}, model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    # URGENT: Must print exactly: [STEP] step=NUM reward=VAL done=BOOL action=STRING
    # No labels like "ACTION:" or extra braces.
    print(f"[STEP] step={step} reward={reward:.2f} done={str(done).lower()} action={action}", flush=True)

def log_end(task: str, success: bool, steps: int, score: float) -> None:
    # URGENT: Must print exactly: [END] task=TASK_ID score=VAL steps=NUM
    print(f"[END] task={task} score={score:.3f} steps={steps}", flush=True)

async def main():
    if not HF_TOKEN or HF_TOKEN == "your_hf_token_here":
        print("ERROR: HF_TOKEN not found or is still the placeholder. Please check your .env file.")
        return

    # Print config for debugging (won't affect grader as long as logs are present)
    print(f"DEBUG: Using Base URL: {API_BASE_URL}", flush=True)
    print(f"DEBUG: Using Model: {MODEL_NAME}", flush=True)

    # Initialize the OpenAI Client pointing to the Standard Router
    openai_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    # Required tasks for Phase 2
    tasks_to_run = ["secure-one", "secure-three", "full-hardening"]

    for current_task in tasks_to_run:
        # Connect to your environment Space
        async with CloudSentinelEnv(base_url=ENV_URL) as env:    
            log_start(task=current_task, env="cloud_sentinel", model=MODEL_NAME)
            
            steps_taken = 0
            final_score = 0.0
            
            try:
                # Reset for the specific task
                result = await env.reset(task_id=current_task)
                
                for step in range(1, MAX_STEPS + 1):
                    obs = result.observation
                    
                    try:
                        # Request next action from LLM
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
                        # Improved error message for debugging
                        print(f"LLM Error: {str(e)}", flush=True)
                        break

                    try:
                        # Parse and execute action
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

                # Logic to determine if task was passed (at least 0.05 baseline)
                success = final_score >= 0.05 
                log_end(current_task, success, steps_taken, final_score)

            except Exception as e:
                print(f"Task Failed: {e}", flush=True)
                log_end(current_task, False, steps_taken, 0.0)

if __name__ == "__main__":
    asyncio.run(main())