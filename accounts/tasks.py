from celery import shared_task
from django.core.mail import send_mail
from django.urls import reverse


@shared_task(bind=True, max_retries=2, autoretry_for=(Exception,))
def email_verify_task(self, url, email):
    subject = "Завершите регистрацию"
    message = f"Для завершения регистрации перейдите по ссылке \n {url}"
    mail_sent = send_mail(subject, message, None, [email])
    return mail_sent


@shared_task(bind=True, max_retries=2, autoretry_for=(Exception,))
def password_reset_task(self, url, email):
    subject = "Завершите сброс пароля"
    message = f"Для завершения сброса пароля перейдите по ссылке \n {url}"
    mail_sent = send_mail(subject, message, None, [email])
    return mail_sent
