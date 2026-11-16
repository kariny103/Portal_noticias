"""
Serializers — model para JSON (Aula 13). É o "ModelForm da API".

Regras seguidas:
  - fields sempre listados explicitamente (nada de "__all__");
  - o campo `organizacao` NUNCA aparece: o blog vem do usuário logado;
  - campos relacionados (categoria, autor, tags) só aceitam registros do
    blog do usuário — o mesmo cuidado dos selects do PostForm (Aula 14);
  - a regra de negócio da P1 (conteúdo mínimo) também protege a API.
"""
from rest_framework import serializers

from core.utils import org_atual

from .models import Autor, Categoria, Post, Tag


class DaOrganizacaoSerializer(serializers.ModelSerializer):
    """Base: filtra pelo blog do usuário o queryset de todo campo relacionado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.org = org_atual(request) if request else None
        for campo in self.fields.values():
            # ManyToMany (ex.: tags) guarda o campo "de verdade" em child_relation
            relacao = getattr(campo, 'child_relation', campo)
            if getattr(relacao, 'queryset', None) is not None:
                relacao.queryset = relacao.queryset.filter(organizacao=self.org)

    def _validar_nome_unico(self, nome):
        """
        Unicidade POR BLOG (UniqueConstraint organizacao + nome). Como
        `organizacao` não está no serializer, o DRF não valida isso
        sozinho — sem esta checagem o banco estouraria IntegrityError.
        """
        existentes = self.Meta.model.objects.filter(organizacao=self.org, nome__iexact=nome)
        if self.instance is not None:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError('Já existe um registro com este nome neste blog.')
        return nome


class CategoriaSerializer(DaOrganizacaoSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']

    def validate_nome(self, value):
        return self._validar_nome_unico(value)


class TagSerializer(DaOrganizacaoSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'nome']

    def validate_nome(self, value):
        return self._validar_nome_unico(value)


class AutorSerializer(DaOrganizacaoSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nome', 'email', 'bio']


class PostSerializer(DaOrganizacaoSerializer):
    """
    O `status` é só leitura: a mudança de estado (rascunho -> revisão ->
    publicado) continua sendo feita pelo Painel Editorial, que é onde
    está o fluxo de aprovação editorial. Pela API, toda matéria nova
    nasce como rascunho.
    """

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'titulo', 'resumo', 'conteudo',
            'categoria', 'autor', 'tags',
            'status', 'status_display',
            'data_criacao', 'data_publicacao', 'visualizacoes',
        ]
        read_only_fields = ['status', 'data_criacao', 'data_publicacao', 'visualizacoes']

    def validate_conteudo(self, value):
        """Feature 2 da P1 na API: mesmo limite do PostForm.clean_conteudo."""
        conteudo = (value or '').strip()
        if len(conteudo) < Post.CONTEUDO_MINIMO:
            raise serializers.ValidationError(
                f'O conteúdo da matéria precisa ter pelo menos {Post.CONTEUDO_MINIMO} '
                f'caracteres (atualmente tem {len(conteudo)}).'
            )
        return conteudo
