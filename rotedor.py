import os
import re
import csv
import shutil
import PyPDF2
from difflib import SequenceMatcher


def limpar_nome(nome):
    """Limpa e padroniza o nome para comparação e salvamento."""
    if not nome: return ""
    nome = re.sub(r'\s+', ' ', str(nome)).strip()
    nome = re.sub(r'\b([A-ZÀ-Ÿa-zà-ÿ])\s([A-ZÀ-Ÿa-zà-ÿ]{2,})\b', r'\1\2', nome)
    nome = re.sub(r'[\\/*?:"<>|]', "", nome)
    return nome.upper()


def extrair_numero_idade(texto):
    """Pega um texto como '38 anos e 10 meses' ou '19 ANO(S)' e devolve só o número."""
    if not texto: return None
    match = re.search(r'\b(\d+)\b', str(texto))
    return match.group(1) if match else None


def carregar_banco_csv(caminho_csv):
    """Lê o CSV tentando várias codificações para evitar erros de acento do Excel."""
    # Lista de codificações (UTF-8 padrão e as usadas pelo Windows no Brasil)
    encodings_para_testar = ['utf-8-sig', 'utf-8', 'cp1252', 'iso-8859-1']

    for codificacao in encodings_para_testar:
        try:
            pacientes = []
            with open(caminho_csv, 'r', encoding=codificacao) as f:
                leitor = csv.DictReader(f, delimiter=';')

                # Se não achar a coluna, o delimitador pode ser vírgula em vez de ponto e vírgula
                if not leitor.fieldnames or 'Nome equipe' not in leitor.fieldnames:
                    f.seek(0)
                    leitor = csv.DictReader(f, delimiter=',')

                for linha in leitor:
                    pacientes.append({
                        'equipe': str(linha.get('Nome equipe', '')).strip(),
                        'nome_oficial': limpar_nome(linha.get('Nome', '')),
                        'idade': extrair_numero_idade(linha.get('Idade', ''))
                    })
            return pacientes  # Se deu certo, retorna a lista e sai da função

        except UnicodeDecodeError:
            continue  # Se der erro de acento, tenta a próxima codificação da lista
        except Exception as e:
            print(f"❌ Erro inexperado ao ler CSV: {e}")
            return []

    print("❌ Erro: Não foi possível ler o arquivo CSV (verifique o formato).")
    return []


