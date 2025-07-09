import os
import requests
import logging

def send_email_notification(subject: str, body: str, to_email: str = None) -> bool:
    """
    Envia notificação por email usando Resend API
    
    Args:
        subject: Assunto do email
        body: Corpo do email (HTML)
        to_email: Email de destino (opcional, usa EMAIL_TO se não fornecido)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Configurações do Resend
        resend_api_key = os.getenv('RESEND_API_KEY')
        email_from = os.getenv('EMAIL_FROM')
        email_to = to_email or os.getenv('EMAIL_TO')
        
        if not resend_api_key or not email_from or not email_to:
            logging.warning("Configurações de email não encontradas. Pulando notificação.")
            return False
        
        # URL da API do Resend
        url = "https://api.resend.com/emails"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        
        # Dados do email
        data = {
            "from": email_from,
            "to": [email_to],
            "subject": subject,
            "html": body
        }
        
        # Envia email via API
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logging.info(f"Email enviado com sucesso para {email_to}")
            return True
        else:
            logging.error(f"Erro ao enviar email: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        logging.error(f"Erro ao enviar email: {str(e)}")
        return False

def send_test_email() -> bool:
    """Envia email de teste para verificar configurações"""
    subject = "🧪 Teste - Trading Bot"
    body = """
    <h2>✅ Teste de Notificação</h2>
    <p>Este é um email de teste do Trading Bot.</p>
    <p>Se você recebeu este email, as configurações estão funcionando corretamente!</p>
    <hr>
    <p><em>Enviado automaticamente pelo Trading Bot</em></p>
    """
    
    return send_email_notification(subject, body)

if __name__ == "__main__":
    # Teste da função
    print("Enviando email de teste...")
    success = send_test_email()
    if success:
        print("✅ Email de teste enviado com sucesso!")
    else:
        print("❌ Falha ao enviar email de teste")