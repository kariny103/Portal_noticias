# Portal Notícias Maricá — Projeto P1 (Django)

Blog / Portal Notícias Maricá com **fluxo de publicação com aprovação editorial**
(3 estados: Rascunho → Em Revisão → Publicado), construído em **Django puro**
(sem framework de front-end separado), seguindo exatamente o padrão ensinado
nas Aulas 3, 4 e 5 da disciplina: **MVT, ORM, Django Admin, Views, URLs,
Templates com herança e ModelForms**.

## Entidades (models)

| Model | Campos principais |
|---|---|
| `Categoria` | nome |
| `Tag` | nome |
| `Autor` | nome, email, bio |
| `Post` | titulo, resumo, conteudo, imagem_capa, categoria (FK), autor (FK), tags (M2M), **status**, data_criacao, data_publicacao, visualizacoes |
| `Comentario` | post (FK), nome_autor, email, texto, data_criacao |

## O fluxo de publicação (o requisito central do P1)

```
RASCUNHO  --enviar p/ revisão-->  EM REVISÃO  --aprovar-->  PUBLICADO
   ^                                   |                         |
   +---------- devolver ---------------+                         |
   <----------------------- despublicar ------------------------+
```

- Toda matéria nova nasce como **Rascunho** (não aparece no site público).
- O editor manda para **Em Revisão** no Painel Editorial.
- Um revisor aprova (**Publicado** — vai ao ar e recebe `data_publicacao`)
  ou devolve para rascunho.
- Uma matéria publicada pode ser despublicada a qualquer momento.

## Layout da home e das categorias

A página inicial e as páginas de categoria usam um layout de duas colunas:

- **Coluna principal** (`.coluna-principal`): grade de cards das notícias publicadas.
- **Barra lateral** (`_sidebar.html`, reaproveitada com `{% include %}`):
  - **Mais Lidas** — ranking real, baseado no campo `Post.visualizacoes`
    (incrementado a cada acesso à página de detalhe de uma matéria publicada,
    em `views.detalhe_post`). Não é estático: se você acessar uma notícia
    várias vezes, ela sobe no ranking.
  - **Previsão do Tempo** — widget ilustrativo (dado fixo, sem integração
    com nenhuma API de meteorologia — isso ficaria para o P2).
  - **Categorias** — lista de todas as categorias cadastradas.

O rodapé (em `base.html`) também foi estruturado em colunas: sobre o portal
com redes sociais, Links Rápidos, Sobre Nós e Contato, com uma barra final
de copyright.

Isso é implementado em `noticias/views.py` (funções `enviar_para_revisao`,
`devolver_rascunho`, `publicar_post`, `despublicar_post`) e visualizado no
**Painel Editorial** (`/painel/`), a tela mais importante para mostrar ao
professor.

## Features obrigatórias do P1

### Feature 1 — Busca e Filtro na Listagem

A página inicial (`/`) tem um formulário de busca acima das notícias:

- **Busca por texto** (`?q=`): procura o termo no **título** ou no **resumo**
  da matéria, com `icontains` (não diferencia maiúsculas de minúsculas).
- **Filtro por categoria** (`?categoria=`) e **por tag** (`?tag=`), com `<select>`.
- Os filtros funcionam juntos ou separados, e o termo digitado continua no
  campo depois da pesquisa (`value="{{ request.GET.q }}"`).
- Sem resultados, o `{% empty %}` mostra uma mensagem com link para limpar
  os filtros.
- **Desafio extra:** todas as condições são montadas com `Q()` e aplicadas
  numa única consulta (`views.lista_posts`).

> Observação: no SQLite, `icontains` só ignora maiúsculas/minúsculas em
> letras sem acento (buscar "MARICÁ" não encontra "Maricá"). No PostgreSQL
> isso funciona normalmente.

### Feature 2 — Validação Customizada no Formulário

