import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

def send_email_notification(subject: str, body: str, to_email: str = None) -> bool:
    """
    Envia notificação por email
    
    Args:
        subject: Assunto do email
        body: Corpo do email (HTML)
        to_email: Email de destino (opcional, usa EMAIL_USER se não fornecido)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Configurações de email
        email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.getenv('EMAIL_PORT', '587'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            logging.warning("Configurações de email não encontradas. Pulando notificação.")
            return False
        
        # Email de destino
        if not to_email:
            to_email = email_user
        
        # Cria mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Adiciona corpo HTML
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Envia email
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        logging.info(f"Email enviado com sucesso para {to_email}")
        return True
        
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