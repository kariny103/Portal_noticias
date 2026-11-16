"""
urls.py do projeto — o "mapa" geral do site.

Segue o padrão da Aula 5: o projeto inclui o urls.py de cada app,
com o prefixo que escolhemos ('' = raiz, para o app noticias).

P2: páginas e API ficam separadas — a API mora em /api/ e tem o seu
próprio arquivo de rotas (noticias/api_urls.py), como na Aula 13.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Login/logout do site (template em noticias/templates/registration/)
    path('contas/', include('django.contrib.auth.urls')),
    # API REST (DRF) + login da Browsable API
    path('api/', include('noticias.api_urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('noticias.urls')),
]

# Em desenvolvimento (DEBUG=True), o Django serve os arquivos de mídia
# (imagens de capa enviadas pelo formulário) diretamente.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
