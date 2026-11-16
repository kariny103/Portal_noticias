"""
Views da API com as generics do DRF (Aula 13).

  ListCreateAPIView            -> GET lista, POST cria
  RetrieveUpdateDestroyAPIView -> GET detalha, PUT/PATCH atualiza, DELETE apaga

Multi-organização (Aula 14): em vez de `queryset = Model.objects.all()`
(que vazaria os dados de todos os blogs), cada view usa get_queryset()
filtrando pelo blog do usuário logado. Um id de outro blog dá 404.
"""
from django.db.models import ProtectedError
from rest_framework import generics, permissions, serializers

from core.utils import org_atual

from .models import Autor, Categoria, Post, Tag
from .serializers import AutorSerializer, CategoriaSerializer, PostSerializer, TagSerializer


class TemOrganizacao(permissions.BasePermission):
    """Só entra na API quem está logado E tem um Perfil ligado a um blog."""

    message = 'Seu usuário não está ligado a nenhum blog (crie um Perfil no Admin).'

    def has_permission(self, request, view):
        return org_atual(request) is not None


class DaOrganizacaoMixin:
    """Tudo o que é comum às views da API: filtro, criação e exclusão por blog."""

    model = None
    permission_classes = [permissions.IsAuthenticated, TemOrganizacao]

    def get_queryset(self):
        return self.model.objects.filter(organizacao=org_atual(self.request))

    def perform_create(self, serializer):
        # O blog vem do usuário logado, nunca do JSON enviado.
        serializer.save(organizacao=org_atual(self.request))

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            # Ex.: apagar uma categoria que ainda tem matérias (on_delete=PROTECT)
            raise serializers.ValidationError(
                'Este registro está em uso por matérias e não pode ser apagado.'
            )


# --- Posts (matérias) ---------------------------------------------------

class PostListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    model = Post
    serializer_class = PostSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('categoria', 'autor').prefetch_related('tags')


class PostDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Post
    serializer_class = PostSerializer


# --- Categorias -----------------------------------------------------------

class CategoriaListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    model = Categoria
    serializer_class = CategoriaSerializer


class CategoriaDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Categoria
    serializer_class = CategoriaSerializer


# --- Tags -------------------------------------------------------------------

class TagListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    model = Tag
    serializer_class = TagSerializer


class TagDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Tag
    serializer_class = TagSerializer


# --- Autores ------------------------------------------------------------------

class AutorListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    model = Autor
    serializer_class = AutorSerializer


class AutorDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Autor
    serializer_class = AutorSerializer
