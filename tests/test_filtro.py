import sys
import os

# Adiciona a pasta raiz do projeto ao caminho do Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.filtro_service import FiltroMaterialService
pytest
@pytest.fixture
def service():
    return FiltroMaterialService()

def test_filtro_temperatura_pvc(service):
    """Garante que o PVC-U é eliminado em temperaturas acima de 80°C"""
    condicoes = {'temperatura_C': 90, 'aplicacao': '', 'contato_quimico': False, 'esforco_mecanico': 'baixo'}
    resultados = service.selecionar(condicoes)
    materiais_recomendados = [r['material'] for r in resultados]
    
    assert "PVC-U" not in materiais_recomendados

def test_esforco_alto_prioriza_acos_ligados(service):
    """Garante que para esforço ALTO, o SAE-4340 pontua mais que o SAE-1020"""
    condicoes = {'temperatura_C': 25, 'aplicacao': '', 'contato_quimico': False, 'esforco_mecanico': 'alto'}
    resultados = service.selecionar(condicoes)
    
    pontuacao_4340 = next(r['pontuacao'] for r in resultados if "4340" in r['material'])
    pontuacao_1020 = next(r['pontuacao'] for r in resultados if "1020" in r['material'])
    
    assert pontuacao_4340 > pontuacao_1020

def test_resistencia_quimica_prioriza_ptfe(service):
    """Garante que exigência química coloca o PTFE no topo entre polímeros"""
    condicoes = {'temperatura_C': 25, 'aplicacao': '', 'contato_quimico': True, 'esforco_mecanico': 'baixo'}
    resultados = service.selecionar(condicoes)
    
    primeiro_colocado = resultados[0]['material']
    assert "PTFE" in primeiro_colocado