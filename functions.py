import json
import random
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_FILE = os.path.join(BASE_DIR, 'students.json')
RESULTS_FILE = os.path.join(BASE_DIR, 'results.json')

TOPICS = [
    "Python Lists vs Tuples",
    "Generators and Iterators",
    "Decorators in Python",
    "OOP Principles",
    "Dependency Injection",
    "RESTful APIs",
    "Docker Basics",
    "SQL vs NoSQL",
    "Git Branching Strategies",
    "CI/CD Pipelines"
]

def load_data(filename: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_data(filename: str, data: List[Dict[str, Any]]) -> None:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def start_exam(email: str, name: str) -> List[str]:
    """
    Registers the student if new, selects 2-3 random topics.
    Returns the list of topics.
    """
    students = load_data(STUDENTS_FILE)
    
    student = next((s for s in students if s['email'] == email), None)
    if not student:
        student = {
            'email': email,
            'name': name,
            'registered_at': datetime.now().isoformat()
        }
        students.append(student)
        save_data(STUDENTS_FILE, students)
    
    selected_topics = random.sample(TOPICS, k=3)
    return selected_topics

def end_exam(email: str, score: float, history: List[Dict[str, Any]]) -> None:
    """
    Saves the exam result. 
    Transform history to the requested format:
    {
        "role": "system" | "user" | "tool_call",
        "content": string,
        "datetime": iso_string
    }
    """
    results = load_data(RESULTS_FILE)
    
    formatted_history = []
    for msg in history:
        role = msg.get("role", "unknown")
        if role == "assistant":
            role = "system" 
        elif role == "tool":
            role = "tool_call"
            
        formatted_history.append({
            "role": role,
            "content": msg.get("content") or (json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else ""),
            "datetime": datetime.now().isoformat()
        })
    
    result_record = {
        'email': email,
        'score': score,
        'history': formatted_history,
        'completed_at': datetime.now().isoformat()
    }
    
    results.append(result_record)
    save_data(RESULTS_FILE, results)

def get_next_topic(all_topics: List[str], current_index: int) -> Optional[str]:
    """
    Returns the next topic based on index.
    """
    if current_index < len(all_topics):
        return all_topics[current_index]
    return None
