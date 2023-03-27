# -*- coding: utf-8 -*-

from sloth import actions

from .models import Servidor, Ferias, Estado, Frequencia, Municipio
from .tasks import TarefaAssincrona

class ExecutarTarefaAssincrona(actions.Action):
    class Meta:
        verbose_name = 'Executar Tarefa Assíncrona'

    def submit(self):
        self.run(TarefaAssincrona(), TarefaAssincrona())


class AdicionarMunicipioEstado(actions.Action):

    class Meta:
        model = Municipio
        related_field = 'estado'
        verbose_name = 'Adicionar Município'
        has_permission = 'Chefe',


class HomologarFrequencia(actions.Action):
    class Meta:
        verbose_name = 'Homologar'
        model = Frequencia
        fields = 'homologado',


class RegistrarPonto(actions.Action):

    class Meta:
        model = Frequencia
        fields = 'horario', 'homologado',
        related_field = 'servidor'


class DefinirSetor(actions.Action):
    class Meta:
        model = Servidor
        fields = 'setor',
        update = '', ''


class CadastrarForm(actions.Action):
    class Meta:
        verbose_name = 'Cadastrar Estado'
        model = Estado
        fieldsets = {
            'Dados Gerais': ('sigla', 'endereco', 'telefones'),
        }


class CadastrarServidor(actions.Action):

    class Meta:
        model = Servidor
        fieldsets = {
            'Dados Gerais': ('nome', 'foto', ('cpf', 'matricula', 'data_nascimento', 'naturalidade'), 'ativo'),
            'Endereço': ('endereco',),
        }


class InformarCidadesMetropolitanas(actions.Action):

    class Meta:
        model = Estado
        fields = 'cidades_metropolitanas',
        verbose_name = 'Informar Cidades Metropolitanas'
        submit_label = 'Informar'

    def get_cidades_metropolitanas_queryset(self, queryset):
        return queryset.filter(estado=self.instance)


class FazerAlgumaCoisa(actions.Action):
    mensagem = actions.CharField(label='Mensagem', widget=actions.Textarea())

    class Meta:
        icon = 'chat-dots'
        verbose_name = 'Fazer Alguma Coisa'
        style = 'warning'
        reload = 'get_dados_gerais',


class EditarSiglaEstado(actions.Action):
    class Meta:
        verbose_name = 'Editar Sigla'
        model = Estado
        fields = 'sigla',


class CorrigirNomeServidor1(actions.Action):
    class Meta:
        verbose_name = 'Corrigir Nome 1'
        model = Servidor
        fields = 'nome',


class CorrigirNomeServidor(actions.Action):
    class Meta:
        verbose_name = 'Corrigir Nome'
        model = Servidor
        fields = 'nome',

    def has_permission(self, user):
        return False


class EditarFerias(actions.Action):
    class Meta:
        verbose_name = 'Editar'
        model = Ferias
        fields = 'inicio', 'fim'


class AtivarServidor(actions.Action):
    class Meta:
        verbose_name = 'Ativar'
        model = Servidor
        fields = ()

    def submit(self):
        self.instance.ativo = True
        super().submit()


class InativarServidores(actions.Action):
    class Meta:
        title = 'Inativar'
        model = Servidor
        fields = ()

    def submit(self):
        self.instance.ativo = False
        super().submit()


class InformarEndereco(actions.Action):
    class Meta:
        model = Servidor
        verbose_name = 'Informar Endereço'
        icon = 'archive'
        style = 'success'
        fields = 'endereco',
        modal = True


class ExcluirEndereco(actions.Action):
    class Meta:
        verbose_name = 'Excluir'
        model = Servidor
        fields = ()

    def submit(self):
        self.instance.endereco.delete()
        self.redirect(message='Endereço excluído com sucesso.')


class CadastrarFerias(actions.Action):
    class Meta:
        verbose_name = 'Cadastrar'
        related_field = 'servidor'
        model = Ferias


class AlterarFerias(actions.Action):
    class Meta:
        verbose_name = 'Alterar'
        model = Ferias
        fields = 'inicio', 'fim'


class ExcluirFerias(actions.Action):
    class Meta:
        verbose_name = 'Excluir'
        style = 'danger'

    def submit(self):
        self.instance.delete()
        self.message('Férias excluídas com sucesso')
        self.redirect()
