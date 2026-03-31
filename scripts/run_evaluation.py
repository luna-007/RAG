# scripts/run_evaluation.py
"""
Run evaluation on the RAG system.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import RAGSystem
from evaluation.evaluator import RAGEvaluator
from evaluation.eval_dataset import INDIA_EVAL_DATASET


def main():
    print("🧪 RAG System Evaluation\n")
    
    # Setup RAG system
    print("Setting up RAG system...")
    rag_system = RAGSystem()
    
    url = "https://en.wikipedia.org/wiki/India"
    if not rag_system.setup_from_url(url, force_rebuild=False):
        print("❌ Failed to setup RAG system")
        sys.exit(1)
    
    print("✅ RAG system ready\n")
    
    # Run evaluation
    evaluator = RAGEvaluator(rag_system)
    metrics = evaluator.evaluate(
        dataset=INDIA_EVAL_DATASET,
        save_results=True
    )
    
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
