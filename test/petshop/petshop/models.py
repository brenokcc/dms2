# -*- coding: utf-8 -*-
from datetime import datetime
from sloth.db import models, role, meta


@role('Administrador', 'cpf')
class Administrador(models.Model):

    nome = models.CharField(verbose_name='None')
    cpf = models.CharField(verbose_name='CPF')

    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administrador'

    def __str__(self):
        return self.nome


class DoencaManager(models.Manager):

    def all(self):
        return self.attach('contagiosas', 'nao_contagiosas')

    def contagiosas(self):
        return self.filter(contagiosa=True).filters()

    def nao_contagiosas(self):
        return self.filter(contagiosa=False).filters().inline_actions('fazer_alguma_coisa')

    @meta('Total de Doenças Contagiosas')
    def get_total_por_contagiosiade(self):
        return self.count('contagiosa')


class Doenca(models.Model):
    descricao = models.CharField(verbose_name='Descrição')
    contagiosa = models.BooleanField(verbose_name='Contagiosa')

    objects = DoencaManager()

    class Meta:
        icon = 'book'
        verbose_name = 'Doença'
        verbose_name_plural = 'Doenças'

    def __str__(self):
        return self.descricao

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Administrador')


class TipoProcedimento(models.Model):
    descricao = models.CharField(verbose_name='Descrição')
    cor = models.ColorField(verbose_name='Cor', default='#FFFFFF')
    valor = models.DecimalField(verbose_name='Valor')

    class Meta:
        verbose_name = 'Tipo de Procedimento'
        verbose_name_plural = 'Tipos de Procedimento'

    def __str__(self):
        return self.descricao

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Administrador')

    def get_dados_gerais(self):
        return self.value_set('descricao', ('cor', 'valor'))

    def view(self):
        return self.value_set('get_dados_gerais')


class TipoAnimal(models.Model):
    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        verbose_name = 'Tipo de Animal'
        verbose_name_plural = 'Tipos de Animais'

    def __str__(self):
        return self.descricao

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Administrador')


@role('Funcionário', 'cpf')
class Funcionario(models.Model):

    nome = models.CharField(verbose_name='None')
    cpf = models.CharField(verbose_name='CPF')

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Administrador')


@role('Cliente', 'cpf')
class Cliente(models.Model):

    nome = models.CharField(verbose_name='None')
    cpf = models.CharField(verbose_name='CPF')

    class Meta:
        icon = 'person-lines-fill'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    class Permission:
        admin = 'Funcionário',

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Funcionário')

    def get_dados_gerais(self):
        return self.value_set(('nome', 'cpf'))

    def get_animais(self):
        return self.animal_set.all()

    def get_total_gasto_por_tipo_procedimento(self):
        return Procedimento.objects.filter(tratamento__animal__proprietario=self).sum('tipo__valor', 'tipo')

    def view(self):
        return self.value_set('get_dados_gerais', 'get_animais', 'get_total_gasto_por_tipo_procedimento')


class AnimalManager(models.Manager):

    def all(self):
        return self.role_lookups(
            'Cliente', proprietario='cliente'
        ).role_lookups(
            'Funcionário'
        ).display('foto', 'nome', 'descricao', 'get_situacao').rows()

    def get_qtd_por_tipo(self):
        return self.all().count('tipo')

    def get_qtd_por_periodo(self):
        return self.all().count('data_cadastro')


class Animal(models.Model):
    foto = models.ImageField(verbose_name='Foto', upload_to='animais')

    nome = models.CharField(verbose_name='Nome')
    tipo = models.ForeignKey(TipoAnimal, verbose_name='Tipo')

    descricao = models.TextField(verbose_name='Descrição')

    proprietario = models.ForeignKey(Cliente, verbose_name='Proprietário')
    data_cadastro = models.DateField(verbose_name='Data do Cadastro', default=datetime.today)

    objects = AnimalManager()

    class Meta:
        icon = 'github'
        verbose_name = 'Animal'
        verbose_name_plural = 'Animais'
        fieldsets = {
            'Dados Gerais': (('nome', 'tipo'), 'foto', 'data_cadastro', 'descricao', 'proprietario'),
        }

    def __str__(self):
        return self.nome

    @meta('Situação', renderer='badges/status')
    def get_situacao(self):
        if self.get_tratamentos().filter(data_fim__isnull=True).exists():
            return 'warning', 'Em Tratamento'
        return 'success', 'Saudável'

    def get_dados_gerais(self):
        return self.value_set(('nome', 'tipo'), 'descricao').image('foto')

    @meta('Proprietário')
    def get_proprietario(self):
        return self.proprietario.value_set(('nome', 'cpf'))

    def get_tratamentos(self):
        return self.tratamento_set.ignore(
            'animal'
        ).global_actions(
            'IniciarTratamento', 'Batata'
        ).actions(
            'ExcluirTratamento'
        ).batch_actions(
            'ExcluirTratamentos'
        ).accordion()

    def get_tratamentos_por_doenca(self):
        return self.tratamento_set.count('doenca').donut_chart()

    def view(self):
        return self.value_set('get_situacao', 'get_dados_gerais', 'get_tratamentos').append('get_proprietario', 'get_tratamentos_por_doenca').actions('fazer_alguma_coisa2')

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains('Funcionário')

    def has_view_permission(self, user):
        return self.proprietario.cpf == user.username


