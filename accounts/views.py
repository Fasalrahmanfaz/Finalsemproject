from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import User, EmailVerificationToken, PasswordResetOTP
from .forms import (CustomerRegistrationForm, BandManagerRegistrationForm,
                    LoginForm, PasswordResetRequestForm, OTPVerificationForm,
                    SetNewPasswordForm, ProfileUpdateForm)
import uuid


def send_verification_email(user, request):
    token = str(uuid.uuid4()).replace('-', '')
    EmailVerificationToken.objects.update_or_create(
        user=user, defaults={'token': token}
    )
    verification_url = request.build_absolute_uri(f'/accounts/verify-email/{token}/')
    send_mail(
        subject='Verify Your Bandez Account',
        message=f'''Hi {user.first_name},

Welcome to Bandez! Please verify your email by clicking the link below:

{verification_url}

This link expires in 24 hours.

— The Bandez Team''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_email_verified = True
            user.save()
            # send_verification_email(user, request)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('accounts:login')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register_customer.html', {'form': form})


def register_band_manager(request):
    if request.method == 'POST':
        form = BandManagerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_email_verified = True
            user.save()
            # send_verification_email(user, request)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('accounts:login')
    else:
        form = BandManagerRegistrationForm()
    return render(request, 'accounts/register_band_manager.html', {'form': form})


def verify_email(request, token):
    try:
        verification = EmailVerificationToken.objects.get(token=token)
        if verification.is_valid():
            user = verification.user
            user.is_email_verified = True
            user.save()
            verification.delete()
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.error(request, 'Verification link has expired. Please request a new one.')
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    return redirect('accounts:login')


def user_login(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.session.get('timeout_message'):
        messages.warning(request, 'Your session expired due to inactivity. Please log in again.')
        del request.session['timeout_message']

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email=email)
                if user_obj.is_locked_out():
                    remaining = int((user_obj.lockout_until - timezone.now()).seconds / 60) + 1
                    messages.error(request, f'Account locked due to too many failed attempts. Try again in {remaining} minutes.')
                    return render(request, 'accounts/login.html', {'form': form})
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                return render(request, 'accounts/login.html', {'form': form})

            user = authenticate(request, username=email, password=password)
            if user is not None:
                if not user.is_email_verified:
                    messages.warning(request, 'Please verify your email before logging in.')
                    return render(request, 'accounts/login.html', {'form': form})
                user.failed_login_attempts = 0
                user.lockout_until = None
                user.save()
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect_by_role(user)
            else:
                user_obj.failed_login_attempts += 1
                if user_obj.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    user_obj.lockout_until = timezone.now() + timezone.timedelta(minutes=settings.LOCKOUT_DURATION)
                    messages.error(request, f'Too many failed attempts. Account locked for {settings.LOCKOUT_DURATION} minutes.')
                else:
                    remaining = settings.MAX_LOGIN_ATTEMPTS - user_obj.failed_login_attempts
                    messages.error(request, f'Invalid password. {remaining} attempts remaining.')
                user_obj.save()
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def redirect_by_role(user):
    if user.role == 'admin' or user.is_staff:
        return redirect('core:admin_dashboard')
    elif user.role == 'band_manager':
        return redirect('bands:manager_dashboard')
    else:
        return redirect('core:customer_dashboard')


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp = PasswordResetOTP.generate_otp()
                PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
                PasswordResetOTP.objects.create(user=user, otp=otp)
                send_mail(
                    subject='Bandez Password Reset OTP',
                    message=f'''Hi {user.first_name},

Your OTP for password reset is: {otp}

This OTP is valid for 30 minutes. Do not share it with anyone.

— The Bandez Team''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
                request.session['reset_email'] = email
                messages.success(request, 'OTP sent to your email address.')
                return redirect('accounts:verify_otp')
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def verify_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(email=email)
                otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).last()
                if otp_obj and otp_obj.is_valid():
                    request.session['reset_verified'] = True
                    otp_obj.is_used = True
                    otp_obj.save()
                    return redirect('accounts:set_new_password')
                else:
                    messages.error(request, 'Invalid or expired OTP.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = OTPVerificationForm()
    return render(request, 'accounts/verify_otp.html', {'form': form})


def set_new_password(request):
    if not request.session.get('reset_verified'):
        return redirect('accounts:password_reset')

    email = request.session.get('reset_email')
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                user.set_password(form.cleaned_data['password1'])
                user.save()
                del request.session['reset_verified']
                del request.session['reset_email']
                messages.success(request, 'Password reset successfully! Please log in.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = SetNewPasswordForm()
    return render(request, 'accounts/set_new_password.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_email_verified=False)
            send_verification_email(user, request)
            messages.success(request, 'Verification email resent!')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with that email.')
    return redirect('accounts:login')


@login_required
def delete_account(request):
    """Allow customers and band managers to delete their own account."""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('core:home')
    return render(request, 'accounts/delete_account.html')
