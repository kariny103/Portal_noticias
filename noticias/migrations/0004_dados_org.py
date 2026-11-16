"""
ETAPA 2 da migração multi-organização (Aula 14, slide "Migração de
Dados com RunPython").

Todos os registros que já existiam na P1 (sem organização) passam a
pertencer ao blog padrão "Portal Notícias Maricá". Assim nenhum dado
da P1 é perdido quando a FK virar obrigatória na etapa 3.

Usamos apps.get_model (e não o import direto do model) para que a
migração enxergue o model como ele era NESTE momento da história.
"""
from django.db import migrations

MODELS_DE_NEGOCIO = ['Categoria', 'Tag', 'Autor', 'Post', 'Comentario']


def org_padrao(apps, schema_editor):
    Organizacao = apps.get_model('core', 'Organizacao')
    org, _ = Organizacao.objects.get_or_create(
        slug='marica',
        defaults={'nome': 'Portal Notícias Maricá'},
    )
    for nome_model in MODELS_DE_NEGOCIO:
        Model = apps.get_model('noticias', nome_model)
        Model.objects.filter(organizacao__isnull=True).update(organizacao=org)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('noticias', '0003_organizacao_nula'),
    ]

    operations = [
        migrations.RunPython(org_padrao, migrations.RunPython.noop),
    ]
