"""
Cria um experimento oficial no LangSmith dashboard com todas as 5 métricas.
Popula a aba 'Experiments' do dataset sem re-executar a avaliação completa.

Uso:
    python src/create_experiment.py
"""

import os
import sys
import time
from dotenv import load_dotenv
from langsmith import Client
from langchain import hub
from langsmith.evaluation import evaluate as ls_evaluate
from utils import get_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()


def main():
    dataset_name = os.getenv("LANGCHAIN_PROJECT", "prompt-optimization-challenge-resolved") + "-eval"
    prompt_name = "bug_to_user_story_v2"

    print(f"Dataset : {dataset_name}")
    print(f"Prompt  : {prompt_name}")
    print(f"Exemplos: 10\n")

    client = Client()

    examples = list(client.list_examples(dataset_name=dataset_name))[:10]
    if not examples:
        print("❌ Nenhum exemplo encontrado no dataset. Execute evaluate.py primeiro.")
        return 1

    print(f"✓ {len(examples)} exemplos carregados do dataset")

    print(f"Puxando prompt do Hub...")
    prompt_template = hub.pull(prompt_name)
    chain = prompt_template | get_llm(temperature=0)
    print(f"✓ Prompt carregado\n")

    def extract_bug_report(inputs: dict) -> str:
        if "bug_report" in inputs:
            return inputs["bug_report"]
        if "messages" in inputs:
            messages = inputs["messages"]
            if messages:
                last = messages[-1]
                if isinstance(last, dict):
                    return last.get("content", "")
                return str(last)
        for v in inputs.values():
            if isinstance(v, str):
                return v
        return ""

    def target(inputs: dict) -> dict:
        try:
            bug_report = extract_bug_report(inputs)
            return {"output": chain.invoke({"bug_report": bug_report}).content}
        except Exception as e:
            print(f"  ⚠️  Erro ao invocar prompt: {e}")
            return {"output": ""}

    def full_evaluator(run, example):
        answer = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = extract_bug_report(example.inputs or {})

        f1 = evaluate_f1_score(question, answer, reference)["score"]
        time.sleep(4)
        clarity = evaluate_clarity(question, answer, reference)["score"]
        time.sleep(4)
        precision = evaluate_precision(question, answer, reference)["score"]

        helpfulness = round((clarity + precision) / 2, 4)
        correctness = round((f1 + precision) / 2, 4)

        print(f"  F1:{f1:.2f} Clarity:{clarity:.2f} Precision:{precision:.2f} "
              f"Helpfulness:{helpfulness:.2f} Correctness:{correctness:.2f}")

        return [
            {"key": "f1_score",    "score": f1},
            {"key": "clarity",     "score": clarity},
            {"key": "precision",   "score": precision},
            {"key": "helpfulness", "score": helpfulness},
            {"key": "correctness", "score": correctness},
        ]

    print("Criando experimento no LangSmith...")
    ls_evaluate(
        target,
        data=examples,
        evaluators=[full_evaluator],
        experiment_prefix=prompt_name,
        max_concurrency=1,
    )

    print("\n✅ Experimento criado!")
    print("Acesse: LangSmith → Datasets & Experiments →", dataset_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
