import random
import math
import favicon

from .rsa import *
from .models import Password
from mechanize import Browser

from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail

browser = Browser()
browser.set_handle_robots(False)

def OTP_code_generator():
    digits="0123456789"
    OTP=""
    for i in range(6):
        OTP+=digits[math.floor(random.random()*10)]
    return OTP

# Create your views here.
def home(request):
    if request.method == "POST":
        if "register-form" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            if password != password2: 
                msg = "Registration Failed: Passwords do not match"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            elif User.objects.filter(username=username).exists():
                msg = f"Registration Failed: {username} already exists"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            elif User.objects.filter(email=email).exists():
                msg = f"Registration Failed: {email} already exists"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                User.objects.create_user(username, email, password)
                new_user = authenticate(request, username=username, password=password2)
                if new_user is not None:
                    login(request, new_user)
                    msg = f"Login succeeded: {username}, welcome to Secretary"
                    messages.success(request, msg)
                    return HttpResponseRedirect(request.path)

        elif "logout" in request.POST:
            msg = f"Logout succeeded: {request.user}, see you again"
            logout(request)
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif 'login-form' in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            new_login = authenticate(request, username=username, password=password)
            if new_login is None:
                msg = f"Login Failed: Your username or password is incorrect"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                otp = OTP_code_generator()
                global global_OTP
                global_OTP = otp
                send_mail(
                    "Secretary Password Manager: Email Confirmation",
                    f"{otp} is your OTP",
                    settings.EMAIL_HOST_USER,
                    [new_login.email],
                    fail_silently=False,
                )
                return render(request, "home.html", {
                    "code":otp, 
                    "user" :new_login,
                })

        elif "confirm" in request.POST:
            input_code = request.POST.get("code")
            user = request.POST.get("user")
            if input_code != global_OTP:
                msg = f"Verification Failed:{input_code} is wrong"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                login(request, User.objects.get(username=user))
                msg = f"Login succeeded: {request.user}, welcome to Secretary"
                messages.success(request, msg)
                return HttpResponseRedirect(request.path)

        elif "add-password" in request.POST:
            url = request.POST.get("url")
            email = request.POST.get("email")
            password = request.POST.get("password")
            # print(email)
            # print(password)
            
            #ecrypt data
            p_q = generate_two_primes()
            n = calculate_N(p_q)
            phi = calculate_phi(p_q)
            e = select_e(phi)
            d = mod_inverse(e, phi)
            public = (e, n)
            private = (d, n)
            encrypted_email = encrypt_RSA(email, public)
            encrypted_password = encrypt_RSA(password, public)

            #get title of the website
            try:
                browser.open(url)
                title = browser.title()
            except:
                title = url
            #get the logo's URL
            try:
                icon = favicon.get(url)[0].url
            except:
                icon = "https://cdn-icons-png.flaticon.com/128/1006/1006771.png"

            # print(encrypted_email)
            # print(encrypted_password)
            # print(title)
            # print(icon)
            decrypt_email = decrypt_RSA(encrypted_email, private)
            decrypt_password = decrypt_RSA(encrypted_password, private)
            saved_email = ','.join(decrypt_email).replace(',','')
            saved_password = ','.join(decrypt_password).replace(',','')

            # print(saved_email)
            # print(saved_password)

            # Save data in database
            new_password = Password.objects.create(
                user=request.user,
                name=title,
                logo=icon,
                email= saved_email,
                password= saved_password
            )
            print(new_password)
    
            msg = f"Add succeeded: Added new password for website - {title}"
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

    return render(request, "home.html", {})
