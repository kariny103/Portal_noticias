"""
Comando de gerenciamento (extensão do manage.py) para popular o banco
com dados de exemplo — útil para a apresentação, sem precisar cadastrar
tudo manualmente no Admin.

P2 (Aula 14): cria DOIS blogs (organizações), cada um com as suas
categorias, tags, autores e matérias, e um usuário editor para cada
blog (com Perfil). Serve para rodar o roteiro de isolamento: o editor
de um blog não pode ver nada do outro.

Uso:
    python manage.py seed_dados

Pode ser rodado mais de uma vez: usa get_or_create, não duplica nada.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Organizacao, Perfil
from noticias.models import Autor, Categoria, Comentario, Post, Tag

SENHA_DEMO = 'portal2026'


class Command(BaseCommand):
    help = 'Popula o banco com 2 blogs, usuários editores e matérias de exemplo.'

    def handle(self, *args, **options):
        marica = self._blog_marica()
        niteroi = self._blog_niteroi()

        self._usuario('editor_marica', marica)
        self._usuario('editor_niteroi', niteroi)

        # O superusuário "admin" da P1 continua editando o blog de Maricá
        # (sem Perfil ele não conseguiria abrir o Painel Editorial).
        admin = User.objects.filter(username='admin').first()
        if admin:
            Perfil.objects.get_or_create(usuario=admin, defaults={'organizacao': marica})

        self.stdout.write(self.style.SUCCESS(
            'Dados de exemplo prontos: 2 blogs (Maricá e Niterói), cada um com '
            'categorias, tags, autores e matérias.\n'
            f'Usuários: editor_marica / editor_niteroi (senha: {SENHA_DEMO}).'
        ))

    # ------------------------------------------------------------------

    def _usuario(self, username, org):
        user, criado = User.objects.get_or_create(username=username)
        if criado:
            user.set_password(SENHA_DEMO)
            user.save()
        Perfil.objects.update_or_create(usuario=user, defaults={'organizacao': org})

    def _base(self, org, nomes_categorias, nomes_tags):
        categorias = {
            nome: Categoria.objects.get_or_create(organizacao=org, nome=nome)[0]
            for nome in nomes_categorias
        }
        tags = {
            nome: Tag.objects.get_or_create(organizacao=org, nome=nome)[0]
            for nome in nomes_tags
        }
        return categorias, tags

    def _blog_marica(self):
        org, _ = Organizacao.objects.get_or_create(
            slug='marica', defaults={'nome': 'Portal Notícias Maricá'},
        )
        categorias, tags = self._base(
            org,
            ['Política', 'Tecnologia', 'Esportes', 'Eventos', 'Educação', 'Concurso', 'Saúde', 'Tempo'],
            ['Brasil', 'Internacional', 'Economia', 'Inovação'],
        )

        autor, _ = Autor.objects.get_or_create(
            organizacao=org, nome='Ana Redatora',
            defaults={'email': 'ana.redatora@portalmarica.com', 'bio': 'Repórter de plantão do Portal Notícias Maricá.'},
        )
        autor2, _ = Autor.objects.get_or_create(
            organizacao=org, nome='Carlos Editor',
            defaults={'email': 'carlos.editor@portalmarica.com', 'bio': 'Editor-chefe de Tecnologia e Economia.'},
        )

        # Uma matéria já publicada
        publicado, criado = Post.objects.get_or_create(
            organizacao=org,
            titulo='Portal Notícias Maricá entra no ar com nova plataforma',
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
                organizacao=org, post=publicado, nome_autor='Leitor Curioso',
                email='leitor@example.com',
                texto='Ótima novidade! O site ficou muito mais rápido.',
            )

        # Uma matéria em revisão (aguardando aprovação editorial)
        revisao, criado = Post.objects.get_or_create(
            organizacao=org,
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
            organizacao=org,
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

        return org

    def _blog_niteroi(self):
        org, _ = Organizacao.objects.get_or_create(
            slug='niteroi', defaults={'nome': 'Portal Notícias Niterói'},
        )
        # "Esportes" e "Brasil" também existem no blog de Maricá: a
        # unicidade agora é por blog, então isso é permitido.
        categorias, tags = self._base(
            org,
            ['Cidade', 'Cultura', 'Esportes', 'Mobilidade'],
            ['Brasil', 'Barcas', 'Praias'],
        )

        autora, _ = Autor.objects.get_or_create(
            organizacao=org, nome='Beatriz Repórter',
            defaults={'email': 'beatriz@portalniteroi.com', 'bio': 'Repórter de cidade do Portal Notícias Niterói.'},
        )

        publicado, criado = Post.objects.get_or_create(
            organizacao=org,
            titulo='Niterói ganha novo horário de barcas aos fins de semana',
            defaults={
                'resumo': 'Operadora amplia a grade de viagens entre Niterói e o Rio aos sábados e domingos.',
                'conteudo': (
                    'A partir do próximo mês, as barcas entre a Praça Araribóia e a Praça XV terão '
                    'viagens extras aos fins de semana. A mudança atende a um pedido antigo de quem '
                    'trabalha e passeia entre as duas cidades.'
                ),
                'categoria': categorias['Mobilidade'],
                'autor': autora,
                'status': Post.PUBLICADO,
                'data_publicacao': timezone.now(),
            },
        )
        if criado:
            publicado.tags.add(tags['Barcas'])

        rascunho, criado = Post.objects.get_or_create(
            organizacao=org,
            titulo='Rascunho: festival de cultura no Caminho Niemeyer',
            defaults={
                'resumo': 'Programação ainda em fechamento com a secretaria de cultura.',
                'conteudo': (
                    'A prefeitura prepara um festival de música e artes no Caminho Niemeyer. A '
                    'programação completa deve ser divulgada nas próximas semanas.'
                ),
                'categoria': categorias['Cultura'],
                'autor': autora,
                'status': Post.RASCUNHO,
            },
        )
        if criado:
            rascunho.tags.add(tags['Praias'])

        return org
