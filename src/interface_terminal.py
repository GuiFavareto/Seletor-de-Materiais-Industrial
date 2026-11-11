from src.filtro_service import FiltroMaterialService

def solicitar_dados_usuario():
    print("=" * 60)
    print(" SISTEMA ESPECIALISTA DE SELEÇÃO DE MATERIAIS ")
    print("=" * 60)

    aplicacao = input("1. Qual é a aplicação principal? (Ex: tubulação, eixo, engrenagem): ")
    
    try:
        temperatura = float(input("2. Qual a temperatura de trabalho em °C? (Ex: 90): "))
    except ValueError:
        print("Valor inválido. Assumindo temperatura ambiente (25 °C).")
        temperatura = 25.0

    quimico_input = input("3. Haverá contato com fluidos químicos agressivos? (s/n): ").strip().lower()
    contato_quimico = True if quimico_input == 's' else False

    esforco_input = input("4. O nível de esforço mecânico/estrutural é alto? (s/n): ").strip().lower()
    esforco_mecanico = 'alto' if esforco_input == 's' else 'baixo'

    return {
        "aplicacao": aplicacao,
        "temperatura_C": temperatura,
        "contato_quimico": contato_quimico,
        "esforco_mecanico": esforco_mecanico
    }

def iniciar_sistema():
    # Instancia o serviço que carrega o JSON
    servico = FiltroMaterialService()
    
    # Coleta as condições
    condicoes = solicitar_dados_usuario()
    
    print("\n[+] Analisando banco de dados...\n")
    resultados = servico.selecionar(condicoes)

    print("=" * 60)
    print(" RESULTADO DA SELEÇÃO DE MATERIAIS ")
    print("=" * 60)

    if not resultados:
        print("Nenhum material no banco de dados atendeu aos requisitos com pontuação viável.")
        return

    for i, res in enumerate(resultados, 1):
        print(f"\n{i}º OPÇÃO: {res['material']} ({res['categoria']}) | PONTUAÇÃO: {res['pontuacao']}")
        
        print("   [+] Por que usar:")
        for motivo in res['justificativas']:
            print(f"       - {motivo}")
            
        print("   [!] Limitações e Cuidados:")
        for limitacao in res['limitacoes']:
            print(f"       - {limitacao}")
            
    print("\n" + "=" * 60)