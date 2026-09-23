# Portal de Últimas Notícias de Maricá — Projeto P1 (Django)

Blog / Portal de Últimas Notícias de Maricá com **fluxo de publicação com aprovação editorial**
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

## Estrutura do projeto

```
portal_noticias/          <- projeto Django (settings, urls gerais)
noticias/                 <- app Django (a "peça de Lego" do sistema)
    models.py              Categoria, Tag, Autor, Post, Comentario
    admin.py                registro no Django Admin
    forms.py                 PostForm e ComentarioForm (ModelForm)
    views.py                  lógica de cada página
    urls.py                    urls do app (criado à mão, como na Aula 5)
    templates/noticias/         HTML com herança de templates (base.html)
    static/noticias/css/         estilo.css
    management/commands/
        seed_dados.py             popula dados de exemplo
manage.py
requirements.txt
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
- **http://127.0.0.1:8000/** — site público (só matérias publicadas)
- **http://127.0.0.1:8000/painel/** — Painel Editorial (fluxo de aprovação)
- **http://127.0.0.1:8000/admin/** — Django Admin

Login do Admin já criado:
- usuário: `admin`
- senha: `admin123`

### Rodando em outra máquina (do zero)

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_dados          # opcional: cria dados de exemplo
python manage.py createsuperuser     # cria seu próprio login de admin
python manage.py runserver
```

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
   (ModelForm da Aula 5), mostre que ela nasce como rascunho.
4. **Site público** (`/`) — mostre a listagem, o filtro por categoria e a
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

## Próximos passos (P2, fora do escopo deste P1)

- Autenticação/login para autores e revisores (permissões reais).
- Múltiplos blogs e papéis de usuário (editor, redator, leitor).
- Dashboard com métricas.
- API com Django REST Framework (DRF), introduzido na Aula 13.
