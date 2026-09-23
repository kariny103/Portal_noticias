"""
Views — a lógica de cada página (Aula 5).

O padrão de sempre: a view busca os dados com o ORM e devolve uma
resposta, normalmente uma página renderizada por um template.

As views deste arquivo estão organizadas em três grupos:
  1. Público  -> o que qualquer visitante do portal vê
  2. CRUD     -> criar / editar / excluir matérias
  3. Editorial -> o fluxo de publicação (rascunho -> revisão -> publicado)
"""
from django.contrib import messages
from django.db.models import F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ComentarioForm, PostForm
from .models import Categoria, Post, Tag


def _menu_contexto():
    """
    Dados que aparecem em quase toda página (menu do topo e rodapé):
    a lista de categorias e o ranking de mais lidas. Reaproveitado nas
    views abaixo para não repetir a mesma consulta em cada uma.
    """
    return {
        'categorias': Categoria.objects.all(),
        'mais_lidas': (
            Post.objects.filter(status=Post.PUBLICADO)
            .order_by('-visualizacoes', '-data_publicacao')[:5]
        ),
    }


# ---------------------------------------------------------------------
# 1. Público
# ---------------------------------------------------------------------

def lista_posts(request):
    """
    Página inicial: só mostra matérias já publicadas.

    Feature 1 do P1 — Busca e Filtro na Listagem. Os parâmetros chegam
    pela URL (ex.: /?q=praia&categoria=3&tag=2) e podem ser usados
    juntos ou separados:
      - q         -> busca por texto no título ou no resumo da matéria
      - categoria -> restringe a uma categoria
      - tag       -> restringe a matérias marcadas com uma tag

    Desafio extra: todas as condições são montadas com Q() e aplicadas
    numa única consulta ao banco.
    """
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    tag_id = request.GET.get('tag', '')

    filtros = Q(status=Post.PUBLICADO)
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
        'tags': Tag.objects.all(),
        'busca_ativa': bool(q or categoria_id or tag_id),
        'categoria_selecionada': categoria_id,
        'tag_selecionada': tag_id,
        **_menu_contexto(),
    })


def posts_por_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    posts = Post.objects.filter(status=Post.PUBLICADO, categoria=categoria)
    return render(request, 'noticias/categoria.html', {
        'categoria': categoria,
        'posts': posts,
        **_menu_contexto(),
    })


def detalhe_post(request, pk):
    """Mostra a matéria completa e trata o envio de novos comentários (GET mostra, POST salva)."""
    post = get_object_or_404(Post, pk=pk)
    comentarios = post.comentarios.all()

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.post = post
            comentario.save()
            messages.success(request, 'Comentário publicado com sucesso!')
            return redirect('detalhe_post', pk=post.pk)
    else:
        form = ComentarioForm()
        if post.status == Post.PUBLICADO:
            # Conta a visualização (só de matéria publicada, só ao exibir
            # a página — não conta de novo quando o comentário é enviado).
            Post.objects.filter(pk=post.pk).update(visualizacoes=F('visualizacoes') + 1)
            post.visualizacoes += 1

    return render(request, 'noticias/detalhe_post.html', {
        'post': post,
        'comentarios': comentarios,
        'form': form,
        **_menu_contexto(),
    })


# ---------------------------------------------------------------------
# 2. CRUD de matérias
# ---------------------------------------------------------------------

def novo_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # status entra como RASCUNHO por padrão do model
            messages.success(request, 'Matéria criada como rascunho.')
            return redirect('painel_editorial')
    else:
        form = PostForm()

    return render(request, 'noticias/post_form.html', {
        'form': form,
        'titulo_pagina': 'Nova Matéria',
        **_menu_contexto(),
    })


def editar_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Matéria atualizada com sucesso!')
            return redirect('painel_editorial')
    else:
        form = PostForm(instance=post)

    return render(request, 'noticias/post_form.html', {
        'form': form,
        'titulo_pagina': f'Editar: {post.titulo}',
        'post': post,
        **_menu_contexto(),
    })


def excluir_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Matéria excluída.')
        return redirect('painel_editorial')

    return render(request, 'noticias/confirmar_exclusao.html', {
        'post': post,
        **_menu_contexto(),
    })


# ---------------------------------------------------------------------
# 3. Fluxo editorial (o coração do projeto: 3 estados de publicação)
# ---------------------------------------------------------------------

def painel_editorial(request):
    """Painel interno: mostra TODAS as matérias, independente do status."""
    posts = Post.objects.all().select_related('categoria', 'autor')
    return render(request, 'noticias/painel_editorial.html', {
        'posts': posts,
        **_menu_contexto(),
    })


def enviar_para_revisao(request, pk):
    """RASCUNHO -> REVISAO"""
    post = get_object_or_404(Post, pk=pk)
    post.status = Post.REVISAO
    post.save()
    messages.info(request, f'"{post.titulo}" enviado para revisão.')
    return redirect('painel_editorial')


def devolver_rascunho(request, pk):
    """REVISAO -> RASCUNHO (o revisor pede ajustes)"""
    post = get_object_or_404(Post, pk=pk)
    post.status = Post.RASCUNHO
    post.save()
    messages.warning(request, f'"{post.titulo}" devolvido para rascunho.')
    return redirect('painel_editorial')


def publicar_post(request, pk):
    """REVISAO -> PUBLICADO (aprovação editorial)"""
    post = get_object_or_404(Post, pk=pk)
    post.status = Post.PUBLICADO
    post.data_publicacao = timezone.now()
    post.save()
    messages.success(request, f'"{post.titulo}" publicado no portal!')
    return redirect('painel_editorial')


def despublicar_post(request, pk):
    """PUBLICADO -> RASCUNHO (remover a matéria do ar)"""
    post = get_object_or_404(Post, pk=pk)
    post.status = Post.RASCUNHO
    post.data_publicacao = None
    post.save()
    messages.warning(request, f'"{post.titulo}" despublicado.')
    return redirect('painel_editorial')
