# Database Schema & ERD
## YOLO Dataset Builder - Complete Database Documentation

**Version**: 1.0
**Database**: SQLite 3
**Location**: `data/annotations.db`

---

## Entity Relationship Diagram (ERD)

###Text-Based ERD
```
┌──────────────────────────┐
│       images             │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 📝 filename  (UNIQUE)    │
│ 📏 width                 │
│ 📏 height                │
│ 📁 file_path             │
│ 📊 status                │
│ 📅 created_at            │
└──────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌──────────────────────────┐
│     annotations          │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 🔗 image_id (FK)         │
│ 🏷️ category_id           │
│ 🏷️ category_name         │
│ 📦 bbox (JSON)           │
│ 📐 points (JSON)         │
│ 🎭 segmentation (JSON)   │
│ 📏 area                  │
│ 👥 iscrowd               │
│ 📊 confidence            │
│ ✅ status                │
│ 📅 created_at            │
└──────────────────────────┘

┌──────────────────────────┐
│  annotation_templates    │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 📝 name                  │
│ 📄 description           │
│ 🏷️ category              │
│ 🔷 template_type         │
│ 📦 bbox_data (JSON)      │
│ 📐 polygon_data (JSON)   │
│ 📊 confidence            │
│ 🏷️ tags (JSON)           │
│ 📈 usage_count           │
│ 📅 created_at            │
│ 📅 updated_at            │
└──────────────────────────┘
```

---

## Table Schemas

### 1. `images` Table

**Purpose**: Store metadata for all uploaded images

**Schema**:
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_filename ON images(filename);
```

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `filename` | TEXT | NOT NULL, UNIQUE | Original filename (e.g., "cat.jpg") |
| `width` | INTEGER | NOT NULL | Image width in pixels |
| `height` | INTEGER | NOT NULL | Image height in pixels |
| `file_path` | TEXT | NOT NULL | Relative path to image file |
| `status` | TEXT | DEFAULT 'pending' | Review status: pending/approved/rejected |
| `created_at` | TIMESTAMP | DEFAULT NOW | Upload timestamp |

**Indexes**:
- Primary index on `id`
- Index on `status` (for filtering)
- Index on `filename` (for uniqueness check)

**Sample Data**:
```json
{
  "id": 1,
  "filename": "cat_001.jpg",
  "width": 640,
  "height": 480,
  "file_path": "data/images/cat_001.jpg",
  "status": "pending",
  "created_at": "2025-10-03T12:34:56"
}
```

---

### 2. `annotations` Table

**Purpose**: Store all annotation data in COCO-compatible format

**Schema**:
```sql
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    bbox TEXT,  -- JSON array: [x, y, width, height]
    points TEXT,  -- JSON array: [[x1,y1], [x2,y2], ...]
    segmentation TEXT,  -- JSON array: COCO RLE or polygon format
    area REAL,
    iscrowd INTEGER DEFAULT 0 CHECK(iscrowd IN (0, 1)),
    confidence REAL DEFAULT 1.0 CHECK(confidence >= 0 AND confidence <= 1),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

