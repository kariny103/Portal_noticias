"""
Models do Portal de Últimas Notícias de Maricá.

Entidades pedidas no projeto: Post, Categoria, Tag, Autor, Comentário.
Cada classe aqui vira uma tabela no banco (via migrations) — exatamente
o que foi ensinado na Aula 4 (ORM do Django).
"""
from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Tag(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Autor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    bio = models.TextField(blank=True, help_text='Uma breve descrição do autor (opcional)')

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Post(models.Model):
    """
    O "livro" deste projeto: a entidade central do sistema.

    O campo `status` implementa o fluxo de publicação com aprovação
    editorial pedido no projeto (3 estados, mais que o mínimo de 2):

        RASCUNHO  -> REVISAO -> PUBLICADO
                  <-          <-
    """
    RASCUNHO = 'rascunho'
    REVISAO = 'revisao'
    PUBLICADO = 'publicado'

    STATUS_CHOICES = [
        (RASCUNHO, 'Rascunho'),
        (REVISAO, 'Em Revisão'),
        (PUBLICADO, 'Publicado'),
    ]

    titulo = models.CharField(max_length=200)
    resumo = models.CharField(
        max_length=300,
        help_text='Texto curto exibido na listagem e nas chamadas da matéria.',
    )
    conteudo = models.TextField()
    imagem_capa = models.ImageField(
        upload_to='capas/', blank=True, null=True,
        help_text='Opcional. Imagem exibida no topo da matéria.',
    )

    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='posts',
    )
    autor = models.ForeignKey(
        Autor, on_delete=models.PROTECT, related_name='posts',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=RASCUNHO,
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_publicacao = models.DateTimeField(blank=True, null=True)

    visualizacoes = models.PositiveIntegerField(
        default=0, verbose_name='Visualizações',
        help_text='Contador de acessos, usado no widget "Mais Lidas".',
    )

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-data_criacao']

    def __str__(self):
        return self.titulo

    @property
    def esta_publicado(self):
        return self.status == self.PUBLICADO


class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    nome_autor = models.CharField(max_length=100, verbose_name='Nome')
    email = models.EmailField()
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['data_criacao']

    def __str__(self):
        return f'Comentário de {self.nome_autor} em "{self.post.titulo}"'
