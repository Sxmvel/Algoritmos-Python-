import random
from collections import Counter
import matplotlib.pyplot as plt


def simular_e_plotar():
    numero_lancamentos = 1_000_000


    lancamentos = random.choices(range(1, 7), k=numero_lancamentos)
    frequencias = Counter(lancamentos)

    # Prepara os dados para o eixo X (faces) e eixo Y (contagens)
    faces = list(range(1, 7))
    contagens = [frequencias[face] for face in faces]

    # 2. Cria o gráfico de barras
    plt.bar(faces, contagens, color='skyblue', edgecolor='black')

    # 3. Adiciona títulos e rótulos
    plt.title(f'Frequência das Faces em {numero_lancamentos} Lançamentos')
    plt.xlabel('Face do Dado')
    plt.ylabel('Frequência')
    plt.xticks(faces)  # Garante que apenas os números 1 a 6 apareçam no eixo X

    # 4. Adiciona o valor exato acima de cada barra para facilitar a leitura
    for i, v in enumerate(contagens):
        plt.text(faces[i], v + 1500, str(v), ha='center', va='bottom')

    # Dá um pequeno espaço extra no topo do gráfico para os números não cortarem
    plt.ylim(0, max(contagens) + 15000)

    # Ajusta o layout e salva o gráfico
    plt.tight_layout()
    plt.show()
    print("Gráfico gerado com sucesso!")


# Executa a função
simular_e_plotar()