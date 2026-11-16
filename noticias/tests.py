"""
Roteiro de isolamento multi-organização (Aula 14, slide 18) em forma
de testes automatizados, para rodar a cada nova tela:

    python manage.py test

Cenário: dois blogs (A = Maricá, B = Niterói), um editor em cada um.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Organizacao, Perfil
from .models import Autor, Categoria, Post, Tag

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
