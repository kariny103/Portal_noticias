"""
Models do Portal Notícias Maricá.

Entidades pedidas no projeto: Post, Categoria, Tag, Autor, Comentário.
Cada classe aqui vira uma tabela no banco (via migrations) — exatamente
o que foi ensinado na Aula 4 (ORM do Django).

P2 (Aula 14): todo model de negócio herda de DaOrganizacao e passa a
pertencer a um blog (organização). Cada blog só enxerga os seus dados.
"""
from django.db import models

from core.models import DaOrganizacao


class Categoria(DaOrganizacao):
    # Na P1 era unique=True (único no banco inteiro). Na P2 a unicidade é
    # POR BLOG: dois blogs podem ter a categoria "Esportes" cada um.
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['organizacao', 'nome'], name='categoria_unica_por_org',
            ),
        ]

    def __str__(self):
        return self.nome


class Tag(DaOrganizacao):
    nome = models.CharField(max_length=50)  # único por blog (ver constraints)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['organizacao', 'nome'], name='tag_unica_por_org',
            ),
        ]

    def __str__(self):
        return self.nome


class Autor(DaOrganizacao):
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    bio = models.TextField(blank=True, help_text='Uma breve descrição do autor (opcional)')

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Post(DaOrganizacao):
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

    # Regra de negócio (Feature 2 do P1): tamanho mínimo do texto de uma
    # matéria para que ela possa ir ao ar. Usado no PostForm e na view
    # de publicação.
    CONTEUDO_MINIMO = 50

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
        # P2, Aula 17: o dashboard sempre filtra por blog + período
        # (data_criacao) e agrupa por mês. Um índice composto nessa ordem
        # atende o filter, o order_by e o TruncMonth sem ler a tabela toda.
        indexes = [
            models.Index(fields=['organizacao', 'data_criacao'], name='post_org_data_idx'),
        ]

    def __str__(self):
        return self.titulo

    @property
    def esta_publicado(self):
        return self.status == self.PUBLICADO


class Comentario(DaOrganizacao):
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
