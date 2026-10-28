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
    """Lista arquivos e pastas dentro do projeto autorizado."""

    target = (PROJECT_ROOT / directory).resolve()

    # Impede o acesso a caminhos fora da pasta do projeto.
    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError("Acesso negado: caminho fora do projeto.")

    if not target.exists():
        raise ValueError("A pasta informada não existe.")

    if not target.is_dir():
        raise ValueError("O caminho informado não é uma pasta.")

    entries = []

    for item in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        if item.is_dir() and item.name in IGNORED_DIRECTORIES:
            continue

        name = item.name + "/" if item.is_dir() else item.name
        entries.append(name)

    return entries


if __name__ == "__main__":
    mcp.run(transport="stdio")