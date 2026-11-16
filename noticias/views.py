"""
Views — a lógica de cada página (Aula 5).

O padrão de sempre: a view busca os dados com o ORM e devolve uma
resposta, normalmente uma página renderizada por um template.

As views deste arquivo estão organizadas em três grupos:
  1. Público  -> o que qualquer visitante do portal vê
  2. CRUD     -> criar / editar / excluir matérias
  3. Editorial -> o fluxo de publicação (rascunho -> revisão -> publicado)

P2 — multi-organização (Aula 14). Cada organização é um BLOG:
  - Páginas públicas: o blog vem do endereço (/blog/<slug>/...). Elas só
    mostram conteúdo PUBLICADO daquele blog.
  - Páginas internas (Painel e CRUD): exigem login, e o blog vem SEMPRE
    do usuário logado (org_atual / request.org), nunca da URL ou do form.
  - Toda consulta parte de filter(organizacao=...), e todo
    get_object_or_404 recebe a organização: trocar o id na URL por o de
    uma matéria de outro blog devolve 404.
"""
from django.contrib import messages
from django.db.models import F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Organizacao
from core.utils import organizacao_required

from .forms import ComentarioForm, PostForm
from .models import Categoria, Post, Tag


def _menu_contexto(blog):
    """
    Dados que aparecem em quase toda página (menu do topo, barra lateral
    e rodapé): o blog atual, as categorias dele e o ranking de mais lidas
    dele. Tudo filtrado pela organização.
    """
    return {
        'blog': blog,
        'categorias': Categoria.objects.filter(organizacao=blog),
        'mais_lidas': (
            Post.objects.filter(organizacao=blog, status=Post.PUBLICADO)
            .order_by('-visualizacoes', '-data_publicacao')[:5]
        ),
    }


# ---------------------------------------------------------------------
# 1. Público
# ---------------------------------------------------------------------

def home(request):
    """Página de entrada: lista os blogs hospedados na plataforma."""
    return render(request, 'noticias/lista_blogs.html', {
        'blogs': Organizacao.objects.all(),
    })


def lista_posts(request, blog_slug):
    """
    Página inicial de um blog: só mostra matérias já publicadas DELE.

    Feature 1 do P1 — Busca e Filtro na Listagem. Os parâmetros chegam
    pela URL (ex.: /blog/marica/?q=praia&categoria=3&tag=2) e podem ser
    usados juntos ou separados:
      - q         -> busca por texto no título ou no resumo da matéria
      - categoria -> restringe a uma categoria
      - tag       -> restringe a matérias marcadas com uma tag

    Desafio extra: todas as condições são montadas com Q() e aplicadas
    numa única consulta ao banco — que agora parte do filtro do blog.
    """
    blog = get_object_or_404(Organizacao, slug=blog_slug)

    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    tag_id = request.GET.get('tag', '')

    filtros = Q(organizacao=blog, status=Post.PUBLICADO)
    if q:
        # icontains = "contém", sem diferenciar maiúsculas de minúsculas.
        # O | (OU) faz o termo ser procurado no título OU no resumo.
        filtros &= Q(titulo__icontains=q) | Q(resumo__icontains=q)
    if categoria_id.isdigit():
        filtros &= Q(categoria_id=categoria_id)
    if tag_id.isdigit():
        filtros &= Q(tags__id=tag_id)

    posts = (
        Post.objects.filter(filtros)
        .select_related('categoria', 'autor')
        .distinct()  # evita repetir a matéria ao filtrar por tag (ManyToMany)
    )
    return render(request, 'noticias/lista_posts.html', {
        'posts': posts,
        'tags': Tag.objects.filter(organizacao=blog),
        'busca_ativa': bool(q or categoria_id or tag_id),
        'categoria_selecionada': categoria_id,
        'tag_selecionada': tag_id,
        **_menu_contexto(blog),
    })


def posts_por_categoria(request, blog_slug, categoria_id):
    blog = get_object_or_404(Organizacao, slug=blog_slug)
    categoria = get_object_or_404(Categoria, pk=categoria_id, organizacao=blog)
    posts = Post.objects.filter(
        organizacao=blog, status=Post.PUBLICADO, categoria=categoria,
    )
    return render(request, 'noticias/categoria.html', {
        'categoria': categoria,
        'posts': posts,
        **_menu_contexto(blog),
    })


def detalhe_post(request, blog_slug, pk):
    """Mostra a matéria completa e trata o envio de novos comentários (GET mostra, POST salva)."""
    blog = get_object_or_404(Organizacao, slug=blog_slug)
    # Só matéria PUBLICADA e DESTE blog. (Na P1 qualquer rascunho podia
    # ser lido no site público digitando o id na URL — ver MELHORIAS_P1.md.)
    post = get_object_or_404(Post, pk=pk, organizacao=blog, status=Post.PUBLICADO)
    comentarios = post.comentarios.all()

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.post = post
            comentario.organizacao = blog
            comentario.save()
            messages.success(request, 'Comentário publicado com sucesso!')
            return redirect('detalhe_post', blog_slug=blog.slug, pk=post.pk)
    else:
        form = ComentarioForm()
        # Conta a visualização (só ao exibir a página — não conta de novo
        # quando o comentário é enviado).
        Post.objects.filter(pk=post.pk).update(visualizacoes=F('visualizacoes') + 1)
        post.visualizacoes += 1

    return render(request, 'noticias/detalhe_post.html', {
        'post': post,
        'comentarios': comentarios,
        'form': form,
        **_menu_contexto(blog),
    })


