from django.shortcuts import redirect
from django.urls import reverse
from .models import CompanySettings

class RequireCompanySettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)
            
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path.startswith('/api/'):
            return self.get_response(request)
            
        if request.path == reverse('login') or request.path == reverse('logout'):
            return self.get_response(request)
            
        # If user is authenticated and hitting an internal page
        if request.user.is_authenticated:
            # Avoid redirect loop
            if request.path != reverse('company_settings'):
                # Check if company settings exists
                if not CompanySettings.objects.exists():
                    from django.contrib import messages
                    messages.warning(request, "Por favor, configure os dados da sua empresa antes de continuar.")
                    return redirect('company_settings')

        return self.get_response(request)
