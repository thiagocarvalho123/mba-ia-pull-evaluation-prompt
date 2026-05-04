"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def extract_prompt_content(prompt) -> dict:
    """
    Extrai conteúdo de um ChatPromptTemplate do LangSmith Hub.

    Args:
        prompt: ChatPromptTemplate retornado pelo hub.pull()

    Returns:
        Dict com system_prompt e user_prompt extraídos
    """
    result = {
        "system_prompt": "",
        "user_prompt": "{bug_report}"
    }

    if not hasattr(prompt, "messages"):
        return result

    for message in prompt.messages:
        msg_type = type(message).__name__.lower()

        # Extrai o template text de diferentes tipos de message
        template_text = ""
        if hasattr(message, "prompt") and hasattr(message.prompt, "template"):
            template_text = message.prompt.template
        elif hasattr(message, "template"):
            template_text = message.template
        elif hasattr(message, "content"):
            template_text = message.content

        if "system" in msg_type:
            result["system_prompt"] = template_text
        elif "human" in msg_type or "user" in msg_type:
            result["user_prompt"] = template_text

    return result


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt base de baixa qualidade do LangSmith Hub e salva localmente.

    Returns:
        True se sucesso, False caso contrário
    """
    source_prompt = "leonanluppi/bug_to_user_story_v1"
    output_path = "prompts/bug_to_user_story_v1.yml"

    print(f"Fazendo pull do prompt: {source_prompt}")

    try:
        prompt = hub.pull(source_prompt)
        print(f"   ✓ Prompt carregado com sucesso")

        content = extract_prompt_content(prompt)

        yaml_data = {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories (pulled from LangSmith Hub)",
                "system_prompt": content.get("system_prompt", ""),
                "user_prompt": content.get("user_prompt", "{bug_report}"),
                "version": "v1",
                "source": source_prompt,
                "tags": ["bug-analysis", "user-story", "product-management"]
            }
        }

        if save_yaml(yaml_data, output_path):
            print(f"   ✓ Prompt salvo em: {output_path}")
            return True

        print(f"   ❌ Falha ao salvar arquivo {output_path}")
        return False

    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{source_prompt}': {e}")
        print("\nVerifique:")
        print("  - LANGSMITH_API_KEY está configurada corretamente no .env")
        print("  - Você tem conexão com a internet")
        print("  - O prompt existe no LangSmith Hub")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        print("\nPróximos passos:")
        print("  1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
        print("  2. Crie sua versão otimizada em prompts/bug_to_user_story_v2.yml")
        print("  3. Execute: python src/push_prompts.py")
        return 0
    else:
        print("\n❌ Falha no pull dos prompts.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
