# diverge/middleware.py

from django.shortcuts import redirect
from django.conf import settings

class SkipLoginForDevMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignora login para desenvolvedor quando DEBUG = True
        if settings.DEBUG and request.user.is_authenticated and request.user.is_superuser:
            # Caso seja superusuário, ignora o login e redireciona para a página inicial
            return redirect('home')  # Ou a URL que você deseja redirecionar

        response = self.get_response(request)
        return response
