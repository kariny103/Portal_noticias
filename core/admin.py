from django.contrib import admin

from .models import Organizacao, Perfil


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'criada_em']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'organizacao']
    list_filter = ['organizacao']
    search_fields = ['usuario__username']
