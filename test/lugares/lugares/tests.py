from datetime import date
from sloth.test import ServerTestCase
from .models import Pais, Estado, Cidade, Pessoa

class TestCase(ServerTestCase):

    def setUp(self):
        pais = Pais.objects.create(nome='Brasil')
        estado = Estado.objects.create(nome='Rio Grande do Norte', pais=pais)
        cidade = Cidade.objects.create(nome='Natal', estado=estado)
        Pessoa.objects.create(nome='João', cidade=cidade, data_nascimento=date.today(), sexo='M')
        Pessoa.objects.create(nome='Maria', cidade=cidade, data_nascimento=date.today(), sexo='F')

    def test(self):
        self.create_user('admin', '123', True)
        self.login('admin', '123')
        response = self.get('/meta/lugares/pais/')
        self.assertEquals(response['type'], 'queryset')
        self.assertEquals(response['name'], 'Países')
        response = self.get('/meta/lugares/pais/1/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Brasil')
        self.assertEquals(response['data']['get_dados_gerais']['type'], 'fieldset')
        self.assertEquals(response['data']['get_dados_gerais']['path'], '/meta/lugares/pais/1/get_dados_gerais/')
        self.assertEquals(response['data']['get_estados']['type'], 'queryset')
        self.assertEquals(response['data']['get_estados']['path'], '/meta/lugares/pais/1/get_estados/')
        response = self.get('/meta/lugares/pais/1/get_dados_gerais/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Brasil')
        self.assertEquals(response['data']['get_dados_gerais']['type'], 'fieldset')
        self.assertEquals(response['data']['get_dados_gerais']['path'], '/meta/lugares/pais/1/get_dados_gerais/')
        response = self.get('/meta/lugares/pais/1/get_estados/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Brasil')
        self.assertEquals(response['data']['get_estados']['type'], 'queryset')
        self.assertEquals(response['data']['get_estados']['path'], '/meta/lugares/pais/1/get_estados/')
        response = self.get('/meta/lugares/pais/1/get_estados/1/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Rio Grande do Norte')
        self.assertEquals(response['data']['get_dados_gerais']['type'], 'fieldset')
        self.assertEquals(response['data']['get_dados_gerais']['path'], '/meta/lugares/pais/1/get_estados/1/get_dados_gerais/')
        self.assertEquals(response['data']['get_cidades']['type'], 'queryset')
        response = self.get('/meta/lugares/pais/1/get_estados/1/get_dados_gerais/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Rio Grande do Norte')
        self.assertEquals(response['data']['get_dados_gerais']['type'], 'fieldset')
        self.assertEquals(response['data']['get_dados_gerais']['path'], '/meta/lugares/pais/1/get_estados/1/get_dados_gerais/')
        response = self.get('/meta/lugares/pais/1/get_estados/1/get_cidades/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Rio Grande do Norte')
        self.assertEquals(response['data']['get_cidades']['type'], 'queryset')
        self.assertEquals(response['data']['get_cidades']['path'], '/meta/lugares/pais/1/get_estados/1/get_cidades/')
        response = self.get('/meta/lugares/pais/1/get_estados/1/get_cidades/1/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Natal')
        self.assertEquals(response['data']['get_habitantes']['type'], 'fieldset-list')
        self.assertEquals(response['data']['get_habitantes']['path'], '/meta/lugares/pais/1/get_estados/1/get_cidades/1/get_habitantes/')
        self.assertEquals(response['data']['get_habitantes']['data']['get_homens']['type'], 'queryset')
        self.assertEquals(response['data']['get_habitantes']['data']['get_homens']['path'], '/meta/lugares/pais/1/get_estados/1/get_cidades/1/get_habitantes/get_homens/')
        self.assertEquals(response['append']['get_total_pessoas_por_sexo']['type'], 'statistics')
        self.assertEquals(response['append']['get_total_pessoas_por_sexo']['path'], '/meta/lugares/pais/1/get_estados/1/get_cidades/1/get_total_pessoas_por_sexo/')
        self.assertEquals(response['append']['get_total_pessoas_por_sexo']['template'], 'app/charts/donut.html')
        self.assertEquals(response['append']['get_total_pessoas_casadas']['type'], 'statistics')
        self.assertEquals(response['append']['get_total_pessoas_casadas']['path'], '/meta/lugares/pais/1/get_estados/1/get_cidades/1/get_total_pessoas_casadas/')
        self.assertEquals(response['append']['get_total_pessoas_casadas']['template'], 'app/charts/column.html')
        self.assertEquals(response['attach'][0]['name'], 'Estatisticas')
        response = self.get('/meta/lugares/pessoa/')
        self.assertEquals(response['type'], 'object')
        self.assertEquals(response['name'], 'Pessoas')
        self.assertEquals(response['data']['homens']['type'], 'queryset')
        self.assertEquals(response['data']['homens']['path'], '/meta/lugares/pessoa/homens/')
        self.assertEquals(response['data']['mulheres']['type'], 'queryset')
        self.assertEquals(response['data']['mulheres']['path'], '/meta/lugares/pessoa/mulheres/')
        self.assertEquals(response['append']['get_total_por_sexo']['type'], 'statistics')
        self.assertEquals(response['append']['get_total_por_sexo']['path'], '/meta/lugares/pessoa/get_total_por_sexo/')
        self.assertEquals(response['append']['get_total_casadas']['type'], 'statistics')
        self.assertEquals(response['append']['get_total_casadas']['path'], '/meta/lugares/pessoa/get_total_casadas/')
        self.assertEquals(response['attach'][0]['name'], 'Total por Sexo Casado')
        self.assertEquals(response['attach'][0]['path'], '/meta/lugares/pessoa/get_total_por_sexo_casado/')