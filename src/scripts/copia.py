
import os
import shutil

# --- Configuração ---
# O nome da pasta onde os seus mapeamentos estão atualmente.
DIRETORIO_ORIGEM = "mappings_cgra_grammar"

# O nome da nova pasta que será criada para conter apenas os arquivos .dot e .json.
DIRETORIO_DESTINO = "dados_mapeamentos"

def copiar_arquivos_filtrados(origem, destino):
    """
    Copia a estrutura de diretórios de uma pasta de origem para uma de destino,
    mas copia apenas os arquivos com extensão .dot e .json.
    """
    arquivos_copiados = 0
    diretorios_criados = 0

    print(f"Iniciando a cópia de '{origem}' para '{destino}'...")
    print("Filtrando por arquivos .dot e .json...")

    # Verifica se o diretório de origem existe
    if not os.path.isdir(origem):
        print(f"ERRO: O diretório de origem '{origem}' não foi encontrado.")
        print("Certifique-se de que o script está na mesma pasta que 'mappings_cgra_grammar'.")
        return

    # Percorre toda a árvore de diretórios da origem
    for dirpath, _, filenames in os.walk(origem):
        # Cria a estrutura de diretórios correspondente no destino
        # Ex: Se encontra 'origem/111/mesh', cria 'destino/111/mesh'
        caminho_destino = dirpath.replace(origem, destino, 1)
        
        if not os.path.exists(caminho_destino):
            os.makedirs(caminho_destino)
            diretorios_criados += 1

        # Itera sobre todos os arquivos no diretório atual
        for filename in filenames:
            # Verifica se o arquivo termina com .dot ou .json
            if filename.endswith(".dot") or filename.endswith(".json"):
                
                # Monta o caminho completo do arquivo de origem e destino
                arquivo_origem = os.path.join(dirpath, filename)
                arquivo_destino = os.path.join(caminho_destino, filename)
                
                # Copia o arquivo
                shutil.copy2(arquivo_origem, arquivo_destino)
                arquivos_copiados += 1

    print("\n--- Processo Concluído ---")
    print(f"Diretórios criados: {diretorios_criados}")
    print(f"Arquivos (.dot e .json) copiados: {arquivos_copiados}")
    print(f"Os arquivos filtrados estão disponíveis em: '{destino}'")

if __name__ == "__main__":
    copiar_arquivos_filtrados(DIRETORIO_ORIGEM, DIRETORIO_DESTINO)
