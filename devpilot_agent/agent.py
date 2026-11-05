
import os
from pathlib import Path

from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)

from mcp import StdioServerParameters


# Localiza a raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Carrega as variáveis do arquivo .env
load_dotenv(PROJECT_ROOT / ".env")

# Caminhos do servidor MCP e do Python do ambiente virtual
MCP_SERVER_SCRIPT = PROJECT_ROOT / "mcp-server" / "server.py"

PYTHON_EXECUTABLE = (
    PROJECT_ROOT
    / "mcp-server"
    / ".venv"
    / "Scripts"
    / "python.exe"
)

# Verifica se a chave da API está configurada
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env")

# Verifica se os arquivos necessários existem
if not MCP_SERVER_SCRIPT.is_file():
    raise FileNotFoundError("server.py não encontrado.")

if not PYTHON_EXECUTABLE.is_file():
    raise FileNotFoundError("Python do ambiente virtual não encontrado.")


# Conecta o agente ao servidor MCP local
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=str(PYTHON_EXECUTABLE),
            args=[str(MCP_SERVER_SCRIPT)],
        )
    )
)


# Define o agente principal
root_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="gwen",
    description="Gwen, sua assistente pessoal de programação.",
    instruction="""
    Você é a Gwen, uma assistente especializada em desenvolvimento
    de software.

    Você possui ferramentas MCP para explorar, ler, pesquisar e modificar
    os arquivos do projeto.

    Regras de comportamento:

    1. Analise o pedido antes de escolher as ferramentas.
    2. Utilize as ferramentas disponíveis sempre que necessário.
    3. Antes de modificar arquivos, examine seu conteúdo atual.
    4. Nunca altere arquivos sem solicitação explícita do usuário.
    5. Nunca exclua arquivos sem solicitação explícita do usuário.
    6. Não invente resultados de operações.
    7. Explique o que foi feito e quais arquivos foram afetados.
    8. Responda sempre em português brasileiro, salvo se o usuário
       solicitar outro idioma.

    Para tarefas que envolvam várias etapas, organize o trabalho
    e utilize as ferramentas necessárias na sequência.
    """,
    tools=[mcp_toolset],
)
