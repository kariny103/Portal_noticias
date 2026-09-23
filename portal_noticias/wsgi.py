"""
Configuração WSGI do projeto portal_noticias.
Ponte usada para colocar o projeto no ar em um servidor de produção.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_noticias.settings')

application = get_wsgi_application()