`PostForm.clean_conteudo()` (em `forms.py`) impede que uma matéria seja
salva com o conteúdo abaixo de **50 caracteres** (`Post.CONTEUDO_MINIMO`),
contando sem os espaços das pontas. A mensagem de erro aparece no próprio
formulário, via `{{ form.as_p }}`. A view `publicar_post` repete a checagem,
porque matérias criadas pelo `/admin/` não passam pelo `PostForm`.

## P2 — de MVP a mini-SaaS (Aulas 13 e 14)

O card do projeto pede para a P2: **múltiplos blogs, papéis, dashboard e
API DRF**. Já estão prontos os pilares das Aulas 13 e 14:

### Pilar 4 — API REST com DRF (Aula 13)

Endpoints em `/api/` (arquivos `serializers.py`, `api_views.py` e
`api_urls.py`, com as *generics* do DRF):

| Recurso | Listar / criar | Detalhar / atualizar / apagar |
|---|---|---|
| Matérias | `GET/POST /api/posts/` | `GET/PUT/PATCH/DELETE /api/posts/<id>/` |
| Categorias | `GET/POST /api/categorias/` | `.../api/categorias/<id>/` |
| Tags | `GET/POST /api/tags/` | `.../api/tags/<id>/` |
| Autores | `GET/POST /api/autores/` | `.../api/autores/<id>/` |

- Só usuário autenticado (`IsAuthenticated`). Sem login a resposta é 403.
- `fields` sempre listados explicitamente: o campo `organizacao` nunca aparece no JSON.
- O `status` da matéria é só leitura: a aprovação editorial continua no Painel.
- A regra da Feature 2 (conteúdo mínimo) também vale na API (`validate_conteudo` → erro 400).
- Teste no navegador: entre em `/api-auth/login/` e abra `/api/posts/` (Browsable API).
  Ou pelo terminal: `curl -u editor_marica:portal2026 http://127.0.0.1:8000/api/posts/`.

A revisão da P1 pedida na Aula 13 está em [MELHORIAS_P1.md](MELHORIAS_P1.md).

### Pilar 1 — Multi-organização: vários blogs na mesma base (Aula 14)

Cada **organização é um blog** (ex.: *Portal Notícias Maricá* e
*Portal Notícias Niterói*). Estratégia: **coluna discriminadora**, ou seja,
uma FK para a organização em todo model de negócio.

- **App `core`**: `Organizacao` (nome, slug, criada_em), a base abstrata
  `DaOrganizacao` e o `Perfil` (liga o `User` ao blog dele).
- **Todos os models do blog herdam `DaOrganizacao`**: Categoria, Tag, Autor, Post e Comentario.
- **Migração sem perder os dados da P1**, em 3 etapas:
  `0003_organizacao_nula` (FK com `null=True`) → `0004_dados_org`
  (`RunPython` move tudo para o blog "Portal Notícias Maricá") →
  `0005_organizacao_obrigatoria` (FK obrigatória).
- **Regra de ouro**: `core/utils.py` tem o `org_atual(request)`, o único
  lugar que define o blog do usuário, sempre a partir de `request.user.perfil`
  e nunca da URL ou do formulário. Toda view interna usa `@organizacao_required`.
- **Toda consulta filtra** por `organizacao`. Todo `get_object_or_404` recebe
  a organização: abrir o id de uma matéria de outro blog dá **404**.
- **Criação com `commit=False`**: o blog é preenchido pela view, não pelo form.
- **Selects filtrados**: categoria, autor e tags do `PostForm` (e da API) só
  mostram e aceitam registros do próprio blog.
- **Unicidade por blog**: `UniqueConstraint(organizacao, nome)` em Categoria e Tag.
- **Site público por blog**: `/` lista os blogs, e cada blog tem o seu site em
  `/blog/<slug>/`, com busca, categorias e "Mais Lidas" só daquele blog.
- **Superusuário sem Perfil** não quebra o sistema: recebe uma mensagem e é
  levado ao Admin para criar o Perfil.

### Roteiro de isolamento (Aula 14, slide 18): resultado