def rotear_exames(pasta_exames, caminho_csv):
    banco_pacientes = carregar_banco_csv(caminho_csv)
    if not banco_pacientes:
        print("Banco de dados vazio ou não encontrado. Encerrando.")
        return

    arquivos_pdf = [f for f in os.listdir(pasta_exames) if f.lower().endswith('.pdf')]
    if not arquivos_pdf:
        print("Nenhum arquivo PDF encontrado na pasta informada.")
        return

    print(f"\nIniciando o roteamento de {len(arquivos_pdf)} arquivos...\n")

    pasta_revisao = os.path.join(pasta_exames, "_Revisar_Urgente")
    pasta_nao_encontrado = os.path.join(pasta_exames, "_Nao_Encontrados")
    os.makedirs(pasta_revisao, exist_ok=True)
    os.makedirs(pasta_nao_encontrado, exist_ok=True)

    for arquivo_atual in arquivos_pdf:
        caminho_antigo = os.path.join(pasta_exames, arquivo_atual)
        nome_pdf_bruto = None
        idade_pdf_bruta = None

        try:
            with open(caminho_antigo, 'rb') as f:
                leitor = PyPDF2.PdfReader(f)
                if len(leitor.pages) == 0: continue
                texto = leitor.pages[0].extract_text()

            linhas = texto.split('\n')

            # Buscar nome e idade
            for i, linha in enumerate(linhas):
                if "Paciente" in linha:
                    # Padrão Tabela FUNED
                    if "Cartão Nacional" in linha or "Idade" in linha:
                        if i + 1 < len(linhas):
                            linha_baixo = linhas[i + 1]
                            match_nome = re.search(r"^([A-Za-zÀ-ÿ\s]+)", linha_baixo)
                            if match_nome: nome_pdf_bruto = match_nome.group(1).strip()

                            # Tenta achar a idade na mesma linha (ex: 19 ANO(S))
                            match_idade = re.search(r"(\d+)\s*ANO", linha_baixo, re.IGNORECASE)
                            if match_idade: idade_pdf_bruta = match_idade.group(1)
                        break
                        # Padrão Normal
                    else:
                        match = re.search(r"Paciente[:\-]?\s*(.+)", linha, re.IGNORECASE)
                        if match: nome_pdf_bruto = match.group(1).strip()
                        break

            # Se achou nome, mas não achou idade, tenta procurar solto no texto
            if nome_pdf_bruto and not idade_pdf_bruta:
                match_idade_geral = re.search(r"Idade[:\-]?\s*(\d+)|(\d+)\s*(?:anos|ano|ANO)", texto, re.IGNORECASE)
                if match_idade_geral:
                    idade_pdf_bruta = match_idade_geral.group(1) or match_idade_geral.group(2)

            if not nome_pdf_bruto:
                shutil.move(caminho_antigo, os.path.join(pasta_nao_encontrado, arquivo_atual))
                print(f"⚠️ NOME NÃO LIDO: {arquivo_atual} -> Movido para _Nao_Encontrados")
                continue

            nome_pdf_limpo = limpar_nome(nome_pdf_bruto)
            idade_pdf_limpa = extrair_numero_idade(idade_pdf_bruta)
            resultados_encontrados = []

            for pac in banco_pacientes:
                # TRAVA DE SEGURANÇA: A idade exata tem que bater
                if pac['idade'] == idade_pdf_limpa:
                    similaridade = SequenceMatcher(None, nome_pdf_limpo, pac['nome_oficial']).ratio()
                    # 0.85 significa 85% de semelhança (ignora pequenos erros de digitação)
                    if similaridade >= 0.85:
                        resultados_encontrados.append(pac)

            if len(resultados_encontrados) == 1:
                paciente_confirmado = resultados_encontrados[0]
                equipe = paciente_confirmado['equipe']
                nome_oficial = paciente_confirmado['nome_oficial']

                pasta_equipe = os.path.join(pasta_exames, equipe)
                os.makedirs(pasta_equipe, exist_ok=True)

                novo_nome = f"{nome_oficial}.pdf"
                caminho_novo = os.path.join(pasta_equipe, novo_nome)
                contador = 2

                while os.path.exists(caminho_novo):
                    novo_nome = f"{nome_oficial}({contador}).pdf"
                    caminho_novo = os.path.join(pasta_equipe, novo_nome)
                    contador += 1

                shutil.move(caminho_antigo, caminho_novo)
                print(f"✅ SUCESSO: [{equipe}] Recebeu o paciente {nome_oficial}")

            elif len(resultados_encontrados) > 1:
                shutil.move(caminho_antigo, os.path.join(pasta_revisao, arquivo_atual))
                print(f"🚨 CONFLITO (Homônimos): {nome_pdf_limpo} -> Movido para _Revisar_Urgente")

            else:
                shutil.move(caminho_antigo, os.path.join(pasta_nao_encontrado, arquivo_atual))
                print(f"❌ NÃO ENCONTRADO NO BANCO: {nome_pdf_limpo} -> Movido para _Nao_Encontrados")

        except Exception as e:
            print(f"❌ Erro ao processar {arquivo_atual}: {e}")

    print("\n🏁 Processamento e Roteamento Concluídos!")


if __name__ == "__main__":
    print("=== ROTEADOR AUTOMÁTICO DE EXAMES ===")

    csv_alvo = input("1. Cole o caminho do arquivo CSV do banco de dados: ").strip('\"\'')
    if not os.path.isfile(csv_alvo):
        print("❌ Erro: Arquivo CSV não encontrado.")
        exit()

    pasta_alvo = input("2. Cole o caminho da PASTA com os PDFs: ").strip('\"\'')
    if os.path.isdir(pasta_alvo):
        rotear_exames(pasta_alvo, csv_alvo)
    else:
        print("❌ Erro: Caminho da pasta de PDFs inválido.")

    input("\nPressione ENTER para encerrar...")