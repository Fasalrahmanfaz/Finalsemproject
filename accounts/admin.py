from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_email_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'is_email_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Bandez Info', {'fields': ('role', 'phone', 'is_email_verified', 'failed_login_attempts', 'lockout_until')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Bandez Info', {'fields': ('email', 'role', 'phone')}),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'is_used']
