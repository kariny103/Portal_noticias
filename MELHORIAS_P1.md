# Melhorias da P1 (Aula 13)

Revisão do MVP entregue na P1 antes de começar a P2. A API e a
multi-organização são construídas em cima dos models e das views da P1,
então tudo o que estava frágil precisava ser corrigido primeiro.

| # | Problema encontrado na P1 | Tipo | Situação |
|---|---|---|---|
| 1 | **Qualquer visitante podia publicar, editar ou excluir matérias.** O Painel Editorial e o CRUD não exigiam login. | Segurança | Corrigido: login obrigatório (`organizacao_required` em `core/utils.py`). |
| 2 | **Rascunhos podiam ser lidos no site público** digitando o id na URL (`/post/<id>/`), porque `detalhe_post` buscava o post sem olhar o status. | Regra de negócio | Corrigido: a página pública só abre matéria `PUBLICADO` (e do blog certo). |
| 3 | **As transições do fluxo editorial não conferiam o estado atual**, nem o método HTTP. Era possível publicar direto um rascunho (pulando a revisão) ou disparar a ação com um simples GET. | Regra de negócio | Corrigido: `@require_POST` e `_mudar_status()`, que só aceita a transição a partir do estado esperado. |
| 4 | **`unique=True` global em `Categoria.nome` e `Tag.nome`.** Com vários blogs, o blog B não poderia ter uma categoria "Esportes" se o blog A já tivesse. | Modelagem | Corrigido: `UniqueConstraint(organizacao, nome)`. A API trata o duplicado com erro 400, em vez de estourar IntegrityError. |
| 5 | **A regra de conteúdo mínimo está escrita em três lugares**: `PostForm.clean_conteudo`, `views.publicar_post` e agora `PostSerializer.validate_conteudo`. | Dívida técnica | Pendente: mover para `Post.clean()` e reaproveitar nos três lugares. |
