import requests
import uuid

API_URL = "http://localhost:8000/v1/check-transaction"

def executar_teste_real(email_para_teste, valor_transacao=150.00):
    cartao_fake_id = str(uuid.uuid4())
    
    payload = {
        "card_hash": cartao_fake_id,
        "email": email_para_teste,
        "amount": valor_transacao,
        "ip": "186.204.121.45"  
    }

    print(f"\n[+] Enviando transação para análise...")
    print(f"    E-mail: {email_para_teste} | Valor: R${valor_transacao}")

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            res = response.json()
            print(f"--- RESULTADO DO ANTI-FRAUD ---")
            print(f"DECISÃO: {res.get('decision')}")
            print(f"SCORE DE RISCO: {res.get('total_risk_score')}")
            lista_flags = res.get('flags', [])
            print(f"FLAGS: {', '.join(lista_flags) if lista_flags else 'Nenhuma'}")
            print(f"-------------------------------")
        else:
            print(f"[!] Erro no Servidor: Status {response.status_code}")
            print(f"    Detalhe: {response.text}")

    except requests.exceptions.ConnectionError:
        print("[!] ERRO: Conexão recusada. O Docker está rodando com 'docker compose up'?")
    except Exception as e:
        print(f"[!] Erro inesperado: {e}")

if __name__ == "__main__":
    print("--- SentinelCard: Sistema de Validação Real ---")
    email_usuario = input("Digite o e-mail para testar a fraude: ").strip()
    
    if email_usuario:
        executar_teste_real(email_usuario)
    else:
        print("[!] E-mail inválido.")