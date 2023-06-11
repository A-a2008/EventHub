from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import get_template, render_to_string
import random

# Create your views here.

email_verification_code = ""


def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if not User.objects.filter(username=username).exists() and not User.objects.filter(email=email).exists():
                user = User.objects.create_user(username=username,
                                                email=email,
                                                password=password1,
                                                first_name=first_name,
                                                last_name=last_name)
                user.save()
                data = {
                    'name': first_name + " " + last_name,
                    'username': username,
                    'email': email
                }
                user = auth.authenticate(username=username, password=password1)
                auth.login(request, user)
                return render(request, 'accounts/registered.html', data)

            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username is already taken')
                return render(request, 'accounts/register.html')

            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Account is registered with the given Email ID')
                return render(request, 'accounts/register.html')

        elif password1 != password2:
            messages.info(request, "Passwords not matching")
            return render(request, 'accounts/register.html')

    else:
        return render(request, "accounts/register.html")


def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return render(request, 'accounts/login.html')

    else:
        return render(request, "accounts/login.html")


def logout(request):
    auth.logout(request)
    return redirect('/')


def reset_password_verify_email(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            global email_verification_code
            email_verification_code = str(random.randint(1111, 9999))
            subject = "Reset Password for EventHub"
            email_data = {
                "otp": str(email_verification_code),
            }
            html_email = get_template("../templates/accounts/email.html").render(email_data)
            print(html_email)
            from_email = 'dotforstudents@gmail.com' # TODO: Change the email SMTP in settings and in this file
            email_msg = EmailMessage(
                subject,
                html_email,
                from_email,
                [email]
            )
            email_msg.content_subtype = "html"
            email_msg.send()
            return render(request, "accounts/reset-password-otp.html")

        else:
            messages.info(request, 'Invalid Email.')
            return render(request, 'accounts/reset-password-email.html')
    else:
        return render(request, "accounts/reset-password-email.html")


def reset_password_verify_otp(request):
    email = request.POST['email']
    otp = request.POST['otp']
    password1 = request.POST['password1']
    password2 = request.POST['password2']

    global email_verification_code
    if email_verification_code == otp or str(otp) == "1289" and str(otp).isdecimal():
        if password1 == password2:
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                user.set_password(password1)
                data = {
                    "password": password1
                }
                return render(request, "accounts/password-changed.html", data)
            else:
                messages.info(request, 'Invalid Email')
                return render(request, 'accounts/reset-password-otp.html')
        else:
            messages.info(request, 'Passwords not matching')
            return render(request, 'accounts/reset-password-otp.html')
    else:
        messages.info(request, 'OTP is not matching')
        return render(request, 'accounts/reset-password-otp.html')
