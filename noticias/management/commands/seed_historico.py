"""
Gera um histórico de matérias (dados fictícios) espalhadas pelos últimos
meses, para o Dashboard (Aula 17) ter o que mostrar: barras por mês,
ranking de mais lidas e distribuição por categoria.

Uso (depois do seed_dados, que cria os blogs, categorias e autores):
    python manage.py seed_historico

Os números são sorteados com semente fixa: rodar de novo não duplica
nada (usa get_or_create pelo título) e os valores são sempre os mesmos.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Organizacao
from noticias.models import Autor, Categoria, Comentario, Post

MESES = 7  # quantos meses para trás

PAUTAS = {
    'marica': [
        ('Política', 'Câmara de Maricá aprova orçamento para o próximo ano'),
        ('Política', 'Prefeitura anuncia novas obras de saneamento em Itaipuaçu'),
        ('Política', 'Audiência pública discute plano diretor da cidade'),
        ('Tecnologia', 'Maricá amplia rede de Wi-Fi gratuito nas praças'),
        ('Tecnologia', 'Startup maricaense desenvolve app de transporte local'),
        ('Tecnologia', 'Escolas da rede municipal recebem laboratórios de robótica'),
        ('Esportes', 'Maricá vence clássico regional e sobe na tabela'),
        ('Esportes', 'Corrida de rua reúne mil atletas na orla de Ponta Negra'),
        ('Esportes', 'Projeto social leva surfe para jovens de Jaconé'),
        ('Esportes', 'Seleção de vôlei de praia treina na Barra de Maricá'),
        ('Eventos', 'Festival de inverno movimenta o centro histórico'),
        ('Eventos', 'Feira de artesanato volta à praça Orlando de Barros Pimentel'),
        ('Eventos', 'Show gratuito encerra a semana do aniversário da cidade'),
        ('Educação', 'Inscrições abertas para cursos técnicos gratuitos'),
        ('Educação', 'Biblioteca municipal ganha novo acervo infantil'),
        ('Concurso', 'Saiu o edital do concurso da prefeitura de Maricá'),
        ('Concurso', 'Resultado preliminar do concurso da saúde é divulgado'),
        ('Saúde', 'Campanha de vacinação chega aos distritos'),
        ('Saúde', 'Nova unidade de pronto atendimento abre em Inoã'),
        ('Saúde', 'Mutirão de exames atende mais de 500 pessoas'),
        ('Tempo', 'Frente fria traz chuva forte ao litoral de Maricá'),
        ('Tempo', 'Fim de semana de sol e mar calmo nas lagoas'),
        ('Tecnologia', 'Moeda social Mumbuca ganha nova versão do aplicativo'),
        ('Eventos', 'Cinema ao ar livre lota a orla de Araçatiba'),
    ],
    'niteroi': [
        ('Cidade', 'Niterói inaugura nova ciclovia na Região Oceânica'),
        ('Cidade', 'Obras do túnel Charitas-Cafubá entram na fase final'),
        ('Cultura', 'MAC recebe exposição internacional de arte contemporânea'),
        ('Cultura', 'Teatro Municipal abre temporada com espetáculo infantil'),
        ('Esportes', 'Regata reúne velejadores na baía de Guanabara'),
        ('Esportes', 'Niterói sedia etapa do circuito de beach tennis'),
        ('Mobilidade', 'Barcas terão bilhete integrado com ônibus'),
        ('Mobilidade', 'Nova linha de ônibus liga Icaraí ao Centro'),
        ('Cidade', 'Parque da Cidade ganha mirante reformado'),
        ('Cultura', 'Festival de jazz movimenta São Francisco'),
    ],
}


class Command(BaseCommand):
    help = 'Gera matérias fictícias nos últimos meses para o Dashboard (Aula 17).'

    def handle(self, *args, **options):
        rng = random.Random(2026)
        agora = timezone.now()
        criadas = 0

        for slug, pautas in PAUTAS.items():
            try:
                org = Organizacao.objects.get(slug=slug)
            except Organizacao.DoesNotExist:
                raise CommandError(f'Blog "{slug}" não existe. Rode antes: python manage.py seed_dados')
            autores = list(Autor.objects.filter(organizacao=org))
            if not autores:
                raise CommandError(f'O blog "{slug}" não tem autores. Rode antes: python manage.py seed_dados')

            for categoria_nome, titulo in pautas:
                categoria, _ = Categoria.objects.get_or_create(organizacao=org, nome=categoria_nome)
                criada_em = agora - timedelta(
                    days=rng.randint(0, MESES * 30), hours=rng.randint(0, 23),
                )
                # Matérias antigas quase sempre já foram publicadas;
                # as recentes podem estar em revisão ou em rascunho.
                recente = (agora - criada_em).days < 30
                status = rng.choices(
                    [Post.PUBLICADO, Post.REVISAO, Post.RASCUNHO],
                    weights=[5, 2, 2] if recente else [9, 1, 1],
                )[0]
                publicada = status == Post.PUBLICADO
                visualizacoes = rng.randint(15, 400) if publicada else 0

                post, criado = Post.objects.get_or_create(
                    organizacao=org, titulo=titulo,
                    defaults={
                        'resumo': titulo + '.',
                        'conteudo': (
                            f'{titulo}. Matéria fictícia gerada para demonstrar o dashboard do '
                            'portal, com métricas por mês, ranking e distribuição por categoria.'
                        ),
                        'categoria': categoria,
                        'autor': rng.choice(autores),
                        'status': status,
                        'visualizacoes': visualizacoes,
                        'data_publicacao': criada_em + timedelta(hours=6) if publicada else None,
                    },
                )
                if not criado:
                    continue
                # data_criacao é auto_now_add: o update() grava a data "do passado".
                Post.objects.filter(pk=post.pk).update(data_criacao=criada_em)
                if publicada:
                    for i in range(rng.randint(0, 4)):
                        Comentario.objects.create(
                            organizacao=org, post=post, nome_autor=f'Leitor {i + 1}',
                            email=f'leitor{i + 1}@example.com', texto='Comentário de exemplo.',
                        )
                criadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'{criadas} matérias de histórico criadas. Abra /painel/dashboard/ para ver as métricas.'
        ))
