from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_welcome_email(user_email, username):
    subject = 'Welcome to News Nexus – Your Daily Dose of News!'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user_email]

    text_content = f"Hi {username},\n\nWelcome to News Nexus! We’re thrilled to have you with us."
    html_content = render_to_string('welcomemail.html', {'username': username, 'user_email': user_email})

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
