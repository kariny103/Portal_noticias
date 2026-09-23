"""
Forms — recebendo dados do usuário (Aula 5).

Usamos ModelForm: o Django gera os campos, os tipos e a validação
a partir do model automaticamente.
"""
from django import forms

from .models import Post, Comentario


class PostForm(forms.ModelForm):
    """
    Formulário de criação/edição de matérias.

    O campo `status` fica de fora de propósito: a mudança de estado
    (rascunho -> revisão -> publicado) é feita pelos botões de ação
    no Painel Editorial, não digitada livremente no formulário —
    isso é o que caracteriza o "fluxo de publicação com aprovação
    editorial" pedido no projeto.
    """

    class Meta:
        model = Post
        fields = ['titulo', 'resumo', 'conteudo', 'imagem_capa', 'categoria', 'autor', 'tags']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Título da matéria'}),
            'resumo': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Resumo curto (aparece na listagem)'}),
            'conteudo': forms.Textarea(attrs={'rows': 12}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def clean_conteudo(self):
        """
        Feature 2 do P1 — Validação customizada.

        Regra de negócio: uma matéria não pode ser publicada com um texto
        abaixo do tamanho mínimo (Post.CONTEUDO_MINIMO caracteres). Como
        todo post criado aqui segue para revisão e publicação, a regra é
        checada já no cadastro/edição — assim nenhuma "notícia" vazia ou
        com uma linha só chega ao Painel Editorial.

        Os espaços das pontas são descartados antes de contar, para que
        não dê para "enganar" a regra preenchendo com espaços em branco.
        """
        conteudo = (self.cleaned_data.get('conteudo') or '').strip()
        if len(conteudo) < Post.CONTEUDO_MINIMO:
            raise forms.ValidationError(
                f'O conteúdo da matéria precisa ter pelo menos {Post.CONTEUDO_MINIMO} '
                f'caracteres para poder ser publicado (atualmente tem {len(conteudo)}).'
            )
        return conteudo


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['nome_autor', 'email', 'texto']
        widgets = {
            'nome_autor': forms.TextInput(attrs={'placeholder': 'Seu nome'}),
            'email': forms.EmailInput(attrs={'placeholder': 'seu@email.com'}),
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva seu comentário...'}),
        }
