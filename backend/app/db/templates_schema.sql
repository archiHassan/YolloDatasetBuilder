-- Annotation Templates Table
CREATE TABLE IF NOT EXISTS annotation_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    template_type TEXT NOT NULL CHECK(template_type IN ('bbox', 'polygon')),

    -- Bounding box template data (x, y, width, height as percentages or absolute)
    bbox_data TEXT,  -- JSON: {"x": 0, "y": 0, "width": 100, "height": 100, "unit": "absolute|percentage"}

    -- Polygon template data
    polygon_data TEXT,  -- JSON: {"points": [[x1,y1], [x2,y2], ...], "unit": "absolute|percentage"}

    -- Metadata
    confidence REAL DEFAULT 1.0,
    tags TEXT,  -- JSON array of tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_templates_category ON annotation_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_type ON annotation_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_templates_usage ON annotation_templates(usage_count DESC);
