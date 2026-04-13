def resolver_mochila(capacidade, pesos, valores):
    n = len(valores)  # Quantidade de itens

    # Criando a matriz DP preenchida com zeros
    # No Java: int[][] dp = new int[n + 1][capacidade + 1];
    dp = [[0 for _ in range(capacidade + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):  # De 1 até n (cada item)
        for w in range(1, capacidade + 1):  # De 1 até capacidade (cada peso)

            peso_do_item_atual = pesos[i - 1]
            valor_do_item_atual = valores[i - 1]

            if peso_do_item_atual <= w:

                # OPÇÃO A: Não pegar o item. O valor é o que estava na célula de cima.
                opcao_nao_pegar = dp[i - 1][w]

                # OPÇÃO B: Pegar o item. Somamos o valor dele + o melhor que cabia
                # com o peso que sobrou (w - peso_do_item_atual).
                opcao_pegar = valor_do_item_atual + dp[i - 1][w - peso_do_item_atual]

                # Escolhemos o maior entre os dois
                dp[i][w] = max(opcao_nao_pegar, opcao_pegar)
            else:
                # O item é pesado demais para a capacidade atual 'w'.
                # Simplesmente repetimos o valor do item anterior.
                dp[i][w] = dp[i - 1][w]

                return dp[n][capacidade]

                # Testando o algoritmo
                valores = [60, 100, 120]
                pesos = [10, 20, 30]
                capacidade_maxima = 50

                resultado = resolver_mochila(capacidade_maxima, pesos, valores)
                print(f"O valor máximo que podemos carregar é: {resultado}")