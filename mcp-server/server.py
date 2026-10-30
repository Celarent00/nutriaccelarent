import os
import re
from pathlib import Path
# API V2
from mcp.server import MCPServer


# Define a pasta principal do projeto.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Pastas que não queremos incluir na listagem.
IGNORED_DIRECTORIES = {".git", "node_modules", ".venv"}


# Cria o servidor MCP.
mcp = MCPServer("DevPilot MCP")


@mcp.tool()
def list_files(directory: str = ".") -> list[str]:
    """Lista recursivamente arquivos e pastas dentro do projeto autorizado."""

    target = (PROJECT_ROOT / directory).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists():
        raise ValueError("A pasta informada não existe.")

    if not target.is_dir():
        raise ValueError("O caminho informado não é uma pasta.")

    entries = []

    for current_root, directories, files in os.walk(target):

        # Remove diretórios que não queremos percorrer.
        directories[:] = sorted(
            d for d in directories
            if d not in IGNORED_DIRECTORIES
        )

        current_path = Path(current_root)

        # Registra as subpastas.
        for directory_name in directories:
            folder = current_path / directory_name
            relative_path = folder.relative_to(PROJECT_ROOT)
            entries.append(relative_path.as_posix() + "/")

        # Registra os arquivos.
        for file_name in sorted(files):
            file = current_path / file_name
            relative_path = file.relative_to(PROJECT_ROOT)
            entries.append(relative_path.as_posix())

    return sorted(entries)

@mcp.tool()
def read_file(file_path: str) -> str:
    """Lê o conteúdo de um arquivo dentro do projeto autorizado."""

    target = (PROJECT_ROOT / file_path).resolve()

    # Impede o acesso a arquivos fora da pasta do projeto.
    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists():
        raise ValueError("O arquivo informado não existe.")

    if not target.is_file():
        raise ValueError("O caminho informado não é um arquivo.")

    # Evita ler arquivos muito grandes de uma só vez.
    max_size = 1_000_000

    if target.stat().st_size > max_size:
        raise ValueError(
            "Arquivo muito grande para leitura integral (limite: 1 MB)."
        )

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            "Não foi possível ler o arquivo como texto UTF-8."
        )

@mcp.tool()
def search_files(query: str, directory: str = ".") -> list[str]:
    """Pesquisa um texto dentro dos arquivos do projeto."""

    if not query.strip():
        raise ValueError("A pesquisa não pode estar vazia.")

    target = (PROJECT_ROOT / directory).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists() or not target.is_dir():
        raise ValueError("A pasta informada não existe ou não é válida.")

    ignored_files = {
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
    }

    ignored_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".ico", ".pdf", ".zip", ".exe", ".dll",
        ".pyc", ".db", ".sqlite", ".fdb",
        ".mp4", ".mp3", ".wav",
    }

    max_file_size = 1_000_000
    max_results = 100
    results = []

    search_term = query.casefold()

    for current_root, directories, files in os.walk(target):

        directories[:] = [
            d for d in directories
            if d not in IGNORED_DIRECTORIES
        ]

        for file_name in files:

            if file_name.lower() in ignored_files:
                continue

            file_path = Path(current_root) / file_name

            if file_path.suffix.lower() in ignored_extensions:
                continue

            try:
                resolved_file = file_path.resolve()

                if not resolved_file.is_relative_to(PROJECT_ROOT):
                    continue

                if resolved_file.stat().st_size > max_file_size:
                    continue

                with resolved_file.open(
                    "r",
                    encoding="utf-8",
                    errors="replace"
                ) as file:

                    for line_number, line in enumerate(file, start=1):

                        if search_term in line.casefold():

                            relative_path = resolved_file.relative_to(
                                PROJECT_ROOT
                            )

                            result = (
                                f"{relative_path.as_posix()}:"
                                f"{line_number}: "
                                f"{line.strip()[:500]}"
                            )

                            results.append(result)

                            if len(results) >= max_results:
                                return results

            except (OSError, ValueError):
                continue

    return results

