"""
App "core" — o que é transversal ao sistema todo (Aula 14).

P2, pilar 1: multi-organização. No Portal de Notícias, cada
"organização" é um BLOG (ex.: Portal Notícias Maricá, Portal Notícias
Niterói). Todos ficam no mesmo banco de dados, mas cada blog só
enxerga as suas próprias matérias, categorias, tags e autores.

Estratégia usada: coluna discriminadora (uma ForeignKey para
Organizacao em todo model de negócio).
"""
from django.contrib.auth.models import User
from django.db import models


class Organizacao(models.Model):
    """O "inquilino" (tenant) do sistema: aqui, um blog de notícias."""

    nome = models.CharField(max_length=120)
    slug = models.SlugField(
        max_length=60, unique=True,
        help_text='Identificador usado no endereço público do blog (ex.: /blog/marica/).',
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organização (blog)'
        verbose_name_plural = 'Organizações (blogs)'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class DaOrganizacao(models.Model):
    """
    Base abstrata: todo model com dados de negócio herda daqui e ganha
    a FK `organizacao`. Como é abstract, o Django NÃO cria tabela para
    ela — o campo é copiado para cada model filho.
    """

    organizacao = models.ForeignKey(
        'core.Organizacao', on_delete=models.PROTECT,
        verbose_name='Organização (blog)',
    )
    # Migração feita em 3 etapas para não perder os dados da P1:
    #   noticias/0003 -> FK com null=True
    #   noticias/0004 -> RunPython preenche o blog padrão
    #   noticias/0005 -> FK obrigatória (null=False)

    class Meta:
        abstract = True


class Perfil(models.Model):
    """
    Liga o usuário do Django à organização (blog) a que ele pertence.
    Na Aula 15 entra o campo `papel` (administrador / operador).
    """

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    organizacao = models.ForeignKey(
        Organizacao, on_delete=models.PROTECT, related_name='perfis',
        verbose_name='Organização (blog)',
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'{self.usuario.username} ({self.organizacao})'
