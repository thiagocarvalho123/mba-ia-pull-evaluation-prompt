"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Fixture que carrega o prompt v2 do arquivo YAML."""
    assert PROMPT_FILE.exists(), (
        f"Arquivo não encontrado: {PROMPT_FILE}\n"
        "Crie o arquivo prompts/bug_to_user_story_v2.yml antes de rodar os testes."
    )
    data = load_prompts(str(PROMPT_FILE))
    assert data is not None, f"Não foi possível parsear o YAML: {PROMPT_FILE}"
    assert PROMPT_KEY in data, (
        f"Chave '{PROMPT_KEY}' não encontrada no arquivo YAML.\n"
        f"Chaves disponíveis: {list(data.keys())}"
    )
    return data[PROMPT_KEY]


class TestPrompts:

    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, (
            "Campo 'system_prompt' não encontrado no YAML."
        )
        system_prompt = prompt_data["system_prompt"]
        assert system_prompt is not None, "system_prompt é None"
        assert isinstance(system_prompt, str), "system_prompt deve ser uma string"
        assert len(system_prompt.strip()) > 0, "system_prompt está vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        role_keywords = [
            "você é",
            "voce e",
            "product manager",
            "especialista",
            "sênior",
            "senior",
            "assistente especializado",
            "analista",
            "engenheiro",
        ]

        has_role = any(keyword in system_prompt for keyword in role_keywords)
        assert has_role, (
            "O prompt não define uma persona/role.\n"
            "Inclua uma definição de papel como 'Você é um Product Manager Sênior...' "
            "ou similar no início do system_prompt."
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        format_keywords = [
            "markdown",
            "user story",
            "como um",
            "critérios de aceitação",
            "criterios de aceitacao",
            "dado que",
            "quando",
            "então",
            "formato",
            "format",
        ]

        has_format = any(keyword in system_prompt for keyword in format_keywords)
        assert has_format, (
            "O prompt não especifica um formato de saída.\n"
            "Mencione explicitamente o formato esperado: User Story, Markdown, "
            "Critérios de Aceitação ou estrutura Dado/Quando/Então."
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        # Verifica exemplos embutidos no system_prompt
        inline_example_keywords = [
            "exemplo",
            "example",
            "bug report:",
            "user story esperada:",
            "few-shot",
            "few shot",
            "entrada",
            "saída",
        ]
        has_inline_examples = any(kw in system_prompt for kw in inline_example_keywords)

        # Verifica exemplos como lista separada no YAML
        examples_list = prompt_data.get("examples", [])
        has_examples_list = isinstance(examples_list, list) and len(examples_list) >= 1

        assert has_inline_examples or has_examples_list, (
            "O prompt não contém exemplos de entrada/saída (Few-Shot Learning).\n"
            "Adicione exemplos concretos de bug reports e user stories esperadas "
            "dentro do system_prompt ou como campo 'examples' no YAML."
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum [TODO] no texto."""
        system_prompt = prompt_data.get("system_prompt", "")
        user_prompt = prompt_data.get("user_prompt", "")
        description = prompt_data.get("description", "")

        full_text = system_prompt + user_prompt + description

        assert "[TODO]" not in full_text, (
            "O prompt contém '[TODO]' não resolvido. "
            "Preencha todos os TODOs antes de finalizar o prompt."
        )
        assert "[todo]" not in full_text.lower(), (
            "O prompt contém '[todo]' não resolvido (case insensitive). "
            "Preencha todos os TODOs antes de finalizar o prompt."
        )

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])

        assert isinstance(techniques, list), (
            "O campo 'techniques_applied' deve ser uma lista no YAML.\n"
            "Exemplo:\n"
            "  techniques_applied:\n"
            "    - role-prompting\n"
            "    - chain-of-thought"
        )

        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}.\n"
            "Adicione o campo 'techniques_applied' no YAML com pelo menos 2 técnicas.\n"
            "Técnicas válidas: role-prompting, chain-of-thought, few-shot-learning, "
            "tree-of-thought, skeleton-of-thought, react, etc."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
