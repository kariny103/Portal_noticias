"""
URLs da API (Aula 13) — arquivo separado das URLs de páginas.
Incluído no urls.py do projeto com o prefixo /api/.

Endereços finais:
  /api/posts/        /api/posts/<id>/
  /api/categorias/   /api/categorias/<id>/
  /api/tags/         /api/tags/<id>/
  /api/autores/      /api/autores/<id>/
  /api/dashboard/    (só GET: métricas do blog — Aula 17)
"""
from django.urls import path

from . import api_views

urlpatterns = [
    path('posts/', api_views.PostListCreate.as_view(), name='api_posts'),
    path('posts/<int:pk>/', api_views.PostDetail.as_view(), name='api_post_detalhe'),
    path('categorias/', api_views.CategoriaListCreate.as_view(), name='api_categorias'),
    path('categorias/<int:pk>/', api_views.CategoriaDetail.as_view(), name='api_categoria_detalhe'),
    path('tags/', api_views.TagListCreate.as_view(), name='api_tags'),
    path('tags/<int:pk>/', api_views.TagDetail.as_view(), name='api_tag_detalhe'),
    path('autores/', api_views.AutorListCreate.as_view(), name='api_autores'),
    path('autores/<int:pk>/', api_views.AutorDetail.as_view(), name='api_autor_detalhe'),
    path('dashboard/', api_views.DashboardApi.as_view(), name='api_dashboard'),
]