CREATE INDEX idx_annotations_image ON annotations(image_id);
CREATE INDEX idx_annotations_category ON annotations(category_id);
CREATE INDEX idx_annotations_status ON annotations(status);
CREATE INDEX idx_annotations_confidence ON annotations(confidence);
```

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing annotation ID |
| `image_id` | INTEGER | FK, NOT NULL | References images(id) |
| `category_id` | INTEGER | NOT NULL | COCO category ID (1=person, 2=car, etc.) |
| `category_name` | TEXT | NOT NULL | Human-readable category (e.g., "person") |
| `bbox` | TEXT (JSON) | NULL | Bounding box [x, y, width, height] |
| `points` | TEXT (JSON) | NULL | Polygon points [[x1,y1], [x2,y2], ...] |
| `segmentation` | TEXT (JSON) | NULL | COCO segmentation format |
| `area` | REAL | NULL | Annotation area in pixels |
| `iscrowd` | INTEGER | 0 or 1 | COCO crowd flag (0=individual, 1=crowd) |
| `confidence` | REAL | 0.0-1.0 | Model confidence score |
| `status` | TEXT | DEFAULT 'pending' | Review status |
| `created_at` | TIMESTAMP | DEFAULT NOW | Creation timestamp |

**Annotation Types**:
1. **Bounding Box**: `bbox` field populated, `points` NULL
2. **Polygon**: `points` field populated, `bbox` can be calculated
3. **Segmentation**: `segmentation` field for masks

**Sample Data** (Bounding Box):
```json
{
  "id": 101,
  "image_id": 1,
  "category_id": 17,
  "category_name": "cat",
  "bbox": "[120, 80, 200, 150]",
  "points": null,
  "segmentation": null,
  "area": 30000.0,
  "iscrowd": 0,
  "confidence": 0.92,
  "status": "approved",
  "created_at": "2025-10-03T12:35:00"
}
```

**Sample Data** (Polygon):
```json
{
  "id": 102,
  "image_id": 1,
  "category_id": 17,
  "category_name": "cat",
  "bbox": null,
  "points": "[[120,80], [320,80], [320,230], [120,230]]",
  "segmentation": null,
  "area": 30000.0,
  "iscrowd": 0,
  "confidence": 0.88,
  "status": "pending",
  "created_at": "2025-10-03T12:36:00"
}
```

---

### 3. `annotation_templates` Table

**Purpose**: Store reusable annotation templates for faster labeling

**Schema**:
```sql
CREATE TABLE annotation_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    template_type TEXT NOT NULL CHECK(template_type IN ('bbox', 'polygon')),
    bbox_data TEXT,  -- JSON: {"x": 0, "y": 0, "width": 100, "height": 150, "unit": "absolute"}
    polygon_data TEXT,  -- JSON: {"points": [[x1,y1], ...], "unit": "absolute"}
    confidence REAL DEFAULT 1.0,
    tags TEXT,  -- JSON array: ["person", "standing", "medium"]
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_category ON annotation_templates(category);
CREATE INDEX idx_templates_type ON annotation_templates(template_type);
CREATE INDEX idx_templates_usage ON annotation_templates(usage_count DESC);
```

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing template ID |
| `name` | TEXT | NOT NULL | Template name (e.g., "Person Standing Medium") |
| `description` | TEXT | NULL | Optional description |
| `category` | TEXT | NOT NULL | Object category (e.g., "person") |
| `template_type` | TEXT | bbox/polygon | Type of annotation |
| `bbox_data` | TEXT (JSON) | NULL | Bounding box dimensions |
| `polygon_data` | TEXT (JSON) | NULL | Polygon shape data |
| `confidence` | REAL | 0.0-1.0 | Default confidence for template |
| `tags` | TEXT (JSON) | NULL | Searchable tags |
| `usage_count` | INTEGER | DEFAULT 0 | How many times template was used |
| `created_at` | TIMESTAMP | DEFAULT NOW | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW | Last update timestamp |

**Sample Data**:
```json
{
  "id": 1,
  "name": "Person Standing (Medium)",
  "description": "Standard person standing, medium size",
  "category": "person",
  "template_type": "bbox",
  "bbox_data": "{\"x\": 0, \"y\": 0, \"width\": 80, \"height\": 200, \"unit\": \"absolute\"}",
  "polygon_data": null,
  "confidence": 0.9,
  "tags": "[\"person\", \"standing\", \"medium\"]",
  "usage_count": 47,
  "created_at": "2025-10-01T10:00:00",
  "updated_at": "2025-10-03T15:30:00"
}
```

---

## Relationships

### 1. Images → Annotations (One-to-Many)
- **Type**: One-to-Many
- **Cardinality**: 1 image → 0..N annotations
- **Foreign Key**: `annotations.image_id` → `images.id`
- **On Delete**: CASCADE (delete annotations when image is deleted)

```sql
-- Get all annotations for an image
SELECT * FROM annotations WHERE image_id = 1;

-- Get image with annotation count
SELECT i.*, COUNT(a.id) as annotation_count
FROM images i
LEFT JOIN annotations a ON i.id = a.image_id
GROUP BY i.id;
```

### 2. Templates (Independent)
- **Type**: No foreign keys
- **Relationship**: Templates are independent, referenced by frontend logic
- **Usage**: Template ID is not stored in annotations table

---

## Data Types & Constraints

### JSON Fields
All JSON fields are stored as TEXT and parsed by application logic.

**Why TEXT instead of JSON type?**
- SQLite JSON support is limited
- Better compatibility
- Application-level validation

**JSON Schemas**:

#### bbox (TEXT):
```json
"[x, y, width, height]"
// Example: "[120, 80, 200, 150]"
```

#### points (TEXT):
```json
"[[x1, y1], [x2, y2], ...]"
// Example: "[[120,80], [320,80], [320,230], [120,230]]"
```

#### bbox_data in templates (TEXT):
```json
{
  "x": 0,
  "y": 0,
  "width": 100,
  "height": 150,
  "unit": "absolute"  // or "percentage"
}
```

### Check Constraints
```sql
-- Status must be one of three values
CHECK(status IN ('pending', 'approved', 'rejected'))

-- Confidence must be between 0 and 1
CHECK(confidence >= 0 AND confidence <= 1)

-- IsCrowd must be 0 or 1
CHECK(iscrowd IN (0, 1))

-- Template type must be bbox or polygon
CHECK(template_type IN ('bbox', 'polygon'))
```

---

## Indexes

### Purpose
- Speed up queries on frequently filtered columns
- Improve JOIN performance
- Optimize sorting operations

### Index Strategy

#### Primary Indexes (Automatic)
- `images.id`
- `annotations.id`
- `annotation_templates.id`

#### Secondary Indexes (Manual)
```sql
-- Images table
CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_filename ON images(filename);

