import json
import os

class FiltroMaterialService:
    def __init__(self):
        # Localiza o arquivo json automaticamente a partir da pasta src/
        base_dir = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(base_dir, 'data', 'materiais.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            self.materiais = dados['materiais']

    def selecionar(self, condicoes_usuario):
        resultados = []

        temp_req = condicoes_usuario.get('temperatura_C', 25)
        app_req = condicoes_usuario.get('aplicacao', '').lower()
        quimico_req = condicoes_usuario.get('contato_quimico')
        esforco_req = condicoes_usuario.get('esforco_mecanico')

        for mat in self.materiais:
            pontuacao = 0
            motivos = []
            viavel = True
            mat_id = mat['id']
            categoria = mat['categoria']

            # 1. FILTRO DE TEMPERATURA (Eliminações específicas por material)
            if temp_req > 80 and mat_id == "PVC-U": viavel = False
            if temp_req > 100 and mat_id in ["PEAD", "POM"]: viavel = False
            if temp_req > 115 and mat_id == "CPVC": viavel = False
            if temp_req > 130 and categoria == "Polímero" and mat_id != "PTFE": viavel = False
            
            if not viavel:
                continue # Pula para o próximo material se não suportar a temperatura

            # 2. FILTRO DE APLICAÇÃO (Match de palavra-chave)
            if app_req:
                match_aplicacao = any(app_req in app.lower() for app in mat.get('aplicacoes_tipicas', []))
                if match_aplicacao:
                    pontuacao += 30
                    motivos.append(f"Possui histórico comprovado na fabricação de '{app_req}'.")

            # 3. FILTRO DE RESISTÊNCIA QUÍMICA (Ranking de especialidade)
            if quimico_req:
                if mat_id == "PTFE":
                    pontuacao += 60
                    motivos.append("Excepcional: Resistência química universal para ambientes agressivos.")
                elif mat_id in ["PP", "PVC-U", "CPVC", "PEAD"]:
                    pontuacao += 40
                    motivos.append(f"Excelente comportamento químico frente a fluidos industriais típico do {mat_id}.")
                elif categoria == "Polímero":
                    pontuacao += 15
                    motivos.append("Resistência química moderada (exige verificação de compatibilidade com o fluido).")
                else:
                    pontuacao -= 30
                    motivos.append(f"Atenção: Por ser aço ({mat['tipo']}), exigirá revestimento ou proteção contra corrosão severa.")

            # 4. FILTRO DE ESFORÇO MECÂNICO (Ranking por limite de resistência)
            if esforco_req == "alto":
                if mat_id in ["SAE-4340", "SAE-4140"]:
                    pontuacao += 70
                    motivos.append("Aço ligado de altíssima resistência e tenacidade, ideal para cargas severas e fadiga.")
                elif mat_id in ["SAE-1045", "SAE-8620"]:
                    pontuacao += 45
                    motivos.append("Boa resistência mecânica; permite tratamentos térmicos para endurecimento superficial.")
                elif mat_id == "SAE-1020":
                    pontuacao += 20
                    motivos.append("Suporta esforço estrutural básico, porém possui menor limite de escoamento que os aços ligados.")
                elif mat_id in ["POM", "PA"]:
                    pontuacao -= 10
                    motivos.append("Apesar de ser plástico de engenharia rígido, perde desempenho mecânico comparado a metais sob carga extrema.")
                else:
                    pontuacao -= 40
                    motivos.append("Alto risco de deformação (fluência) estrutural caso submetido a altas cargas mecânicas.")

            # 5. PERSONALIZAÇÃO DE DESEMPATE E IDENTIDADE DO MATERIAL
            # Puxa uma característica técnica real do JSON para criar textos únicos e desempatar notas
            if mat.get('caracteristicas_relevantes'):
                # Usamos o tamanho do nome ou a densidade de forma oculta para gerar um micro-desempate seguro (1 a 5 pontos)
                pontos_desempate = len(mat_id) % 5 + 1 
                pontuacao += pontos_desempate
                
                # Extrai a primeira característica da lista do JSON
                caracteristica_chave = mat['caracteristicas_relevantes'][0]
                motivos.append(f"Destaque do material: {caracteristica_chave}.")

            # 6. SALVAR RESULTADOS POSITIVOS
            if pontuacao > 0:
                resultados.append({
                    "material": mat['nome'],
                    "categoria": categoria,
                    "pontuacao": pontuacao,
                    "justificativas": motivos,
                    "limitacoes": mat.get('limitacoes_cuidados', [])
                })

        # Ordenar do maior para o menor
        resultados.sort(key=lambda x: x['pontuacao'], reverse=True)
        return resultados