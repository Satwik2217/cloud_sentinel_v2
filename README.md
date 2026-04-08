---
title: Cloud Sentinel
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
- openenv
---

# 🛡️ Cloud Sentinel: Phase 2 RL Environment

Cloud Sentinel is a high-utility Cybersecurity environment designed for the OpenEnv benchmark. 

## 🚀 Overview
The agent acts as a Cloud Security Engineer tasked with securing 5 vulnerable servers. 
- **Security Goal:** All servers must be `is_public=False` AND `is_encrypted=True`.
- **Action Space:** `resource_id:command` (Commands: `revoke_access`, `encrypt`).
- **Reward:** +0.1 for every security hardening action taken.

## 📊 Tasks
1. **Easy (`secure-one`):** Harden at least one resource.
2. **Medium (`secure-three`):** Harden three resources (60% compliance).
3. **Hard (`full-hardening`):** 100% network hardening.

## 📐 Grader Logic
The environment uses a deterministic scoring system:
- **Incremental Reward:** +0.1 for each valid hardening step (max 10 steps).
- **Security Score:** A normalized value [0.0 - 1.0] representing total network compliance.
- **Completion:** Each task ID triggers a specific threshold check in the evaluation loop.

## 🛠️ Tech Stack
- **Runtime:** FastAPI
- **Model Support:** OpenAI-compatible (Llama 3, Qwen 2.5)
- **Framework:** OpenEnv-Core