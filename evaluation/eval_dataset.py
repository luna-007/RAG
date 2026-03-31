# evaluation/eval_dataset.py
"""
Evaluation datasets for different document types.
"""
from typing import List, Dict, TypedDict

class EvalQuestion(TypedDict):
    """Structure for evaluation question"""
    id: int
    question: str
    expected_keywords: List[str]
    should_answer: bool  # Whether system should have the answer
    difficulty: str  # 'easy', 'medium', 'hard'
    category: str  # 'factual', 'reasoning', 'off-topic'


# India Wikipedia dataset
INDIA_EVAL_DATASET: List[EvalQuestion] = [
    {
        "id": 1,
        "question": "What is the capital of India?",
        "expected_keywords": ["New Delhi", "Delhi", "capital"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 2,
        "question": "What is India's population?",
        "expected_keywords": ["billion", "population", "1.4", "1.3"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 3,
        "question": "Who is the current Prime Minister of India?",
        "expected_keywords": ["Narendra Modi", "Modi", "Prime Minister"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 4,
        "question": "When did India gain independence?",
        "expected_keywords": ["1947", "independence", "British", "August 15"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 5,
        "question": "What is India's currency?",
        "expected_keywords": ["rupee", "INR", "currency"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 6,
        "question": "What are the major religions in India?",
        "expected_keywords": ["Hindu", "Muslim", "Christian", "Sikh", "religion"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 7,
        "question": "What are India's neighboring countries?",
        "expected_keywords": ["Pakistan", "China", "Nepal", "Bangladesh", "Myanmar", "Sri Lanka"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 8,
        "question": "What is the Ganges river and why is it important?",
        "expected_keywords": ["Ganges", "Ganga", "river", "sacred", "holy"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "reasoning"
    },
    {
        "id": 9,
        "question": "What is India's GDP and economic ranking?",
        "expected_keywords": ["GDP", "economy", "trillion", "world"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 10,
        "question": "What is the Taj Mahal?",
        "expected_keywords": ["Taj Mahal", "monument", "Agra", "Shah Jahan", "mausoleum"],
        "should_answer": True,
        "difficulty": "easy",
        "category": "factual"
    },
    {
        "id": 11,
        "question": "What languages are spoken in India?",
        "expected_keywords": ["Hindi", "English", "languages", "multilingual"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 12,
        "question": "Compare India's government structure to the United States",
        "expected_keywords": ["democracy", "parliament", "republic", "federal"],
        "should_answer": True,
        "difficulty": "hard",
        "category": "reasoning"
    },
    {
        "id": 13,
        "question": "What's the weather in Mumbai today?",  # Should NOT answer
        "expected_keywords": [],
        "should_answer": False,
        "difficulty": "easy",
        "category": "off-topic"
    },
    {
        "id": 14,
        "question": "What is Python programming language?",  # Off-topic
        "expected_keywords": [],
        "should_answer": False,
        "difficulty": "easy",
        "category": "off-topic"
    },
    {
        "id": 15,
        "question": "How do I cook biryani?",  # Off-topic
        "expected_keywords": [],
        "should_answer": False,
        "difficulty": "easy",
        "category": "off-topic"
    },
    {
        "id": 16,
        "question": "What is India's space program?",
        "expected_keywords": ["ISRO", "space", "satellite", "Mars", "Chandrayaan"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 17,
        "question": "What is India's literacy rate?",
        "expected_keywords": ["literacy", "education", "percent"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 18,
        "question": "Describe India's relationship with Pakistan",
        "expected_keywords": ["Pakistan", "conflict", "Kashmir", "partition"],
        "should_answer": True,
        "difficulty": "hard",
        "category": "reasoning"
    },
    {
        "id": 19,
        "question": "What are the major industries in India?",
        "expected_keywords": ["IT", "technology", "agriculture", "manufacturing", "textile"],
        "should_answer": True,
        "difficulty": "medium",
        "category": "factual"
    },
    {
        "id": 20,
        "question": "What is India's role in climate change?",
        "expected_keywords": ["emissions", "renewable", "solar", "energy", "climate"],
        "should_answer": True,
        "difficulty": "hard",
        "category": "reasoning"
    },
]


def get_dataset_by_category(category: str) -> List[EvalQuestion]:
    """Get eval questions by category"""
    return [q for q in INDIA_EVAL_DATASET if q['category'] == category]


def get_dataset_by_difficulty(difficulty: str) -> List[EvalQuestion]:
    """Get eval questions by difficulty"""
    return [q for q in INDIA_EVAL_DATASET if q['difficulty'] == difficulty]