Executado com dois usuários de blogs diferentes. Os cenários também viraram
testes automatizados em `noticias/tests.py` (`python manage.py test`, 21 testes, todos passando).

| Cenário | Esperado | Resultado |
|---|---|---|
| Editor A abre o Painel / a lista da API | Vê só as matérias do blog A | ✅ OK |
| Editor A abre `/post/<id-do-B>/editar/` ou `/api/posts/<id-do-B>/` | 404 | ✅ OK |
| Editor A cria uma matéria (pelo form ou pela API, mesmo enviando `organizacao` do B no JSON) | Gravada no blog A | ✅ OK |
| Formulário do editor A | Selects só com opções do blog A; categoria do B é recusada | ✅ OK |
| Editor A cadastra categoria com nome que já existe no blog B | Permitido (unicidade é por blog) | ✅ OK |
| Editor A cadastra categoria repetida no próprio blog | Erro 400, sem IntegrityError | ✅ OK |
| Site público do blog A com o id de uma matéria do B | 404 | ✅ OK |

## Estrutura do projeto

```
portal_noticias/          <- projeto Django (settings, urls gerais)
core/                     <- app da P2: o que é transversal ao sistema
    models.py              Organizacao (blog), DaOrganizacao (base abstrata), Perfil
    utils.py                org_atual() e @organizacao_required
    admin.py                 registro de Organizacao e Perfil
noticias/                 <- app Django (a "peça de Lego" do sistema)
    models.py              Categoria, Tag, Autor, Post, Comentario
    admin.py                registro no Django Admin
    forms.py                 PostForm e ComentarioForm (ModelForm)
    views.py                  lógica de cada página
    urls.py                    urls do app (criado à mão, como na Aula 5)
    serializers.py              P2: serializers da API (DRF)
    api_views.py                 P2: views da API (generics)
    api_urls.py                   P2: urls da API (/api/...)
    tests.py                       P2: roteiro de isolamento automatizado
    templates/noticias/         HTML com herança de templates (base.html)
    templates/registration/     tela de login
    static/noticias/css/         estilo.css
    management/commands/
        seed_dados.py             popula 2 blogs, usuários e dados de exemplo
manage.py
requirements.txt
MELHORIAS_P1.md            revisão da P1 (Aula 13)
.env / .env.example        configuração (nunca comitar o .env real)
```

## Como rodar (Windows / PowerShell)

O projeto já vem com um ambiente virtual (`venv/`) criado e as dependências
instaladas, banco SQLite migrado, dados de exemplo carregados e um
superusuário pronto. Para rodar agora mesmo:

```powershell
.\venv\Scripts\activate
python manage.py runserver
```

Abra no navegador:
- **http://127.0.0.1:8000/** — lista dos blogs
- **http://127.0.0.1:8000/blog/marica/** — site público de um blog (só matérias publicadas)
- **http://127.0.0.1:8000/painel/** — Painel Editorial (exige login; mostra só o blog do usuário)
- **http://127.0.0.1:8000/api/posts/** — API REST (exige login)
- **http://127.0.0.1:8000/admin/** — Django Admin (vê todos os blogs)

Logins já criados:

| Usuário | Senha | Blog |
|---|---|---|
| `admin` (superusuário) | `admin123` | Portal Notícias Maricá |
| `editor_marica` | `portal2026` | Portal Notícias Maricá |
| `editor_niteroi` | `portal2026` | Portal Notícias Niterói |

> Se o banco não tiver esses usuários, rode `python manage.py seed_dados`.