# ---------------------------------------------------------------------
# 2. CRUD de matérias (exige login; o blog vem do usuário logado)
# ---------------------------------------------------------------------

@organizacao_required
def novo_post(request):
    org = request.org
    form = PostForm(request.POST or None, request.FILES or None, org=org)
    if request.method == 'POST' and form.is_valid():
        # commit=False: o form não tem o campo organizacao; ele é
        # preenchido aqui, com o blog do usuário logado, antes de salvar.
        post = form.save(commit=False)
        post.organizacao = org
        post.save()          # status entra como RASCUNHO por padrão do model
        form.save_m2m()      # grava as tags (ManyToMany)
        messages.success(request, 'Matéria criada como rascunho.')
        return redirect('painel_editorial')

    return render(request, 'noticias/post_form.html', {
        'form': form,
        'titulo_pagina': 'Nova Matéria',
        **_menu_contexto(org),
    })


@organizacao_required
def editar_post(request, pk):
    org = request.org
    post = get_object_or_404(Post, pk=pk, organizacao=org)

    form = PostForm(request.POST or None, request.FILES or None, instance=post, org=org)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Matéria atualizada com sucesso!')
        return redirect('painel_editorial')

    return render(request, 'noticias/post_form.html', {
        'form': form,
        'titulo_pagina': f'Editar: {post.titulo}',
        'post': post,
        **_menu_contexto(org),
    })


@organizacao_required
def excluir_post(request, pk):
    org = request.org
    post = get_object_or_404(Post, pk=pk, organizacao=org)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Matéria excluída.')
        return redirect('painel_editorial')

    return render(request, 'noticias/confirmar_exclusao.html', {
        'post': post,
        **_menu_contexto(org),
    })


# ---------------------------------------------------------------------
# 3. Fluxo editorial (o coração do projeto: 3 estados de publicação)
# ---------------------------------------------------------------------

@organizacao_required
def painel_editorial(request):
    """Painel interno: mostra TODAS as matérias do blog do usuário, em qualquer status."""
    org = request.org
    posts = Post.objects.filter(organizacao=org).select_related('categoria', 'autor')
    return render(request, 'noticias/painel_editorial.html', {
        'posts': posts,
        **_menu_contexto(org),
    })


def _mudar_status(request, pk, de, para, mensagem, nivel=messages.info):
    """
    Faz uma transição do fluxo editorial, só se a matéria estiver no
    estado esperado (`de`). Evita, por exemplo, publicar direto um
    rascunho chamando a URL de publicação.
    """
    post = get_object_or_404(Post, pk=pk, organizacao=request.org)
    if post.status not in de:
        messages.error(
            request,
            f'"{post.titulo}" está como {post.get_status_display()} e não pode ir para esse estado.',
        )
        return None
    post.status = para
    # Só matéria publicada tem data de publicação.
    post.data_publicacao = timezone.now() if para == Post.PUBLICADO else None
    post.save()
    nivel(request, mensagem.format(titulo=post.titulo))
    return post


@require_POST
@organizacao_required
def enviar_para_revisao(request, pk):
    """RASCUNHO -> REVISAO"""
    _mudar_status(request, pk, [Post.RASCUNHO], Post.REVISAO,
                  '"{titulo}" enviado para revisão.')
    return redirect('painel_editorial')


@require_POST
@organizacao_required
def devolver_rascunho(request, pk):
    """REVISAO -> RASCUNHO (o revisor pede ajustes)"""
    _mudar_status(request, pk, [Post.REVISAO], Post.RASCUNHO,
                  '"{titulo}" devolvido para rascunho.', messages.warning)
    return redirect('painel_editorial')


@require_POST
@organizacao_required
def publicar_post(request, pk):
    """REVISAO -> PUBLICADO (aprovação editorial)"""
    post = get_object_or_404(Post, pk=pk, organizacao=request.org)
    # Mesma regra do PostForm.clean_conteudo, repetida aqui porque uma
    # matéria criada pelo /admin não passa pelo nosso formulário.
    if len(post.conteudo.strip()) < Post.CONTEUDO_MINIMO:
        messages.error(
            request,
            f'"{post.titulo}" não pode ser publicado: o conteúdo precisa ter '
            f'pelo menos {Post.CONTEUDO_MINIMO} caracteres. Edite a matéria e tente de novo.',
        )
        return redirect('painel_editorial')
    _mudar_status(request, pk, [Post.REVISAO], Post.PUBLICADO,
                  '"{titulo}" publicado no portal!', messages.success)
    return redirect('painel_editorial')


@require_POST
@organizacao_required
def despublicar_post(request, pk):
    """PUBLICADO -> RASCUNHO (remover a matéria do ar)"""
    _mudar_status(request, pk, [Post.PUBLICADO], Post.RASCUNHO,
                  '"{titulo}" despublicado.', messages.warning)
    return redirect('painel_editorial')
