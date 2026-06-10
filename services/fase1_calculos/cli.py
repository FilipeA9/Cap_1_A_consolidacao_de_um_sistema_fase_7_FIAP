"""
FarmTech Solutions - Fase 1 - Menu de terminal.
Mesma experiencia da entrega original (loops, decisao, vetores),
agora consumindo as funcoes puras de calculos.py e com opcao de
persistir os registros no banco unificado.

Execucao: python main.py fase1
"""

from services.fase1_calculos import calculos as c

culturas_data = []  # vetor de dados, como na Fase 1


def entrada_dados():
    print("\nENTRADA DE DADOS:")
    print("1 - Cafe (talhao retangular)")
    print("2 - Cana-de-acucar (pivo circular)")
    opcao = input("Escolha a cultura (1 ou 2): ").strip()

    try:
        if opcao == '1':
            comprimento = float(input("Comprimento do terreno (m): "))
            largura = float(input("Largura do terreno (m): "))
            registro = c.montar_registro('cafe', 'retangulo',
                                         comprimento=comprimento, largura=largura)
        elif opcao == '2':
            raio = float(input("Raio do pivo central (m): "))
            registro = c.montar_registro('cana', 'circulo', raio=raio)
        else:
            print("Opcao invalida!")
            return
    except ValueError as e:
        print(f"Erro: {e}")
        return

    c.adicionar(culturas_data, registro)
    print(f"\nDados adicionados! Area: {registro['area_hectares']:.2f} ha")

    if input("Salvar no banco de dados? (s/N): ").strip().lower() == 's':
        cultura_id = c.persistir_no_banco(registro)
        print(f"Registro gravado na tabela culturas (id={cultura_id}).")


def saida_dados():
    print("\nDADOS CADASTRADOS:")
    if not culturas_data:
        print("Nenhum dado cadastrado.")
        return
    for i, d in enumerate(culturas_data, 1):
        print(f"\n--- Registro {i} ---")
        print(f"Cultura: {d['nome_cultura']} ({d['geometria']})")
        print(f"Area: {d['area_hectares']:.2f} hectares")
        print("Insumos necessarios:")
        for insumo, info in d['insumos'].items():
            print(f"  {insumo.capitalize()}: {info['quantidade']} {info['unidade']}")


def atualizar_dados():
    print("\nATUALIZAR DADOS:")
    if not culturas_data:
        print("Nenhum dado cadastrado para atualizar.")
        return
    saida_dados()
    try:
        pos = int(input("\nNumero do registro a atualizar: ")) - 1
        antigo = culturas_data[pos]
        if antigo['geometria'] == 'retangulo':
            comprimento = float(input("Novo comprimento (m): "))
            largura = float(input("Nova largura (m): "))
            novo = c.montar_registro(antigo['cultura'], 'retangulo',
                                     comprimento=comprimento, largura=largura)
        else:
            raio = float(input("Novo raio (m): "))
            novo = c.montar_registro(antigo['cultura'], 'circulo', raio=raio)
        c.atualizar(culturas_data, pos, novo)
        print(f"Atualizado! Nova area: {novo['area_hectares']:.2f} ha")
    except (ValueError, IndexError) as e:
        print(f"Erro: {e}")


def deletar_dados():
    print("\nDELETAR DADOS:")
    if not culturas_data:
        print("Nenhum dado cadastrado para deletar.")
        return
    saida_dados()
    try:
        pos = int(input("\nNumero do registro a deletar: ")) - 1
        removido = c.deletar(culturas_data, pos)
        print(f"Registro '{removido['nome_cultura']}' removido!")
    except (ValueError, IndexError) as e:
        print(f"Erro: {e}")


def menu_principal():
    while True:
        print("\n" + "=" * 50)
        print("    FARMTECH SOLUTIONS - Fase 1 (Area e Insumos)")
        print("=" * 50)
        print("1 - Entrada de dados")
        print("2 - Visualizar dados")
        print("3 - Atualizar dados")
        print("4 - Deletar dados")
        print("5 - Sair")
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == '1':
            entrada_dados()
        elif opcao == '2':
            saida_dados()
        elif opcao == '3':
            atualizar_dados()
        elif opcao == '4':
            deletar_dados()
        elif opcao == '5':
            print("\nObrigado por usar o FarmTech Solutions!")
            break
        else:
            print("Opcao invalida! Tente novamente.")


if __name__ == "__main__":
    menu_principal()