### Rodando em outra máquina (do zero)

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_dados          # opcional: cria 2 blogs, editores e dados de exemplo
python manage.py createsuperuser     # cria seu próprio login de admin
python manage.py runserver
```

> Use sempre `python -m pip install ...` com o venv ativo. Se o venv foi
> copiado de outra pasta, o `pip.exe` pode instalar no venv antigo.

Para rodar os testes do roteiro de isolamento: `python manage.py test`.

## Banco de dados: SQLite (padrão) ou PostgreSQL

O arquivo `.env` controla o banco pela variável `DB_ENGINE`:

- `DB_ENGINE=sqlite3` (como está agora) — zero configuração, ótimo para testar
  e para a apresentação.
- `DB_ENGINE=postgresql` — o banco oficial ensinado na disciplina.

### Trocando para PostgreSQL

1. Crie o banco: `CREATE DATABASE portal_noticias_db;` (via psql/pgAdmin).
2. No `.env`, ajuste:
   ```
   DB_ENGINE=postgresql
   DB_NAME=portal_noticias_db
   DB_USER=postgres
   DB_PASSWORD=sua_senha_real
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. Rode novamente:
   ```powershell
   python manage.py migrate
   python manage.py seed_dados
   python manage.py createsuperuser
   ```

O `psycopg2-binary` (driver do PostgreSQL) já está no `requirements.txt`,
então não precisa instalar mais nada.

## Roteiro sugerido para a apresentação

1. **Django Admin** (`/admin/`) — mostre `Categoria`, `Tag`, `Autor` já
   cadastrados (Aula 4: "baterias inclusas", painel gerado automaticamente
   a partir dos models).
2. **Painel Editorial** (`/painel/`) — o coração do projeto. Mostre as 3
   matérias de exemplo em estados diferentes (rascunho, em revisão,
   publicado) e demonstre ao vivo:
   - clique em "Enviar p/ revisão" num rascunho;
   - clique em "Aprovar e publicar" numa matéria em revisão;
   - mostre que ela aparece imediatamente na home pública.
3. **Nova Matéria** (`/novo/`) — crie uma matéria pelo formulário
   (ModelForm da Aula 5), mostre que ela nasce como rascunho. Antes, tente
   salvar com um conteúdo curto para mostrar a mensagem de erro da
   **Feature 2**.
4. **Site público** (`/`) — mostre a listagem com a **busca e os filtros
   da Feature 1** (ex.: buscar "time" e depois escolher uma categoria) e a
   página de detalhe de um post, incluindo o formulário de comentário
   (CSRF token, `{{ form.as_p }}`).
5. Se quiser, explique o ciclo **URL → View → Template** olhando
   `noticias/urls.py` → `noticias/views.py` → `noticias/templates/noticias/`.

## Conceitos da disciplina aplicados no projeto

- **MVT** (Aula 3): `models.py` (dados), `views.py` (lógica), `templates/`
  (tela).
- **ORM** (Aula 3-4): `Post.objects.filter(status=Post.PUBLICADO)`,
  `objects.create`, `.save()`, sem uma linha de SQL escrita à mão.
- **Migrations** (Aula 4): `makemigrations` + `migrate` levaram os models
  ao banco.
- **Django Admin** (Aula 4): `admin.py` com `list_display`, `list_filter`,
  `search_fields`.
- **Views + URLs** (Aula 5): funções em `views.py` conectadas a rotas em
  `urls.py` (app) incluído no `urls.py` do projeto.
- **Templates + herança** (Aula 5): `base.html` com `{% block content %}`,
  páginas com `{% extends %}`, `{% for %}`, `{% if %}`.
- **Forms / ModelForm** (Aula 5): `PostForm` e `ComentarioForm`, com
  `{% csrf_token %}` e `{{ form.as_p }}`.
- **Credenciais fora do código** (Aula 4): `python-dotenv` + `.env`
  (nunca versionado — veja `.gitignore`).

## Próximos passos da P2

- [x] API com Django REST Framework (Aula 13)
- [x] Múltiplos blogs com isolamento de dados e login (Aula 14)
- [ ] Papéis de usuário (ex.: editor-chefe aprova/publica, redator só escreve), nas telas e na API (Aula 15)
- [ ] Dashboard com métricas por blog: matérias por status, mais lidas e publicações por período (Aula 17)
- [ ] Mover a regra de conteúdo mínimo para `Post.clean()` (item 5 do MELHORIAS_P1.md)
