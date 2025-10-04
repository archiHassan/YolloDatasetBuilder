"""
Initialize annotation templates database
"""
import sqlite3
from pathlib import Path

def init_templates_db(db_path: str = "data/annotations.db"):
    """Initialize templates table in the database"""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = Path(__file__).parent / "templates_schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    conn.commit()

    # Insert some default templates
    default_templates = [
        {
            'name': 'Person Standing (Medium)',
            'description': 'Standard person standing, medium size',
            'category': 'person',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 80, "height": 200, "unit": "absolute"}',
            'confidence': 0.9
        },
        {
            'name': 'Person Standing (Large)',
            'description': 'Person standing, large/close-up',
            'category': 'person',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 150, "height": 350, "unit": "absolute"}',
            'confidence': 0.9
        },
        {
            'name': 'Person Standing (Small)',
            'description': 'Person standing, small/distant',
            'category': 'person',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 40, "height": 100, "unit": "absolute"}',
            'confidence': 0.9
        },
        {
            'name': 'Car Side View',
            'description': 'Standard car from side view',
            'category': 'car',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 180, "height": 120, "unit": "absolute"}',
            'confidence': 0.95
        },
        {
            'name': 'Car Front/Rear View',
            'description': 'Car from front or rear',
            'category': 'car',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 140, "height": 100, "unit": "absolute"}',
            'confidence': 0.95
        },
        {
            'name': 'Dog Standing',
            'description': 'Dog in standing position',
            'category': 'dog',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 120, "height": 90, "unit": "absolute"}',
            'confidence': 0.85
        },
        {
            'name': 'Cat Sitting',
            'description': 'Cat in sitting position',
            'category': 'cat',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 70, "height": 80, "unit": "absolute"}',
            'confidence': 0.85
        },
        {
            'name': 'Bicycle Side View',
            'description': 'Bicycle from side',
            'category': 'bicycle',
            'template_type': 'bbox',
            'bbox_data': '{"x": 0, "y": 0, "width": 150, "height": 110, "unit": "absolute"}',
            'confidence': 0.9
        }
    ]

    # Check if templates already exist
    cursor.execute("SELECT COUNT(*) FROM annotation_templates")
    count = cursor.fetchone()[0]

    if count == 0:
        for template in default_templates:
            cursor.execute("""
                INSERT INTO annotation_templates
                (name, description, category, template_type, bbox_data, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template['name'],
                template['description'],
                template['category'],
                template['template_type'],
                template['bbox_data'],
                template['confidence']
            ))

        conn.commit()
        print(f"[OK] Inserted {len(default_templates)} default templates")
    else:
        print(f"[OK] Templates table already has {count} templates")

    conn.close()
    print("[OK] Templates database initialized")

if __name__ == "__main__":
    init_templates_db()
