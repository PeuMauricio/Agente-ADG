import os
import zipfile
from pathlib import Path


class GerenciadorDeArquivos:
    """
    Classe de utilidades focada em operações de manipulação de arquivos,
    como a descompactação de pacotes ZIP.
    """

    @staticmethod
    def extrair_zip(caminho_do_zip: str, pasta_destino: str = None) -> Path:
        """
        Realiza a extração de um arquivo compactado no formato .zip para um
        diretório de destino. Se nenhum destino for fornecido, a extração
        ocorrerá em uma nova pasta com o mesmo nome do arquivo ZIP.

        Args:
            caminho_do_zip (str): O caminho completo para o arquivo .zip a ser extraído.
            pasta_destino (str, optional): O diretório onde o conteúdo será extraído.
                                           Se omitido, um diretório padrão é criado.

        Returns:
            Path: O objeto Path apontando para o diretório de destino com os arquivos extraídos.

        Raises:
            FileNotFoundError: Lançado se o arquivo ZIP não for encontrado ou for inválido.
        """
        caminho_zip_obj = Path(caminho_do_zip)

        if not caminho_zip_obj.is_file() or not zipfile.is_zipfile(caminho_zip_obj):
            raise FileNotFoundError(
                f"O arquivo ZIP especificado é inválido ou não foi encontrado em: {caminho_zip_obj}"
            )

        # Define o diretório de destino
        if pasta_destino:
            diretorio_final = Path(pasta_destino)
        else:
            diretorio_final = caminho_zip_obj.parent / caminho_zip_obj.stem
        
        # Garante que o diretório de destino exista
        diretorio_final.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(caminho_zip_obj, "r") as zip_ref:
            zip_ref.extractall(diretorio_final)
            print(f"📦 Arquivo ZIP extraído com sucesso para o diretório: {diretorio_final.resolve()}")

        return diretorio_final

    @staticmethod
    def descompactar_zip_condicionalmente(diretorio_alvo: str, caminho_do_zip: str) -> Path:
        """
        Gerencia a descompactação de um arquivo ZIP de forma inteligente,
        extraindo-o apenas se o diretório de destino estiver vazio.
        Isso evita reprocessamento desnecessário.

        Args:
            diretorio_alvo (str): O caminho do diretório que deve receber os arquivos.
            caminho_do_zip (str): O caminho completo para o arquivo .zip.

        Returns:
            Path: O objeto Path para o diretório de destino.
        """
        pasta_obj = Path(diretorio_alvo)

        if not pasta_obj.exists():
            print(f"INFO: O diretório de destino não existe. Criando em: {pasta_obj}")
            pasta_obj.mkdir(parents=True)

        # Verifica se o diretório já tem algum conteúdo
        if any(pasta_obj.iterdir()):
            print(
                f"INFO: O diretório '{pasta_obj}' já possui conteúdo. A extração será ignorada."
            )
            return pasta_obj
        else:
            print(f"AÇÃO: O diretório '{pasta_obj}' está vazio. Iniciando o processo de extração...")
            try:
                return GerenciadorDeArquivos.extrair_zip(caminho_do_zip, diretorio_alvo)
            except Exception as e:
                print(f"ERRO CRÍTICO: A descompactação falhou. Motivo: {e}")
                raise