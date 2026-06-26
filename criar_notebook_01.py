from pathlib import Path
import nbformat as nbf

pasta_notebooks = Path("notebooks")
pasta_notebooks.mkdir(exist_ok=True)

caminho = pasta_notebooks / "01_configuracao_projeto.ipynb"

notebook = nbf.v4.new_notebook()

notebook.cells = [
    nbf.v4.new_markdown_cell(
        "# 01 - Configuração do Projeto\n\n"
        "Este notebook configura a estrutura inicial do projeto, cria o banco SQLite, "
        "gera a base sintética de leads agrícolas e valida as primeiras consultas."
    )
]

nbf.write(notebook, caminho)

print(f"Notebook criado com sucesso: {caminho}")
