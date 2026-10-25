from django.shortcuts import render, redirect
from .models import HoneypotHit

def home_redirect(request):
    """Show the public landing page at the site root."""
    return redirect('index')

def decoy_admin(request):
    HoneypotHit.objects.create(
        trigger_type='decoy_admin',
        path=request.path,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        extra_info=f"Method: {request.method}"
    )
    return render(request, 'security/decoy_admin.html')