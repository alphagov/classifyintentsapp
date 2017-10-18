from notifications_python_client.notifications import NotificationsAPIClient
from flask import current_app

templates = {
    'confirm' : 'a071a344-7edf-4c56-8bfd-fa15b7a9eea3',
    'password_reset' : 'd374892e-e9f5-4cc4-90fb-e8f2f139d48c',
    'change_email' : 'f0462a68-201b-44ca-b0e0-9988aa580cbb'
    }

def send_email(to, subject, name, body, template):
    personalisation = {
        'subject': subject,
        'name': name,
        'body': body
    }

    notify_client = NotificationsAPIClient(current_app.config['NOTIFY_API_KEY'])

    response = notify_client.send_email_notification(
        email_address=to,
        template_id=templates[template],
        personalisation=personalisation,
        reference=None
    )
