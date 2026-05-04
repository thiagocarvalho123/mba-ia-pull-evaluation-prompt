"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client as LangSmithClient
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (sem username)
        prompt_data: Dados do prompt carregados do YAML

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
        print("   Configure seu username do LangSmith Hub no arquivo .env")
        return False

    full_prompt_name = f"{username}/{prompt_name}"
    print(f"Fazendo push do prompt: {full_prompt_name}")

    try:
        system_prompt = prompt_data.get("system_prompt", "")
        user_prompt = prompt_data.get("user_prompt", "{bug_report}")
        description = prompt_data.get("description", "Prompt otimizado para converter bugs em User Stories")
        techniques = prompt_data.get("techniques_applied", [])
        tags = prompt_data.get("tags", [])

        # Monta descrição com técnicas aplicadas
        if techniques:
            description += f" | Técnicas: {', '.join(techniques)}"

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])

        client = LangSmithClient()
        url = client.push_prompt(
            full_prompt_name,
            object=prompt_template,
            is_public=True,
            description=description,
        )

        print(f"   ✓ Prompt publicado com sucesso!")
        if url:
            print(f"   ✓ URL: {url}")
        else:
            print(f"   ✓ Acesse em: https://smith.langchain.com/prompts/{full_prompt_name}")

        return True

    except Exception as e:
        error_msg = str(e)
        if "Nothing to commit" in error_msg or "409" in error_msg:
            print(f"   ✓ Prompt já está atualizado no LangSmith (nenhuma alteração desde o último push)")
            print(f"   ✓ Acesse em: https://smith.langchain.com/prompts/{full_prompt_name}")
            return True

        print(f"❌ Erro ao fazer push do prompt '{full_prompt_name}': {e}")
        print("\nVerifique:")
        print("  - LANGSMITH_API_KEY está configurada corretamente no .env")
        print("  - USERNAME_LANGSMITH_HUB está correto")
        print("  - Você tem conexão com a internet")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    # Verifica campos obrigatórios
    if "system_prompt" not in prompt_data:
        errors.append("Campo 'system_prompt' não encontrado")
    elif not prompt_data["system_prompt"].strip():
        errors.append("Campo 'system_prompt' está vazio")

    if "version" not in prompt_data:
        errors.append("Campo 'version' não encontrado")

    # Verifica ausência de TODOs
    system_prompt = prompt_data.get("system_prompt", "")
    if "[TODO]" in system_prompt or "[todo]" in system_prompt.lower():
        errors.append("system_prompt contém TODOs não resolvidos")

    # Verifica técnicas aplicadas
    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}. "
            f"Adicione 'techniques_applied' no YAML."
        )

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    yaml_file = "prompts/bug_to_user_story_v2.yml"
    print(f"Carregando prompt de: {yaml_file}")

    yaml_data = load_yaml(yaml_file)
    if not yaml_data:
        print(f"❌ Não foi possível carregar: {yaml_file}")
        print("   Certifique-se de ter criado o arquivo prompts/bug_to_user_story_v2.yml")
        return 1

    prompt_key = "bug_to_user_story_v2"
    prompt_data = yaml_data.get(prompt_key)
    if not prompt_data:
        print(f"❌ Chave '{prompt_key}' não encontrada no arquivo YAML")
        print(f"   Certifique-se de que o YAML começa com '{prompt_key}:'")
        return 1

    print("Validando prompt...")
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Validação aprovada")

    success = push_prompt_to_langsmith(prompt_key, prompt_data)

    if success:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "")
        print(f"\n✅ Push concluído com sucesso!")
        print(f"\nVerifique o prompt publicado em:")
        print(f"  https://smith.langchain.com/prompts/{username}/{prompt_key}")
        print(f"\nPróximos passos:")
        print(f"  1. Confirme que o prompt está público no LangSmith")
        print(f"  2. Execute a avaliação: python src/evaluate.py")
        return 0
    else:
        print("\n❌ Falha no push do prompt.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