-- Annotations table
CREATE INDEX idx_annotations_image ON annotations(image_id);
CREATE INDEX idx_annotations_category ON annotations(category_id);
CREATE INDEX idx_annotations_status ON annotations(status);
CREATE INDEX idx_annotations_confidence ON annotations(confidence);

-- Templates table
CREATE INDEX idx_templates_category ON annotation_templates(category);
CREATE INDEX idx_templates_type ON annotation_templates(template_type);
CREATE INDEX idx_templates_usage ON annotation_templates(usage_count DESC);
```

### Query Performance
| Query | Without Index | With Index |
|-------|---------------|------------|
| Find image by filename | O(n) scan | O(log n) lookup |
| Filter by status | O(n) scan | O(log n) lookup |
| Get annotations for image | O(n) scan | O(log n) lookup |
| Sort templates by usage | O(n log n) | O(n) (pre-sorted) |

---

## Migration Scripts

### Initial Schema Creation
```sql
-- File: backend/app/db/init_db.sql

-- Create images table
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create annotations table
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    bbox TEXT,
    points TEXT,
    segmentation TEXT,
    area REAL,
    iscrowd INTEGER DEFAULT 0,
    confidence REAL DEFAULT 1.0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_annotations_image ON annotations(image_id);
CREATE INDEX idx_annotations_category ON annotations(category_id);
```

### Template Schema Creation
```sql
-- File: backend/app/db/templates_schema.sql

CREATE TABLE IF NOT EXISTS annotation_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    template_type TEXT NOT NULL CHECK(template_type IN ('bbox', 'polygon')),
    bbox_data TEXT,
    polygon_data TEXT,
    confidence REAL DEFAULT 1.0,
    tags TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_category ON annotation_templates(category);
```

---

## Backup & Recovery

### Backup Strategy
```bash
# Full database backup
cp data/annotations.db data/backups/annotations_$(date +%Y%m%d_%H%M%S).db

# Incremental backup (SQLite doesn't support, use full backups)
# Recommended: Daily backups, keep last 7 days
```

### Recovery
```bash
# Restore from backup
cp data/backups/annotations_20251003_120000.db data/annotations.db
```

### Export to SQL
```bash
# Export schema + data
sqlite3 data/annotations.db .dump > backup.sql

# Import from SQL
sqlite3 data/annotations_new.db < backup.sql
```

---

## Common Queries

### Get image with annotations
```sql
SELECT
    i.*,
    json_group_array(
        json_object(
            'id', a.id,
            'category', a.category_name,
            'bbox', a.bbox,
            'confidence', a.confidence
        )
    ) as annotations
FROM images i
LEFT JOIN annotations a ON i.id = a.image_id
WHERE i.id = ?
GROUP BY i.id;
```

### Get review queue (pending images)
```sql
SELECT * FROM images
WHERE status = 'pending'
ORDER BY created_at ASC
LIMIT 20;
```

### Get annotation statistics
```sql
SELECT
    category_name,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence
FROM annotations
GROUP BY category_name
ORDER BY count DESC;
```

### Get most used templates
```sql
SELECT * FROM annotation_templates
ORDER BY usage_count DESC
LIMIT 10;
```

---

## Database Constraints & Integrity

### Foreign Key Enforcement
```sql
-- Enable foreign key constraints (must be done per connection)
PRAGMA foreign_keys = ON;
```

### Data Integrity Rules
1. **Images must be unique by filename**
2. **Annotations cannot exist without image** (CASCADE delete)
3. **Status must be valid** (CHECK constraint)
4. **Confidence must be 0-1** (CHECK constraint)
5. **Template type must be bbox/polygon** (CHECK constraint)

---

## Future Enhancements

### Planned Schema Changes
1. **Users table** (for authentication)
   ```sql
   CREATE TABLE users (
       id INTEGER PRIMARY KEY,
       username TEXT UNIQUE,
       password_hash TEXT,
       role TEXT
   );
   ```

2. **Annotation history** (for audit trail)
   ```sql
   CREATE TABLE annotation_history (
       id INTEGER PRIMARY KEY,
       annotation_id INTEGER,
       user_id INTEGER,
       action TEXT,
       old_value TEXT,
       new_value TEXT,
       timestamp TIMESTAMP
   );
   ```

3. **Projects** (for organization)
   ```sql
   CREATE TABLE projects (
       id INTEGER PRIMARY KEY,
       name TEXT,
       description TEXT,
       created_by INTEGER
   );
   ```

### Migration to PostgreSQL
If scaling beyond SQLite:
```sql
-- PostgreSQL would use:
- SERIAL instead of AUTOINCREMENT
- JSONB instead of TEXT for JSON
- UUID instead of INTEGER for IDs
- Proper timestamp types
```

---

**Document Status**: ✅ Complete
**Last Updated**: October 2025
**Schema Version**: 1.0
