"""
Roteiro de isolamento multi-organização (Aula 14, slide 18) em forma
de testes automatizados, para rodar a cada nova tela:

    python manage.py test

Cenário: dois blogs (A = Maricá, B = Niterói), um editor em cada um.
"""
from datetime import datetime

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from core.models import Organizacao, Perfil
from . import dashboard as metricas
from .models import Autor, Categoria, Comentario, Post, Tag

CONTEUDO_OK = 'Texto da matéria com tamanho suficiente para passar na validação da P1.'


class IsolamentoTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organizacao.objects.create(nome='Blog A', slug='blog-a')
        cls.org_b = Organizacao.objects.create(nome='Blog B', slug='blog-b')

        cls.user_a = User.objects.create_user('editor_a', password='senha-teste-123')
        cls.user_b = User.objects.create_user('editor_b', password='senha-teste-123')
        Perfil.objects.create(usuario=cls.user_a, organizacao=cls.org_a)
        Perfil.objects.create(usuario=cls.user_b, organizacao=cls.org_b)

        cls.cat_a = Categoria.objects.create(organizacao=cls.org_a, nome='Esportes')
        cls.cat_b = Categoria.objects.create(organizacao=cls.org_b, nome='Cultura')
        cls.autor_a = Autor.objects.create(organizacao=cls.org_a, nome='Autor A', email='a@a.com')
        cls.autor_b = Autor.objects.create(organizacao=cls.org_b, nome='Autor B', email='b@b.com')
        cls.tag_a = Tag.objects.create(organizacao=cls.org_a, nome='Tag A')
        cls.tag_b = Tag.objects.create(organizacao=cls.org_b, nome='Tag B')

        cls.post_a = Post.objects.create(
            organizacao=cls.org_a, titulo='Matéria do blog A', resumo='r', conteudo=CONTEUDO_OK,
            categoria=cls.cat_a, autor=cls.autor_a, status=Post.REVISAO,
        )
        cls.post_b = Post.objects.create(
            organizacao=cls.org_b, titulo='Matéria do blog B', resumo='r', conteudo=CONTEUDO_OK,
            categoria=cls.cat_b, autor=cls.autor_b, status=Post.PUBLICADO,
            data_publicacao=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.user_a)

    # --- Cenário 1: usuário A abre a lista -> só vê o blog A -------------

    def test_painel_mostra_so_materias_do_proprio_blog(self):
        resp = self.client.get(reverse('painel_editorial'))
        self.assertContains(resp, 'Matéria do blog A')
        self.assertNotContains(resp, 'Matéria do blog B')

    def test_site_publico_de_um_blog_nao_mostra_materias_do_outro(self):
        resp = self.client.get(reverse('lista_posts', args=['blog-a']))
        self.assertNotContains(resp, 'Matéria do blog B')

    def test_api_lista_so_registros_do_proprio_blog(self):
        titulos = [p['titulo'] for p in self.client.get('/api/posts/').json()]
        self.assertEqual(titulos, ['Matéria do blog A'])
        nomes = [c['nome'] for c in self.client.get('/api/categorias/').json()]
        self.assertEqual(nomes, ['Esportes'])

    # --- Cenário 2: usuário A abre o ID de um registro de B -> 404 -------

    def test_editar_materia_de_outro_blog_da_404(self):
        resp = self.client.get(reverse('editar_post', args=[self.post_b.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_acoes_do_fluxo_em_materia_de_outro_blog_dao_404(self):
        for nome in ['despublicar_post', 'excluir_post']:
            resp = self.client.post(reverse(nome, args=[self.post_b.pk]))
            self.assertEqual(resp.status_code, 404, nome)
        self.post_b.refresh_from_db()
        self.assertEqual(self.post_b.status, Post.PUBLICADO)

    def test_api_detalhe_de_outro_blog_da_404(self):
        self.assertEqual(self.client.get(f'/api/posts/{self.post_b.pk}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/posts/{self.post_b.pk}/').status_code, 404)
        self.assertTrue(Post.objects.filter(pk=self.post_b.pk).exists())

    def test_url_publica_de_um_blog_nao_abre_materia_de_outro(self):
        resp = self.client.get(reverse('detalhe_post', args=['blog-a', self.post_b.pk]))
        self.assertEqual(resp.status_code, 404)

    # --- Cenário 3: usuário A cria um registro -> gravado no blog A ------

    def test_nova_materia_pelo_formulario_vai_para_o_blog_do_usuario(self):
        self.client.post(reverse('novo_post'), {
            'titulo': 'Nova do A', 'resumo': 'r', 'conteudo': CONTEUDO_OK,
            'categoria': self.cat_a.pk, 'autor': self.autor_a.pk, 'tags': [self.tag_a.pk],
        })
        post = Post.objects.get(titulo='Nova do A')
        self.assertEqual(post.organizacao, self.org_a)
        self.assertEqual(post.status, Post.RASCUNHO)
        self.assertEqual(list(post.tags.all()), [self.tag_a])

    def test_api_ignora_organizacao_enviada_no_json(self):
        resp = self.client.post('/api/posts/', {
            'titulo': 'Via API', 'resumo': 'r', 'conteudo': CONTEUDO_OK,
            'categoria': self.cat_a.pk, 'autor': self.autor_a.pk,
            'organizacao': self.org_b.pk,  # tentativa de "escolher" o blog
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Post.objects.get(titulo='Via API').organizacao, self.org_a)

    # --- Cenário 4: selects do formulário só mostram opções do blog A ----

    def test_selects_do_formulario_so_tem_opcoes_do_proprio_blog(self):
        form = self.client.get(reverse('novo_post')).context['form']
        self.assertEqual(list(form.fields['categoria'].queryset), [self.cat_a])
        self.assertEqual(list(form.fields['autor'].queryset), [self.autor_a])
        self.assertEqual(list(form.fields['tags'].queryset), [self.tag_a])

    def test_formulario_recusa_categoria_de_outro_blog(self):
        self.client.post(reverse('novo_post'), {
            'titulo': 'Trapaça', 'resumo': 'r', 'conteudo': CONTEUDO_OK,
            'categoria': self.cat_b.pk, 'autor': self.autor_a.pk,
        })
        self.assertFalse(Post.objects.filter(titulo='Trapaça').exists())

    def test_api_recusa_categoria_e_tag_de_outro_blog(self):
        resp = self.client.post('/api/posts/', {
            'titulo': 'Trapaça', 'resumo': 'r', 'conteudo': CONTEUDO_OK,
            'categoria': self.cat_b.pk, 'autor': self.autor_a.pk, 'tags': [self.tag_b.pk],
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('categoria', resp.json())
        self.assertIn('tags', resp.json())

    # --- Cenário 5: unicidade é por blog ---------------------------------

    def test_mesmo_nome_de_categoria_em_blogs_diferentes_e_permitido(self):
        resp = self.client.post('/api/categorias/', {'nome': 'Cultura'}, content_type='application/json')
        self.assertEqual(resp.status_code, 201)  # "Cultura" já existe, mas no blog B

    def test_nome_repetido_no_mesmo_blog_da_400_e_nao_500(self):
        resp = self.client.post('/api/categorias/', {'nome': 'Esportes'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class AcessoTestCase(TestCase):
    """Login obrigatório, superusuário sem Perfil e regras do fluxo editorial."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organizacao.objects.create(nome='Blog A', slug='blog-a')
        cls.user = User.objects.create_user('editor', password='senha-teste-123')
        Perfil.objects.create(usuario=cls.user, organizacao=cls.org)
        cat = Categoria.objects.create(organizacao=cls.org, nome='Geral')
        autor = Autor.objects.create(organizacao=cls.org, nome='Autor', email='a@a.com')
        cls.rascunho = Post.objects.create(
            organizacao=cls.org, titulo='Um rascunho', resumo='r', conteudo=CONTEUDO_OK,
            categoria=cat, autor=autor,
        )

    def test_painel_sem_login_redireciona_para_o_login(self):
        resp = self.client.get(reverse('painel_editorial'))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('painel_editorial')}")

    def test_api_sem_login_e_recusada(self):
        self.assertEqual(self.client.get('/api/posts/').status_code, 403)

    def test_superusuario_sem_perfil_nao_quebra(self):
        admin = User.objects.create_superuser('root', password='senha-teste-123')
        self.client.force_login(admin)
        self.assertRedirects(self.client.get(reverse('painel_editorial')), reverse('admin:index'))
        self.assertEqual(self.client.get('/api/posts/').status_code, 403)

    def test_rascunho_nao_aparece_no_site_publico(self):
        resp = self.client.get(reverse('detalhe_post', args=['blog-a', self.rascunho.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_acao_do_fluxo_exige_post(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('enviar_revisao', args=[self.rascunho.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_nao_publica_direto_do_rascunho(self):
        self.client.force_login(self.user)
        self.client.post(reverse('publicar_post', args=[self.rascunho.pk]))
        self.rascunho.refresh_from_db()
        self.assertEqual(self.rascunho.status, Post.RASCUNHO)

    def test_api_valida_conteudo_minimo_da_p1(self):
        self.client.force_login(self.user)
        resp = self.client.post('/api/posts/', {
            'titulo': 'Curta', 'resumo': 'r', 'conteudo': 'curto',
            'categoria': Categoria.objects.get().pk, 'autor': Autor.objects.get().pk,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('conteudo', resp.json())


def _data(ano, mes, dia):
    return timezone.make_aware(datetime(ano, mes, dia, 12, 0))


class DashboardTestCase(TestCase):
    """
    Testes das métricas do Dashboard (Aula 17, slide 37): "se o número
    está errado, o dashboard mente". Dados conhecidos, fáceis de conferir
    à mão:

      Blog A: 3 matérias  -> jan/2026: 1 publicada (10 leituras, 2 comentários)
                             fev/2026: 1 publicada (4 leituras) + 1 rascunho
      Blog B: 5 matérias publicadas (100 leituras cada)
    """

    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organizacao.objects.create(nome='Blog A', slug='blog-a')
        cls.org_b = Organizacao.objects.create(nome='Blog B', slug='blog-b')
        cls.org_vazia = Organizacao.objects.create(nome='Blog Vazio', slug='blog-vazio')

        cls.user_a = User.objects.create_user('editor_a', password='senha-teste-123')
        cls.user_vazio = User.objects.create_user('editor_vazio', password='senha-teste-123')
        Perfil.objects.create(usuario=cls.user_a, organizacao=cls.org_a)
        Perfil.objects.create(usuario=cls.user_vazio, organizacao=cls.org_vazia)

        cat_a = Categoria.objects.create(organizacao=cls.org_a, nome='Esportes')
        cat_a2 = Categoria.objects.create(organizacao=cls.org_a, nome='Política')
        autor_a = Autor.objects.create(organizacao=cls.org_a, nome='Autor A', email='a@a.com')

        def criar(org, cat, autor, titulo, status, criada, views=0):
            post = Post.objects.create(
                organizacao=org, titulo=titulo, resumo='r', conteudo=CONTEUDO_OK,
                categoria=cat, autor=autor, status=status, visualizacoes=views,
                data_publicacao=criada if status == Post.PUBLICADO else None,
            )
            # data_criacao é auto_now_add: ajustamos depois, via update()
            Post.objects.filter(pk=post.pk).update(data_criacao=criada)
            return post

        cls.jan = criar(cls.org_a, cat_a, autor_a, 'Jogo de janeiro', Post.PUBLICADO, _data(2026, 1, 15), 10)
        criar(cls.org_a, cat_a, autor_a, 'Jogo de fevereiro', Post.PUBLICADO, _data(2026, 2, 10), 4)
        criar(cls.org_a, cat_a2, autor_a, '=HYPERLINK("http://mal.example")', Post.RASCUNHO, _data(2026, 2, 20))
        for _ in range(2):
            Comentario.objects.create(
                organizacao=cls.org_a, post=cls.jan, nome_autor='Leitor', email='l@l.com', texto='Boa!',
            )

        cat_b = Categoria.objects.create(organizacao=cls.org_b, nome='Cultura')
        autor_b = Autor.objects.create(organizacao=cls.org_b, nome='Autor B', email='b@b.com')
        for i in range(5):
            criar(cls.org_b, cat_b, autor_b, f'Matéria secreta do B {i}', Post.PUBLICADO, _data(2026, 1, 5), 100)

    def setUp(self):
        self.client.force_login(self.user_a)

    def _get(self, **params):
        return self.client.get(reverse('dashboard'), params)

    # --- Total só da organização ------------------------------------------

    def test_kpis_contam_so_o_proprio_blog(self):
        kpis = self._get().context['kpis']
        self.assertEqual(kpis['total'], 3)          # o blog B tem 5: não podem aparecer
        self.assertEqual(kpis['publicadas'], 2)
        self.assertEqual(kpis['rascunhos'], 1)
        self.assertEqual(kpis['em_revisao'], 0)
        self.assertEqual(kpis['visualizacoes'], 14)  # 10 + 4 (o B somaria 500)
        self.assertEqual(kpis['comentarios'], 2)

    def test_ranking_serie_e_categorias_nao_vazam_dados_de_outro_blog(self):
        resp = self._get()
        self.assertEqual([r['titulo'] for r in resp.context['ranking']],
                         ['Jogo de janeiro', 'Jogo de fevereiro'])
        self.assertEqual(resp.context['ranking'][0]['n_comentarios'], 2)
        self.assertEqual(resp.context['por_mes'], [
            {'mes': '01/2026', 'total': 1, 'publicadas': 1},
            {'mes': '02/2026', 'total': 2, 'publicadas': 1},
        ])
        self.assertEqual(resp.context['por_categoria'], [
            {'categoria__nome': 'Esportes', 'total': 2},
            {'categoria__nome': 'Política', 'total': 1},
        ])
        self.assertNotContains(resp, 'Matéria secreta do B')

    # --- Período filtrando --------------------------------------------------

    def test_filtro_por_periodo(self):
        resp = self._get(inicio='2026-02-01', fim='2026-02-28')
        self.assertEqual(resp.context['kpis']['total'], 2)
        self.assertEqual([m['mes'] for m in resp.context['por_mes']], ['02/2026'])

    def test_fim_do_periodo_inclui_o_dia_inteiro(self):
        # A matéria de janeiro foi criada em 15/01 ao meio-dia
        resp = self._get(inicio='2026-01-15', fim='2026-01-15')
        self.assertEqual(resp.context['kpis']['total'], 1)

    def test_data_invalida_nao_gera_erro_500(self):
        resp = self._get(inicio='abc', fim='2026-13-45')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].errors)
        self.assertEqual(resp.context['kpis']['total'], 3)  # ignora o filtro inválido

    def test_inicio_depois_do_fim_e_recusado(self):
        resp = self._get(inicio='2026-03-01', fim='2026-01-01')
        self.assertIn('__all__', resp.context['form'].errors)

    # --- Dashboard vazio sem erro ------------------------------------------

    def test_dashboard_de_blog_sem_materias_nao_quebra(self):
        self.client.force_login(self.user_vazio)
        resp = self._get()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['kpis']['total'], 0)
        self.assertEqual(resp.context['kpis']['visualizacoes'], 0)  # Sum() vazio vira 0, não None
        self.assertContains(resp, 'Sem dados no período.')

    def test_dashboard_exige_login(self):
        self.client.logout()
        resp = self._get()
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('dashboard')}")

    # --- Desempenho: sem N+1 ---------------------------------------------------

    def test_metricas_usam_numero_fixo_de_consultas(self):
        # KPI (1) + comentários (1) + ranking (1) + série (1) + categorias (1).
        # Se alguém introduzir um N+1 aqui, o teste falha.
        with self.assertNumQueries(5):
            metricas.calcular_metricas(metricas.base_do_blog(self.org_a))

    def test_csv_nao_tem_n_mais_1(self):
        # Com N+1, cada matéria a mais custaria 2 consultas (categoria e
        # autor). Com select_related o total não muda com o tamanho do CSV.
        with CaptureQueriesContext(connection) as antes:
            self.client.get(reverse('exportar_csv'))
        post = Post.objects.filter(organizacao=self.org_a).first()
        for i in range(5):
            Post.objects.create(
                organizacao=self.org_a, titulo=f'Extra {i}', resumo='r', conteudo=CONTEUDO_OK,
                categoria=post.categoria, autor=post.autor,
            )
        with CaptureQueriesContext(connection) as depois:
            resp = self.client.get(reverse('exportar_csv'))
        self.assertEqual(len(resp.content.decode('utf-8-sig').strip().splitlines()), 9)
        self.assertEqual(len(depois), len(antes))

    # --- Exportação CSV ------------------------------------------------------

    def test_csv_exporta_so_o_proprio_blog_e_respeita_o_periodo(self):
        resp = self.client.get(reverse('exportar_csv'), {'inicio': '2026-02-01'})
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', resp['Content-Disposition'])
        texto = resp.content.decode('utf-8-sig')
        self.assertEqual(len(texto.strip().splitlines()), 3)  # cabeçalho + 2 matérias de fevereiro
        self.assertNotIn('secreta do B', texto)

    def test_csv_neutraliza_formula_do_excel(self):
        texto = self.client.get(reverse('exportar_csv')).content.decode('utf-8-sig')
        self.assertIn("'=HYPERLINK", texto)
        self.assertFalse(any(linha.startswith('=') for linha in texto.splitlines()))

    # --- API do dashboard -----------------------------------------------------

    def test_api_dashboard_devolve_as_mesmas_metricas(self):
        dados = self.client.get('/api/dashboard/').json()
        self.assertEqual(dados['kpis']['total'], 3)
        self.assertEqual(len(dados['por_mes']), 2)

    def test_api_dashboard_valida_o_periodo(self):
        self.assertEqual(self.client.get('/api/dashboard/', {'inicio': 'abc'}).status_code, 400)

    def test_api_dashboard_exige_login(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)
