import json
import os
import re


class FiltroMaterialService:
    def __init__(self, json_path=None):
        if json_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, 'data', 'materiais.json')

        with open(json_path, 'r', encoding='utf-8') as f:
            self.materiais = json.load(f)['materiais']

    def _extrair_numero(self, val):
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", val.replace(',', '.'))]
            if nums:
                return sum(nums) / len(nums)
        return None

    def _obter_limite_temperatura(self, mat):
        mat_id = mat.get("id", "").upper()
        
        limites_conhecidos = {
            "PVC-U": 60,
            "CPVC": 90,
            "PEAD": 80,
            "PP": 100,
            "POM": 100,
            "PA": 120,
            "UHMWPE": 80,
            "PC-POLICARBONATO": 120,
            "PTFE": 260,
            "PEEK": 250,
            "COMPOSITO-CARBONO-EPOXI": 180,
            "SAE-660": 220,
            "AL-6061-T6": 150,
            "AL-7075-T6": 120,
        }
        
        if mat_id in limites_conhecidos:
            return limites_conhecidos[mat_id]
        
        if mat.get("categoria") == "Metal":
            return 400
        
        prop = mat.get("propriedades_tecnicas", {})
        temp = self._extrair_numero(prop.get("temperatura_vicat_C") or prop.get("temperatura_fusao_C"))
        if temp:
            return temp - 15
            
        return 100

    def selecionar(self, condicoes):
        temp_req = condicoes.get('temperatura_C', 25)
        kw = condicoes.get('aplicacao', '').lower().strip()
        quimico_req = condicoes.get('contato_quimico', False)
        esforco = condicoes.get('esforco_mecanico', 'moderado').lower()

        resultados = []

        for m in self.materiais:
            pontuacao = 50  # Pontuação base
            justificativas = []
            limitacoes = list(m.get("limitacoes_cuidados", []))
            detalhamento = []

            # 1. TEMPERATURA DE OPERAÇÃO
            temp_max = self._obter_limite_temperatura(m)
            if temp_req > temp_max:
                continue
            else:
                pontuacao += 20
                justificativas.append(f"Suporta a temperatura de trabalho ({temp_req} °C <= máx {temp_max} °C).")
                detalhamento.append({"Critério": "Temperatura", "Pontos": "+20", "Observação": f"Compatível (Máx: {temp_max} °C)"})

            # 2. ESFORÇO MECÂNICO & TRATAMENTO DE CREEP/FLUÊNCIA
            prop = m.get("propriedades_tecnicas", {})
            tracao = self._extrair_numero(prop.get("resistencia_tracao_MPa") or prop.get("limite_escoamento_MPa"))
            
            if tracao is None and m["id"] == "SAE-4140":
                tracao = 1000.0

            if esforco == "alto":
                if tracao is not None:
                    if tracao >= 800:
                        pontuacao += 50
                        justificativas.append(f"Altíssima resistência mecânica ({tracao:.0f} MPa), excelente para cargas severas.")
                        detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "+50", "Observação": f"Excelente ({tracao:.0f} MPa)"})
                    elif tracao >= 400:
                        pontuacao += 30
                        justificativas.append(f"Boa resistência mecânica ({tracao:.0f} MPa) para cargas elevadas.")
                        detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "+30", "Observação": f"Adequado ({tracao:.0f} MPa)"})
                    elif tracao >= 80:
                        pontuacao += 10
                        justificativas.append(f"Resistência moderada ({tracao:.0f} MPa); atende a esforços controlados.")
                        detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "+10", "Observação": f"Moderado ({tracao:.0f} MPa)"})
                    else:  # Baixa resistência mecânica (ex: PTFE ~28 MPa, UHMWPE, PEAD)
                        pontuacao -= 40
                        limitacoes.append(f"ALERTA: Baixa resistência à tração ({tracao:.0f} MPa) e alta tendência à fluência (creep) sob esforço mecânico elevado.")
                        detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "-40", "Observação": f"Crítico ({tracao:.0f} MPa - risco de deformação)"})
                else:
                    pontuacao += 10
            elif esforco == "moderado":
                if tracao and tracao >= 300:
                    pontuacao += 20
                    justificativas.append("Resistência mecânica adequada ao uso geral.")
                    detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "+20", "Observação": "Adequado"})
            else:  # baixo
                pontuacao += 15
                justificativas.append("Atende perfeitamente a baixas solicitações mecânicas.")
                detalhamento.append({"Critério": "Esforço Mecânico", "Pontos": "+15", "Observação": "Carga leve"})

            # 3. RESISTÊNCIA QUÍMICA
            if quimico_req:
                m_id = m["id"]
                comp_quim = str(prop.get("comportamento_quimico", "")).lower()
                carac_str = " ".join(m.get("caracteristicas_relevantes", [])).lower()
                
                if m_id in ["PTFE", "PEEK", "AISI-316L", "TI-6AL-4V", "COMPOSITO-CARBONO-EPOXI"]:
                    pontuacao += 40
                    justificativas.append("Excepcional resistência e inércia química.")
                    detalhamento.append({"Critério": "Resistência Química", "Pontos": "+40", "Observação": "Inerte / Alta resistência"})
                elif "boa" in comp_quim or "excelente" in comp_quim or "química" in carac_str or m_id in ["AISI-304", "CPVC", "PP", "PEAD", "POM"]:
                    pontuacao += 25
                    justificativas.append("Boa compatibilidade química com fluidos e reagentes industriais.")
                    detalhamento.append({"Critério": "Resistência Química", "Pontos": "+25", "Observação": "Boa resistência"})
                else:
                    pontuacao -= 15
                    limitacoes.append("Resistência química limitada para meios agressivos.")
                    detalhamento.append({"Critério": "Resistência Química", "Pontos": "-15", "Observação": "Não recomendado para meio corrosivo"})

            # 4. PALAVRA-CHAVE DE APLICAÇÃO
            if kw:
                aplicacoes = " ".join(m.get("aplicacoes_tipicas", [])).lower()
                nome_tipo = (m["nome"] + " " + m["tipo"]).lower()
                if kw in aplicacoes or kw in nome_tipo:
                    pontuacao += 30
                    justificativas.append(f"Material com uso consolidado na aplicação '{kw}'.")
                    detalhamento.append({"Critério": "Palavra-chave", "Pontos": "+30", "Observação": f"Compatível com '{kw}'"})

            resultados.append({
                "id": m["id"],
                "material": m["nome"],
                "categoria": m["categoria"],
                "pontuacao": pontuacao,
                "justificativas": justificativas,
                "limitacoes": limitacoes,
                "detalhamento": detalhamento
            })

        resultados.sort(key=lambda x: x["pontuacao"], reverse=True)
        return resultados