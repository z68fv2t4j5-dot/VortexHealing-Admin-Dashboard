from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Task, TaskStatus
from pydantic import BaseModel
import httpx
from datetime import datetime

router = APIRouter()

class TaskPrompt(BaseModel):
    prompt: str
    priority: int = 0

class TaskResponse(BaseModel):
    title: str
    description: str
    priority: int
    id: int = None

@router.post("/ai/generate-task", response_model=TaskResponse)
async def generate_task_with_ai(task_prompt: TaskPrompt, db: Session = Depends(get_db)):
    """Generate and create a task using Qwen AI"""

    # Send prompt to Qwen for refinement
    qwen_prompt = f"""You are a task planning AI. Refine this task description into a clear, actionable task:

User Input: {task_prompt.prompt}

Respond with ONLY a JSON object (no markdown, no code blocks) with these exact fields:
{{"title": "concise task title (max 100 chars)", "description": "detailed task description with clear next steps"}}"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": "qwen",
                    "messages": [{"role": "user", "content": qwen_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Qwen error: {response.text}")

            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            # Try to extract JSON from the response
            import json
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            task_data = json.loads(content)

    except Exception as e:
        # Fallback if Qwen fails
        task_data = {
            "title": task_prompt.prompt[:100],
            "description": task_prompt.prompt
        }

    # Create task in database
    db_task = Task(
        title=task_data.get("title", task_prompt.prompt[:100]),
        description=task_data.get("description", task_prompt.prompt),
        status=TaskStatus.TODO,
        priority=task_prompt.priority,
        created_at=datetime.utcnow()
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return TaskResponse(
        title=db_task.title,
        description=db_task.description,
        priority=db_task.priority,
        id=db_task.id
    )
