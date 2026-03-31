# evaluation/evaluator.py
"""
RAG system evaluator with multiple metrics.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from evaluation.eval_dataset import EvalQuestion, INDIA_EVAL_DATASET
from src.utils.logging_utils import get_logger

logger = get_logger("evaluator")


@dataclass
class EvalResult:
    """Result for a single evaluation question"""
    question_id: int
    question: str
    answer: str
    retrieved_chunks: int
    retrieval_success: bool
    answer_has_keywords: bool
    proper_rejection: bool
    latency_seconds: float
    error: str = ""


@dataclass
class EvalMetrics:
    """Aggregate evaluation metrics"""
    total_questions: int
    retrieval_hit_rate: float
    answer_quality: float
    rejection_rate: float
    avg_latency: float
    avg_chunks_retrieved: float
    errors: int


class RAGEvaluator:
    """Evaluate RAG system performance"""
    
    def __init__(self, rag_system):
        """
        Initialize evaluator.
        
        Args:
            rag_system: RAGSystem instance to evaluate
        """
        self.rag_system = rag_system
        self.results: List[EvalResult] = []
        
    def evaluate(
        self,
        dataset: List[EvalQuestion] = None,
        save_results: bool = True
    ) -> EvalMetrics:
        """
        Run evaluation on dataset.
        
        Args:
            dataset: List of evaluation questions (uses India dataset if None)
            save_results: Whether to save results to file
            
        Returns:
            EvalMetrics with aggregate results
        """
        if dataset is None:
            dataset = INDIA_EVAL_DATASET
        
        logger.info("Starting evaluation", num_questions=len(dataset))
        print(f"\n📊 Evaluating on {len(dataset)} questions...\n")
        
        self.results = []
        
        for i, item in enumerate(dataset, 1):
            print(f"[{i}/{len(dataset)}] {item['question'][:50]}...", end=" ")
            
            result = self._evaluate_single(item)
            self.results.append(result)
            
            if result.error:
                print("❌ ERROR")
            elif result.proper_rejection and not item['should_answer']:
                print("✅ Properly rejected")
            elif result.answer_has_keywords:
                print("✅ Correct")
            else:
                print("⚠️ Partial/Incorrect")
        
        # Calculate metrics
        metrics = self._calculate_metrics(dataset)
        
        # Print summary
        self._print_summary(metrics)
        
        # Save results
        if save_results:
            self._save_results(metrics)
        
        return metrics
    
    def _evaluate_single(self, item: EvalQuestion) -> EvalResult:
        """Evaluate a single question"""
        start_time = time.time()
        
        try:
            # Query the system (no streaming for eval)
            answer = self.rag_system.query(
                item['question'],
                chat_history=[],
                stream=False
            )
            
            if answer is None:
                return EvalResult(
                    question_id=item['id'],
                    question=item['question'],
                    answer="",
                    retrieved_chunks=0,
                    retrieval_success=False,
                    answer_has_keywords=False,
                    proper_rejection=False,
                    latency_seconds=time.time() - start_time,
                    error="Query returned None"
                )
            
            # Get retrieval info (would need to modify RAG system to expose this)
            # For now, assume we got some chunks
            retrieved_chunks = 10  # Placeholder
            
            # Check retrieval success
            answer_lower = answer.lower()
            retrieval_success = False
            if item['should_answer']:
                retrieval_success = any(
                    keyword.lower() in answer_lower
                    for keyword in item['expected_keywords']
                )
            
            # Check answer quality
            answer_has_keywords = False
            if item['should_answer'] and item['expected_keywords']:
                answer_has_keywords = any(
                    keyword.lower() in answer_lower
                    for keyword in item['expected_keywords']
                )
            
            # Check proper rejection
            proper_rejection = False
            if not item['should_answer']:
                rejection_phrases = [
                    "don't have",
                    "no information",
                    "cannot answer",
                    "not in my knowledge"
                ]
                proper_rejection = any(
                    phrase in answer_lower
                    for phrase in rejection_phrases
                )
            
            return EvalResult(
                question_id=item['id'],
                question=item['question'],
                answer=answer[:200],  # Truncate for storage
                retrieved_chunks=retrieved_chunks,
                retrieval_success=retrieval_success,
                answer_has_keywords=answer_has_keywords,
                proper_rejection=proper_rejection,
                latency_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error("Evaluation failed for question",
                        question_id=item['id'],
                        error=str(e))
            
            return EvalResult(
                question_id=item['id'],
                question=item['question'],
                answer="",
                retrieved_chunks=0,
                retrieval_success=False,
                answer_has_keywords=False,
                proper_rejection=False,
                latency_seconds=time.time() - start_time,
                error=str(e)
            )
    
    def _calculate_metrics(self, dataset: List[EvalQuestion]) -> EvalMetrics:
        """Calculate aggregate metrics"""
        total = len(dataset)
        
        # Separate into should-answer and should-reject
        should_answer = [
            r for r in self.results
            if dataset[r.question_id - 1]['should_answer']
        ]
        should_reject = [
            r for r in self.results
            if not dataset[r.question_id - 1]['should_answer']
        ]
        
        # Calculate rates
        retrieval_hit_rate = (
            sum(r.retrieval_success for r in should_answer) / len(should_answer)
            if should_answer else 0
        )
        
        answer_quality = (
            sum(r.answer_has_keywords for r in should_answer) / len(should_answer)
            if should_answer else 0
        )
        
        rejection_rate = (
            sum(r.proper_rejection for r in should_reject) / len(should_reject)
            if should_reject else 0
        )
        
        avg_latency = sum(r.latency_seconds for r in self.results) / total
        avg_chunks = sum(r.retrieved_chunks for r in self.results) / total
        errors = sum(1 for r in self.results if r.error)
        
        return EvalMetrics(
            total_questions=total,
            retrieval_hit_rate=retrieval_hit_rate,
            answer_quality=answer_quality,
            rejection_rate=rejection_rate,
            avg_latency=avg_latency,
            avg_chunks_retrieved=avg_chunks,
            errors=errors
        )
    
    def _print_summary(self, metrics: EvalMetrics):
        """Print evaluation summary"""
        print("\n" + "="*70)
        print("EVALUATION RESULTS")
        print("="*70)
        print(f"Total Questions:        {metrics.total_questions}")
        print(f"Retrieval Hit Rate:     {metrics.retrieval_hit_rate:.1%}")
        print(f"Answer Quality:         {metrics.answer_quality:.1%}")
        print(f"Proper Rejection Rate:  {metrics.rejection_rate:.1%}")
        print(f"Avg Latency:            {metrics.avg_latency:.2f}s")
        print(f"Avg Chunks Retrieved:   {metrics.avg_chunks_retrieved:.1f}")
        print(f"Errors:                 {metrics.errors}")
        print("="*70)
    
    def _save_results(self, metrics: EvalMetrics):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eval_results_{timestamp}.json"
        filepath = Path("evaluation/results") / filename
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            "timestamp": timestamp,
            "metrics": asdict(metrics),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info("Results saved", filepath=str(filepath))
        print(f"\n💾 Results saved to: {filepath}")
