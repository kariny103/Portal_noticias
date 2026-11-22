"""
urls.py do app noticias — criado manualmente (o startapp não gera
este arquivo, como explicado na Aula 5). Conecta cada endereço a
uma view.

P2: as páginas públicas ficam dentro do blog (/blog/<slug>/...).
As páginas internas (painel e CRUD) não levam o blog na URL: ele vem
do usuário logado.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Público
    path('', views.home, name='home'),
    path('blog/<slug:blog_slug>/', views.lista_posts, name='lista_posts'),
    path('blog/<slug:blog_slug>/categoria/<int:categoria_id>/', views.posts_por_categoria, name='posts_por_categoria'),
    path('blog/<slug:blog_slug>/post/<int:pk>/', views.detalhe_post, name='detalhe_post'),

    # CRUD (exige login)
    path('novo/', views.novo_post, name='novo_post'),
    path('post/<int:pk>/editar/', views.editar_post, name='editar_post'),
    path('post/<int:pk>/excluir/', views.excluir_post, name='excluir_post'),

    # Painel e fluxo editorial (exige login)
    path('painel/', views.painel_editorial, name='painel_editorial'),
    path('post/<int:pk>/enviar-revisao/', views.enviar_para_revisao, name='enviar_revisao'),
    path('post/<int:pk>/devolver-rascunho/', views.devolver_rascunho, name='devolver_rascunho'),
    path('post/<int:pk>/publicar/', views.publicar_post, name='publicar_post'),
    path('post/<int:pk>/despublicar/', views.despublicar_post, name='despublicar_post'),

    # Dashboard e relatório (P2, Aula 17 — exige login)
    path('painel/dashboard/', views.dashboard, name='dashboard'),
    path('painel/dashboard/exportar.csv', views.exportar_csv, name='exportar_csv'),
]
