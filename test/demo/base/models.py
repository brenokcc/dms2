from dms2.db import models
from dms2.decorators import meta, allow


class Estado(models.Model):
    sigla = models.CharField('Sigla')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estado'

    def __str__(self):
        return self.sigla


class Municipio(models.Model):
    nome = models.CharField('Nome')
    estado = models.ForeignKey(Estado, verbose_name='Estado')

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)


class Endereco(models.Model):
    logradouro = models.CharField('Logradouro')
    numero = models.CharField('Número')
    municipio = models.ForeignKey(Municipio, verbose_name='Município')

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'


class ServidorSet(models.QuerySet):

    @meta('Todos')
    @allow('AtivarServidor')
    def all(self):
        super().all()

    @meta('Com Endereço')
    def com_endereco(self):
        return self.filter(endereco__isnull=False)

    @allow('InativarServidores')
    def sem_endereco(self):
        return self.filter(endereco__isnull=True)

    @meta('Sem Endereço')
    def inativos(self):
        return self.filter(ativo=False)


class Servidor(models.Model):
    matricula = models.CharField('Matrícula')
    nome = models.CharField('Nome')
    cpf = models.CharField('CPF')
    endereco = models.OneToOneField(Endereco, verbose_name='Endereço')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Servidor'
        verbose_name_plural = 'Servidores'

    def __str__(self):
        return self.nome

    def add(self):
        self.save()

    def edit(self):
        self.save()

    def remove(self):
        self.delete()

    def can_view_nome(self, **kwargs):
        return self.pk is not None

    @meta('Dados Gerais', primary=True)
    def get_dados_gerais(self):
        return self.values('nome', 'cpf')

    @meta('Endereço')
    @allow('InformarEndereco', 'EditarEndereco', 'ExcluirEndereco')
    def get_endereco(self):
        return self.endereco.values(
            'logradouro', ('logradouro', 'numero'), ('municipio', 'municipio__estado')
        )

    def view(self):
        return self.values('get_dados_gerais', 'get_endereco', 'get_dados_recursos_humanos')

    @meta('Frequências')
    def get_frequencias(self):
        return self.frequencia_set.paginate(5)

    @meta('Férias', auxiliary=True)
    @allow('CadastrarFerias', 'AlterarFerias', 'ExcluirFerias')
    def get_ferias(self):
        return self.ferias_set.all()

    @meta('Recursos Humanos')
    def get_dados_recursos_humanos(self):
        return self.values('get_frequencias', 'get_ferias', 'get_endereco')


class Ferias(models.Model):
    servidor = models.ForeignKey(Servidor, verbose_name='Servidor')
    ano = models.IntegerField('Ano')
    inicio = models.DateField('Início')
    fim = models.DateField('Fim')

    class Meta:
        verbose_name = 'Férias'
        verbose_name_plural = 'Férias'


class Frequencia(models.Model):
    servidor = models.ForeignKey(Servidor, verbose_name='Servidor')
    horario = models.DateTimeField('Horário')
    homologado = models.BooleanField('Homologado', default=False)

    class Meta:
        verbose_name = 'Frequência'
        verbose_name_plural = 'Frequências'
