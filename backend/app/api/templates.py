"""
API endpoints for annotation templates
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime

router = APIRouter()

DB_PATH = "data/annotations.db"

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    template_type: str  # 'bbox' or 'polygon'
    bbox_data: Optional[dict] = None
    polygon_data: Optional[dict] = None
    confidence: float = 1.0
    tags: Optional[List[str]] = None

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None

class Template(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    template_type: str
    bbox_data: Optional[dict]
    polygon_data: Optional[dict]
    confidence: float
    tags: Optional[List[str]]
    created_at: str
    updated_at: str
    usage_count: int

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def row_to_template(row) -> dict:
    """Convert database row to template dict"""
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "category": row[3],
        "template_type": row[4],
        "bbox_data": json.loads(row[5]) if row[5] else None,
        "polygon_data": json.loads(row[6]) if row[6] else None,
        "confidence": row[7],
        "tags": json.loads(row[8]) if row[8] else None,
        "created_at": row[9],
        "updated_at": row[10],
        "usage_count": row[11]
    }

@router.get("/", response_model=List[Template])
async def list_templates(category: Optional[str] = None, template_type: Optional[str] = None):
    """List all templates with optional filters"""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM annotation_templates WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if template_type:
        query += " AND template_type = ?"
        params.append(template_type)

    query += " ORDER BY usage_count DESC, name ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [row_to_template(row) for row in rows]

@router.get("/{template_id}", response_model=Template)
async def get_template(template_id: int):
    """Get a specific template by ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM annotation_templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    return row_to_template(row)

@router.post("/", response_model=Template)
async def create_template(template: TemplateCreate):
    """Create a new template"""
    conn = get_db()
    cursor = conn.cursor()

    # Validate template type
    if template.template_type not in ['bbox', 'polygon']:
        raise HTTPException(status_code=400, detail="template_type must be 'bbox' or 'polygon'")

    # Ensure corresponding data exists
    if template.template_type == 'bbox' and not template.bbox_data:
        raise HTTPException(status_code=400, detail="bbox_data required for bbox template")
    if template.template_type == 'polygon' and not template.polygon_data:
        raise HTTPException(status_code=400, detail="polygon_data required for polygon template")

    cursor.execute("""
        INSERT INTO annotation_templates
        (name, description, category, template_type, bbox_data, polygon_data, confidence, tags, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        template.name,
        template.description,
        template.category,
        template.template_type,
        json.dumps(template.bbox_data) if template.bbox_data else None,
        json.dumps(template.polygon_data) if template.polygon_data else None,
        template.confidence,
        json.dumps(template.tags) if template.tags else None,
        datetime.now().isoformat()
    ))

    template_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return await get_template(template_id)

@router.put("/{template_id}", response_model=Template)
async def update_template(template_id: int, template: TemplateUpdate):
    """Update an existing template"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if template exists
    cursor.execute("SELECT id FROM annotation_templates WHERE id = ?", (template_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Template not found")

    # Build update query
    updates = []
    params = []

    if template.name is not None:
        updates.append("name = ?")
        params.append(template.name)

    if template.description is not None:
        updates.append("description = ?")
        params.append(template.description)

    if template.category is not None:
        updates.append("category = ?")
        params.append(template.category)

    if template.confidence is not None:
        updates.append("confidence = ?")
        params.append(template.confidence)

    if template.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(template.tags))

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())

    params.append(template_id)

    cursor.execute(f"""
        UPDATE annotation_templates
        SET {', '.join(updates)}
        WHERE id = ?
    """, params)

    conn.commit()
    conn.close()

    return await get_template(template_id)

@router.delete("/{template_id}")
async def delete_template(template_id: int):
    """Delete a template"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM annotation_templates WHERE id = ?", (template_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}

@router.post("/{template_id}/use")
async def increment_template_usage(template_id: int):
    """Increment usage count for a template"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE annotation_templates
        SET usage_count = usage_count + 1,
            updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), template_id))

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Usage count incremented"}

@router.get("/categories/list")
async def list_template_categories():
    """Get list of all unique categories in templates"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM annotation_templates ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()

    return {"categories": categories}
