"""
Django Admin — painel administrativo gerado automaticamente a partir
dos models (Aula 4). Útil para cadastrar Categorias, Tags e Autores
rapidamente antes de criar os Posts pelo formulário do site.
"""
from django.contrib import admin

from .models import Categoria, Tag, Autor, Post, Comentario


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email']
    search_fields = ['nome', 'email']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'autor', 'status', 'visualizacoes', 'data_criacao', 'data_publicacao']
    list_filter = ['status', 'categoria', 'autor']
    search_fields = ['titulo', 'conteudo']
    filter_horizontal = ['tags']
    date_hierarchy = 'data_criacao'


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['nome_autor', 'post', 'data_criacao']
    search_fields = ['nome_autor', 'texto']
    list_filter = ['post']
