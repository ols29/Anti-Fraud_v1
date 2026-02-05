import os
import httpx
import redis
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Anti-Fraud System v1")
cache = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

ABSTRACT_EMAIL_KEY = "4f3453b316314de2b4858028a960a338"
ABSTRACT_URL = "https://emailreputation.abstractapi.com/v1/"

async def get_email_intelligence(email: str):
    params = {
        "api_key": ABSTRACT_EMAIL_KEY,
        "email": email
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(ABSTRACT_URL, params=params, timeout=10.0)
            print(f"--- REPUTATION LOG: {response.status_code} | {response.text} ---", flush=True)
            return response.json()
        except Exception as e:
            print(f"--- ERRO DE CONEXÃO: {e} ---", flush=True)
            return None

@app.post("/v1/check-transaction")
async def check_transaction(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"decision": "ERROR", "total_risk_score": 0, "flags": ["JSON INVÁLIDO"]}

    card_hash = data.get("card_hash", "unknown")
    email = data.get("email", "")
    score = 0
    flags = []

    try:
        attempts = cache.incr(f"velocity:{card_hash}")
        if attempts == 1: cache.expire(f"velocity:{card_hash}", 300)
        if attempts > 3:
            score += 70
            flags.append("Alta velocidade (Carding)")
    except Exception as e:
        attempts = 0

    if email:
        email_data = await get_email_intelligence(email)
        if email_data:
            quality = email_data.get('email_quality', {})
            
            if quality.get('is_disposable') is True:
                score += 50
                flags.append("E-mail temporário detectado")

            # 2. Verifica o score de qualidade da Abstract
            q_score = quality.get('score', 1.0)
            if float(q_score) < 0.7:
                score += 30
                flags.append(f"Baixa reputação (Quality Score: {q_score})")

            risk = email_data.get('email_risk', {})
            if risk.get('domain_risk_status') == "high":
                score += 20
                flags.append("Domínio de alto risco")

    # --- Yes or No? ---
    decision = "APPROVE"
    if score >= 90: decision = "BLOCK"
    elif score >= 40: decision = "REVIEW"

    return {
        "decision": decision,
        "total_risk_score": score,
        "flags": flags,
        "analysis_summary": {"attempts": attempts}
    }