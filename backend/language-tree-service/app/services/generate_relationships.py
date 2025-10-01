import asyncio
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime

# Import your function (adjust path if needed)
from app.services.wikipedia_service import fetch_language_relationships

# Define seed languages to start traversals from (expand as needed)
SEED_LANGUAGES = [
    "English"
    # Add more for broader coverage, e.g., "Swahili", "Latin", etc.
]

# Depth for each traversal (keep small to avoid explosion; max from your settings)
DEPTH = 1

# Output file
OUTPUT_FILE = "language_relationships_dataset.json"

# Task tracking
task_status = {}

class TaskStatus:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "running"  # running, completed, failed
        self.progress = 0
        self.total_languages = len(SEED_LANGUAGES)
        self.current_language = None
        self.error = None
        self.started_at = datetime.now()
        self.completed_at = None
        self.result_file = None

async def generate_dataset(task_id: str) -> List[Dict[str, str]]:
    """
    Generate a dataset by running fetch_language_relationships for each seed language,
    collecting and deduplicating relationships.
    """
    task = task_status[task_id]
    all_relationships: List[Dict[str, str]] = []
    
    try:
        for i, language in enumerate(SEED_LANGUAGES):
            task.current_language = language
            task.progress = i
            print(f"Processing {language} at depth {DEPTH}... ({i+1}/{len(SEED_LANGUAGES)})")
            
            try:
                # Run without WebSocket (None for manager and connection_id)
                rels = await fetch_language_relationships(
                    language_name=language,
                    depth=DEPTH,
                    websocket_manager=None,
                    connection_id=None
                )
                all_relationships.extend(rels)
                print(f"Added {len(rels)} relationships from {language}.")
            except ValueError as e:
                print(f"Error processing {language}: {e}")
            # Brief delay to avoid rate-limiting issues
            await asyncio.sleep(1)
        
        # Deduplicate: Convert to tuple of items for set uniqueness
        unique_rels = [dict(t) for t in {tuple(d.items()) for d in all_relationships}]
        
        print(f"Total unique relationships: {len(unique_rels)}")
        task.status = "completed"
        task.completed_at = datetime.now()
        task.progress = len(SEED_LANGUAGES)
        return unique_rels
    
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now()
        raise

def save_dataset(relationships: List[Dict[str, str]], task_id: str):
    """Save the dataset to JSON."""
    task = task_status[task_id]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"language_relationships_dataset_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(relationships, f, ensure_ascii=False, indent=4)
    
    task.result_file = filename
    print(f"Dataset saved to {filename}")

async def run_dataset_generation_background(task_id: str):
    """Background task to generate dataset."""
    try:
        relationships = await generate_dataset(task_id)
        save_dataset(relationships, task_id)
    except Exception as e:
        print(f"Background task failed: {e}")

def start_dataset_generation() -> str:
    """Start dataset generation as background task and return task ID."""
    task_id = str(uuid.uuid4())
    task_status[task_id] = TaskStatus(task_id)
    
    # Start background task
    asyncio.create_task(run_dataset_generation_background(task_id))
    
    return task_id

def get_task_status(task_id: str) -> Optional[dict]:
    """Get status of a dataset generation task."""
    if task_id not in task_status:
        return None
    
    task = task_status[task_id]
    return {
        "task_id": task_id,
        "status": task.status,
        "progress": task.progress,
        "total_languages": task.total_languages,
        "current_language": task.current_language,
        "error": task.error,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result_file": task.result_file
    }

async def final():
    """Async version of final that can be called from FastAPI endpoints."""
    # This is now deprecated in favor of the background task approach
    task_id = str(uuid.uuid4())
    task_status[task_id] = TaskStatus(task_id)
    relationships = await generate_dataset(task_id)
    save_dataset(relationships, task_id)