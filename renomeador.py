import os
import re
import PyPDF2


def padronizar_nome(nome):

    """
    Limpa e padroniza o nome do paciente para o banco de dados.
    Corrige problemas de espaçamento causados por PDF/OCR.
    """

    # 1. Remove espaços extras
    nome = re.sub(r'\s+', ' ', nome).strip()

    # 2. Remove caracteres inválidos para arquivos
    nome = re.sub(r'[\\/*?:"<>|]', "", nome)

    # 3. Lista de palavras que NÃO devem ser unidas
    preposicoes = {"DA", "DE", "DO", "DAS", "DOS", "E"}

    palavras = nome.split()
    palavras_corrigidas = []

    i = 0
    while i < len(palavras):
        palavra = palavras[i].upper()

        # Se for preposição, mantém normal
        if palavra in preposicoes:
            palavras_corrigidas.append(palavra)
            i += 1
            continue

        # Se for palavra curta (provável erro do PDF)
        if len(palavra) <= 3 and i + 1 < len(palavras):
            proxima = palavras[i + 1].upper()

            # Se a próxima NÃO for preposição, junta
            if proxima not in preposicoes:
                palavra_corrigida = palavra + proxima
                palavras_corrigidas.append(palavra_corrigida)
                i += 2
                continue

        palavras_corrigidas.append(palavra)
        i += 1

    nome_corrigido = " ".join(palavras_corrigidas)

    return nome_corrigido.upper()


def renomear_exames(caminho_pasta):
    arquivos_pdf = [f for f in os.listdir(caminho_pasta) if f.lower().endswith('.pdf')]

    if not arquivos_pdf:
        print("Nenhum PDF encontrado nesta pasta.")
        return

    print(f"\nIniciando a leitura de {len(arquivos_pdf)} arquivos...\n")

    for arquivo_atual in arquivos_pdf:
        caminho_antigo = os.path.join(caminho_pasta, arquivo_atual)

        try:
            with open(caminho_antigo, 'rb') as f:
                leitor = PyPDF2.PdfReader(f)
                if len(leitor.pages) == 0:
                    continue
                texto = leitor.pages[0].extract_text()

            linhas = texto.split('\n')
            nome_bruto = None

            for i, linha in enumerate(linhas):
                if "Paciente" in linha:

                    # CENÁRIO 1: Formato de Tabela
                    if "Cartão Nacional" in linha or "Idade" in linha:
                        if i + 1 < len(linhas):
                            linha_baixo = linhas[i + 1]
                            match_nome = re.search(r"^([A-Za-zÀ-ÿ\s]+)", linha_baixo)
                            if match_nome:
                                nome_bruto = match_nome.group(1).strip()
                        break

                        # CENÁRIO 2: Formato padrão
                    else:
                        match = re.search(r"Paciente[:\-]?\s*(.+)", linha, re.IGNORECASE)
                        if match and match.group(1).strip():
                            nome_bruto = match.group(1).strip()
                        break

            if nome_bruto:
                nome_perfeito = padronizar_nome(nome_bruto)

                novo_nome = f"{nome_perfeito}.pdf"
                caminho_novo = os.path.join(caminho_pasta, novo_nome)

                # Controle de duplicados
                contador = 2
                while os.path.exists(caminho_novo):
                    if caminho_novo == caminho_antigo:
                        break

                    novo_nome = f"{nome_perfeito}({contador}).pdf"
                    caminho_novo = os.path.join(caminho_pasta, novo_nome)
                    contador += 1

                if caminho_novo != caminho_antigo:
                    os.rename(caminho_antigo, caminho_novo)
                    print(f"✅ {arquivo_atual} -> {novo_nome}")
                else:
                    print(f"⏩ {arquivo_atual} já está com o nome correto.")
            else:
                print(f"⚠️ AVISO: Nome do paciente não encontrado em: {arquivo_atual}")

        except Exception as e:
            print(f"❌ Erro ao ler {arquivo_atual}: {e}")

    print("\nProcessamento concluído!")


if __name__ == "__main__":
    print("=== Sistema de Renomeação de Exames ===")
    pasta_alvo = input("Cole o caminho da pasta onde estão os PDFs e aperte ENTER: ")
    pasta_alvo = pasta_alvo.strip('\"\'')

    if os.path.isdir(pasta_alvo):
        renomear_exames(pasta_alvo)
    else:
        print("\n❌ Erro: Caminho da pasta inválido.")

    input("\nPressione ENTER para encerrar...")