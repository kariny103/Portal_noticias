"""
Métricas do Dashboard (P2, Aula 17).

"Comece pela pergunta, não pela tela": cada função responde a uma
pergunta que o dono de um blog faria toda semana.

  1. KPI          -> Quanto o blog produziu no período? (total, por status,
                     visualizações e comentários)            aggregate()
  2. Ranking      -> Quais matérias foram mais lidas?        annotate() + order_by
  3. Série        -> Quantas matérias foram escritas por mês? TruncMonth
  4. Distribuição -> Em quais categorias o blog mais escreve? values() + annotate()

Todas recebem a MESMA `base`: o queryset de Post já filtrado pela
organização (blog) e pelo período. Assim o isolamento entre blogs e o
filtro de datas valem para todos os cartões e gráficos automaticamente.
As views (página, CSV e API) só chamam estas funções — nenhuma consulta
fica duplicada.
"""
from datetime import datetime, time, timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .forms import PeriodoForm
from .models import Comentario, Post


def base_do_blog(org):
    """Primeira linha de toda métrica: só os posts do blog do usuário."""
    return Post.objects.filter(organizacao=org)


def filtrar_periodo(params, qs):
    """
    Aplica o filtro de período (?inicio=AAAA-MM-DD&fim=AAAA-MM-DD) validado
    pelo PeriodoForm. Nunca confiamos na data digitada na URL: "abc" vira
    erro de formulário, e não erro 500.

    Devolve (queryset_filtrado, form). Se o form for inválido, o queryset
    volta sem filtro de período e o template mostra os erros.

    O período usa a data de criação da matéria. Em vez de
    `data_criacao__date__gte` (que aplica uma função na coluna e impede o
    uso do índice), montamos o intervalo [início 00:00, fim+1 00:00) no
    fuso do projeto.
    """
    form = PeriodoForm(params)
    if form.is_valid():
        inicio = form.cleaned_data['inicio']
        fim = form.cleaned_data['fim']
        if inicio:
            qs = qs.filter(data_criacao__gte=_inicio_do_dia(inicio))
        if fim:
            qs = qs.filter(data_criacao__lt=_inicio_do_dia(fim + timedelta(days=1)))
    return qs, form


def _inicio_do_dia(data):
    return timezone.make_aware(datetime.combine(data, time.min))


# ---------------------------------------------------------------------
# 1. KPI — aggregate(): UM dicionário com vários totais em UMA consulta
# ---------------------------------------------------------------------

def kpis(base):
    totais = base.aggregate(
        total=Count('id'),
        publicadas=Count('id', filter=Q(status=Post.PUBLICADO)),
        em_revisao=Count('id', filter=Q(status=Post.REVISAO)),
        rascunhos=Count('id', filter=Q(status=Post.RASCUNHO)),
        visualizacoes=Sum('visualizacoes'),
    )
    # Sum() de nenhuma linha devolve None: no cartão queremos 0.
    totais['visualizacoes'] = totais['visualizacoes'] or 0
    # Comentários ficam numa consulta à parte de propósito: somar
    # visualizacoes junto com um JOIN em comentarios repetiria cada post
    # uma vez por comentário e inflaria a soma.
    totais['comentarios'] = Comentario.objects.filter(post__in=base).count()
    return totais


# ---------------------------------------------------------------------
# 2. Ranking — top 5 matérias publicadas mais lidas (com nº de comentários)
# ---------------------------------------------------------------------

def ranking_mais_lidas(base, limite=5):
    return list(
        base.filter(status=Post.PUBLICADO)
        .annotate(n_comentarios=Count('comentarios'))
        .order_by('-visualizacoes', 'titulo')
        .values('pk', 'titulo', 'visualizacoes', 'n_comentarios')[:limite]
    )


# ---------------------------------------------------------------------
# 3. Série no tempo — matérias criadas por mês (e quantas já publicadas)
# ---------------------------------------------------------------------

def serie_por_mes(base):
    linhas = (
        base.annotate(mes=TruncMonth('data_criacao'))
        .values('mes')
        .annotate(
            total=Count('id'),
            publicadas=Count('id', filter=Q(status=Post.PUBLICADO)),
        )
        .order_by('mes')  # sem order_by os meses podem sair embaralhados
    )
    # O JavaScript precisa de um rótulo legível, não de um datetime.
    return [
        {'mes': r['mes'].strftime('%m/%Y'), 'total': r['total'], 'publicadas': r['publicadas']}
        for r in linhas
    ]


# ---------------------------------------------------------------------
# 4. Distribuição — matérias por categoria
# ---------------------------------------------------------------------

def distribuicao_por_categoria(base):
    return list(
        base.values('categoria__nome')
        .annotate(total=Count('id'))
        .order_by('-total', 'categoria__nome')
    )


def calcular_metricas(base):
    """Tudo o que o dashboard mostra, a partir de uma única base filtrada."""
    return {
        'kpis': kpis(base),
        'ranking': ranking_mais_lidas(base),
        'por_mes': serie_por_mes(base),
        'por_categoria': distribuicao_por_categoria(base),
    }
