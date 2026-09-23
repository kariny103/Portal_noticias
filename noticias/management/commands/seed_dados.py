"""
Comando de gerenciamento (extensão do manage.py) para popular o banco
com dados de exemplo — útil para a apresentação, sem precisar cadastrar
tudo manualmente no Admin.

Uso:
    python manage.py seed_dados
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from noticias.models import Autor, Categoria, Comentario, Post, Tag


class Command(BaseCommand):
    help = 'Popula o banco com categorias, tags, autores e posts de exemplo.'

    def handle(self, *args, **options):
        categorias = {
            nome: Categoria.objects.get_or_create(nome=nome)[0]
            for nome in [
                'Política', 'Tecnologia', 'Esportes', 'Eventos',
                'Educação', 'Concurso', 'Saúde', 'Tempo',
            ]
        }

        tags = {
            nome: Tag.objects.get_or_create(nome=nome)[0]
            for nome in ['Brasil', 'Internacional', 'Economia', 'Inovação']
        }

        autor, _ = Autor.objects.get_or_create(
            nome='Ana Redatora',
            defaults={'email': 'ana.redatora@portalmarica.com', 'bio': 'Repórter de plantão do Portal de Últimas Notícias de Maricá.'},
        )
        autor2, _ = Autor.objects.get_or_create(
            nome='Carlos Editor',
            defaults={'email': 'carlos.editor@portalmarica.com', 'bio': 'Editor-chefe de Tecnologia e Economia.'},
        )

        # Uma matéria já publicada
        publicado, criado = Post.objects.get_or_create(
            titulo='Portal de Últimas Notícias de Maricá entra no ar com nova plataforma',
            defaults={
                'resumo': 'Site foi reconstruído do zero com Django e traz um novo fluxo de aprovação editorial.',
                'conteudo': (
                    'A equipe de tecnologia concluiu hoje a migração do portal para uma nova plataforma '
                    'construída com Python e Django. Entre as novidades está o fluxo de publicação com '
                    'aprovação editorial, que garante que toda matéria sobre Maricá e região passe por '
                    'revisão antes de ir ao ar.'
                ),
                'categoria': categorias['Tecnologia'],
                'autor': autor2,
                'status': Post.PUBLICADO,
                'data_publicacao': timezone.now(),
                'imagem_capa': 'capas/marica-capa.jpg',
            },
        )
        if criado:
            publicado.tags.add(tags['Inovação'], tags['Brasil'])
            Comentario.objects.create(
                post=publicado, nome_autor='Leitor Curioso',
                email='leitor@example.com',
                texto='Ótima novidade! O site ficou muito mais rápido.',
            )

        # Uma matéria em revisão (aguardando aprovação editorial)
        revisao, criado = Post.objects.get_or_create(
            titulo='Time de Maricá se prepara para a próxima rodada do campeonato',
            defaults={
                'resumo': 'Comissão técnica define escalação para o próximo desafio em casa.',
                'conteudo': (
                    'Com foco na próxima partida, o técnico realizou os últimos ajustes táticos durante '
                    'a semana no centro de treinamento da cidade. A expectativa da torcida maricaense é '
                    'grande para o próximo confronto.'
                ),
                'categoria': categorias['Esportes'],
                'autor': autor,
                'status': Post.REVISAO,
            },
        )
        if criado:
            revisao.tags.add(tags['Brasil'])

        # Uma matéria em rascunho
        rascunho, criado = Post.objects.get_or_create(
            titulo='Rascunho: prefeitura de Maricá anuncia novo investimento',
            defaults={
                'resumo': 'Matéria em produção — aguardando confirmação oficial da fonte.',
                'conteudo': (
                    'Texto inicial da pauta sobre o novo investimento anunciado para a cidade, ainda em '
                    'levantamento de dados com as fontes oficiais da prefeitura.'
                ),
                'categoria': categorias['Política'],
                'autor': autor,
                'status': Post.RASCUNHO,
            },
        )
        if criado:
            rascunho.tags.add(tags['Economia'])

        self.stdout.write(self.style.SUCCESS(
            f'Dados de exemplo criados: {len(categorias)} categorias, {len(tags)} tags, '
            '2 autores e 3 posts (1 publicado, 1 em revisão, 1 rascunho).'
        ))