class TratamentoManager(models.Manager):

    def all(self):
        return self.calendar('data_inicio').preview('get_procedimentos_por_tipo', modal=True).verbose_name('todos')

    def em_andamento(self):
        return self.filter(data_fim__isnull=True)

    def total_por_animal(self):
        return self.count('animal').column_chart()

    def total_por_doenca(self):
        return self.count('animal').donut_chart()

    def xx(self):
        return self.value_set('all').append('total_por_animal').attach('total_por_doenca')


class Tratamento(models.Model):
    animal = models.ForeignKey(Animal, verbose_name='Animal')
    doenca = models.ForeignKey(Doenca, verbose_name='Doença')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término', null=True)
    eficaz = models.BooleanField(verbose_name='Eficaz', null=True)

    objects = TratamentoManager()

    class Meta:
        icon = 'journal-text'
        verbose_name = 'Tratamento'
        verbose_name_plural = 'Tratamentos'
        fieldsets = {
            'Dados Gerais': (('animal', 'doenca'), ('data_inicio', 'data_fim')),
            'Resultado': ('eficaz',),
        }

    def __str__(self):
        return '{} - Tratamento de {} contra {}'.format(self.id, self.animal, self.doenca)

    @meta('Etapas', renderer='utils/steps')
    def get_etapas(self):
        etapas = []
        etapas.append(('Início', self.data_inicio))
        for procedimento in self.procedimento_set.all():
            etapas.append((procedimento.tipo, procedimento.data_hora))
        etapas.append(('Fim', self.data_fim))
        return etapas

    def get_dados_gerais(self):
        return self.value_set(('animal', 'doenca'), ('data_inicio', 'data_fim'))#.actions('RegistrarProcedimento', inline=True)

    def get_procedimentos(self):
        return self.procedimento_set.ignore('tratamento').inline_actions('RegistrarProcedimento').actions('edit', 'delete').totalizer('tipo__valor').timeline().expand()

    @meta('Procedimentos por Tipo')
    def get_procedimentos_por_tipo(self):
        return self.procedimento_set.count('tipo').bar_chart()

    def get_eficacia(self):
        return self.value_set('eficaz').actions('FinalizarTratamento', 'RetomarTratamento')

    def get_detalhamento(self):
        return self.value_set('get_procedimentos_por_tipo', 'get_x')

    def get_x(self):
        return self.value_set('get_procedimentos', 'get_etapas')

    def view(self):
        return self.value_set('get_dados_gerais', 'get_detalhamento', 'get_eficacia')#.append('get_etapas')

    def has_view_permission(self, user):
        return user.is_superuser or user.roles.contains('Funcionário') or self.animal.proprietario.cpf == user.username

    def has_edit_permission(self, user):
        return user.is_superuser or user.roles.contains('Funcionário') and not self.procedimento_set.exists()

    def has_delete_permission(self, user):
        return self.has_edit_permission(user)


class ProcedimentoManager(models.Manager):

    def get_valor_gasto(self):
        return self.sum('tipo__valor')


class Procedimento(models.Model):
    tratamento = models.ForeignKey(Tratamento, verbose_name='Tratamento')

    tipo = models.ForeignKey(TipoProcedimento, verbose_name='Tipo')
    data_hora = models.DateTimeField(verbose_name='Data/Hora')

    observacao = models.TextField(verbose_name='Observação', blank=True)

    objects = ProcedimentoManager()

    class Meta:
        verbose_name = 'Procedimento'
        verbose_name_plural = 'Procedimentos'
        fieldsets = {
            'Dados Gerais': ('tratamento', ('tipo', 'data_hora'),),
            'Outras Informações': ('observacao',),
        }

    def __str__(self):
        return 'Tratamento {}'.format(self.id)

    def has_edit_permission(self, user):
        return user.roles.contains('Funcionário') and self.tratamento and self.tratamento.data_fim is None