@mcp.tool()
def write_file(
    file_path: str,
    content: str,
    overwrite: bool = False
) -> str:
    """Cria ou atualiza um arquivo dentro do projeto autorizado."""

    target = (PROJECT_ROOT / file_path).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if target.exists() and not target.is_file():
        raise ValueError("O caminho informado não é um arquivo.")

    if target.exists() and not overwrite:
        raise ValueError(
            "O arquivo já existe. Use overwrite=True para substituí-lo."
        )

    max_size = 1_000_000

    if len(content.encode("utf-8")) > max_size:
        raise ValueError(
            "Conteúdo muito grande (limite: 1 MB)."
        )

    if not target.parent.exists():
        raise ValueError(
            "A pasta de destino não existe. Crie-a primeiro."
        )

    target.write_text(content, encoding="utf-8")

    return f"Arquivo salvo com sucesso: {target.relative_to(PROJECT_ROOT).as_posix()}"


@mcp.tool()
def create_directory(directory_path: str) -> str:
    """Cria uma pasta dentro do projeto autorizado."""

    target = (PROJECT_ROOT / directory_path).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if target.exists():
        if target.is_dir():
            return "A pasta já existe."

        raise ValueError("Já existe um arquivo com esse nome.")

    target.mkdir(parents=True)

    return (
        "Pasta criada com sucesso: "
        f"{target.relative_to(PROJECT_ROOT).as_posix()}"
    )


@mcp.tool()
def delete_file(file_path: str, confirm: bool = False) -> str:
    """Exclui um arquivo do projeto após confirmação explícita."""

    target = (PROJECT_ROOT / file_path).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists():
        raise ValueError("O arquivo informado não existe.")

    if not target.is_file():
        raise ValueError("O caminho informado não é um arquivo.")

    if not confirm:
        raise ValueError(
            "Exclusão não autorizada. Use confirm=True para confirmar."
        )

    target.unlink()

    return (
        "Arquivo excluído com sucesso: "
        f"{target.relative_to(PROJECT_ROOT).as_posix()}"
    )


@mcp.tool()
def get_file_outline(file_path: str) -> list[str]:
    """Identifica imports, funções, classes, componentes e exportações."""

    target = (PROJECT_ROOT / file_path).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists():
        raise ValueError("O arquivo informado não existe.")

    if not target.is_file():
        raise ValueError("O caminho informado não é um arquivo.")

    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

    if target.suffix.lower() not in supported_extensions:
        raise ValueError(
            "Formato não suportado. Use arquivos JS, JSX, TS ou TSX."
        )

    if target.stat().st_size > 1_000_000:
        raise ValueError("Arquivo muito grande (limite: 1 MB).")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError("Não foi possível ler o arquivo como UTF-8.")

    outline = []

    patterns = [
        (
            "Import",
            re.compile(r"^\s*import\s+.*", re.MULTILINE)
        ),
        (
            "Função",
            re.compile(
                r"^\s*(?:export\s+)?(?:default\s+)?"
                r"(?:async\s+)?function\s+(\w+)",
                re.MULTILINE
            )
        ),
        (
            "Classe",
            re.compile(
                r"^\s*(?:export\s+)?(?:default\s+)?"
                r"class\s+(\w+)",
                re.MULTILINE
            )
        ),
        (
            "Componente ou função",
            re.compile(
                r"^\s*(?:export\s+)?(?:default\s+)?"
                r"(?:const|let)\s+(\w+)\s*=\s*"
                r"(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>",
                re.MULTILINE
            )
        ),
    ]

    for label, pattern in patterns:
        for match in pattern.finditer(content):
            line_number = content.count("\n", 0, match.start()) + 1

            if label == "Import":
                description = match.group(0).strip()
            else:
                name = match.group(1)

                if label == "Componente ou função":
                    if name[0].isupper():
                        description = f"Componente: {name}"
                    else:
                        description = f"Função: {name}"
                else:
                    description = f"{label}: {name}"

            outline.append((line_number, description))

    for line_number, line in enumerate(content.splitlines(), start=1):
        if re.match(r"^\s*export\s+default\b", line):
            outline.append((line_number, "Exportação default"))

    outline.sort(key=lambda item: item[0])

    if not outline:
        return ["Nenhuma estrutura reconhecida neste arquivo."]

    return [
        f"Linha {line_number}: {description}"
        for line_number, description in outline
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")