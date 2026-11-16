"""
Utilitários de multi-organização (Aula 14 — "A Regra de Ouro").

`org_atual(request)` é o ÚNICO lugar do sistema que decide qual é a
organização (blog) do usuário. Ela vem sempre do usuário logado
(request.user.perfil), NUNCA da URL ou do formulário.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Perfil


def org_atual(request):
    """Organização (blog) do usuário logado, ou None se ele não tiver Perfil."""
    try:
        return request.user.perfil.organizacao
    except (AttributeError, Perfil.DoesNotExist):
        return None


def organizacao_required(view):
    """
    Decorator para as telas internas (Painel Editorial e CRUD):

    1. exige login (@login_required) — sem login não existe organização;
    2. exige que o usuário tenha um Perfil ligado a um blog.

    Armadilha do slide 17: um superusuário sem Perfil geraria
    RelatedObjectDoesNotExist em request.user.perfil. Aqui ele recebe
    uma mensagem clara e é mandado para o Admin, onde pode criar o Perfil.
    """
    @wraps(view)
    @login_required
    def _view(request, *args, **kwargs):
        org = org_atual(request)
        if org is None:
            messages.error(
                request,
                'Seu usuário não está ligado a nenhum blog. Crie um Perfil para ele '
                'no Django Admin (Core > Perfis) e tente novamente.',
            )
            return redirect('admin:index' if request.user.is_staff else 'home')
        request.org = org
        return view(request, *args, **kwargs)

    return _view
