# API Reference
## YOLO Dataset Builder - Complete API Documentation

**Version**: 1.0
**Base URL**: `http://localhost:8000/api`
**Format**: JSON
**Authentication**: None (currently)

---

## Table of Contents
1. [Overview](#overview)
2. [Images API](#images-api)
3. [Annotations API](#annotations-api)
4. [Review API](#review-api)
5. [Export API](#export-api)
6. [Templates API](#templates-api)
7. [SAM API](#sam-api)
8. [Error Handling](#error-handling)
9. [Examples](#examples)

---

## Overview

### Base URL
```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

### Response Format
All responses are JSON with the following structure:

**Success Response**:
```json
{
  "data": {...},
  "status": "success"
}
```

**Error Response**:
```json
{
  "detail": "Error message",
  "status": "error"
}
```

### HTTP Status Codes
- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Interactive Documentation
FastAPI provides auto-generated interactive docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Images API

Base path: `/api/images`

### List All Images

**Endpoint**: `GET /api/images`

**Description**: Get paginated list of all images

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 20 | Items per page |
| `status` | string | No | all | Filter by status (pending/approved/rejected) |

**Response**:
```json
{
  "images": [
    {
      "id": 1,
      "filename": "cat_001.jpg",
      "width": 640,
      "height": 480,
      "file_path": "data/images/cat_001.jpg",
      "status": "pending",
      "created_at": "2025-10-03T12:34:56",
      "annotation_count": 3
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

**Example**:
```bash
curl http://localhost:8000/api/images?page=1&per_page=10
```

---

### Get Single Image

**Endpoint**: `GET /api/images/{image_id}`

**Description**: Get detailed information about a specific image

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Response**:
```json
{
  "id": 1,
  "filename": "cat_001.jpg",
  "width": 640,
  "height": 480,
  "file_path": "data/images/cat_001.jpg",
  "status": "pending",
  "created_at": "2025-10-03T12:34:56",
  "annotations": [
    {
      "id": 101,
      "category_id": 17,
      "category_name": "cat",
      "bbox": [120, 80, 200, 150],
      "confidence": 0.92
    }
  ]
}
```

**Errors**:
- `404` - Image not found

---

### Create Image

**Endpoint**: `POST /api/images`

**Description**: Register a new image in the database

**Request Body**:
```json
{
  "filename": "dog_001.jpg",
  "width": 800,
  "height": 600,
  "file_path": "data/images/dog_001.jpg"
}
```

**Response**: `201 Created`
```json
{
  "id": 2,
  "filename": "dog_001.jpg",
  "width": 800,
  "height": 600,
  "file_path": "data/images/dog_001.jpg",
  "status": "pending",
  "created_at": "2025-10-03T13:00:00"
}
```

**Errors**:
- `400` - Invalid data (missing fields, invalid dimensions)
- `409` - Filename already exists

---

### Update Image

**Endpoint**: `PUT /api/images/{image_id}`

**Description**: Update image metadata or status

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Request Body** (all fields optional):
```json
{
  "status": "approved"
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "filename": "cat_001.jpg",
  "status": "approved",
  ...
}
```

**Errors**:
- `404` - Image not found
- `400` - Invalid status value

---

### Delete Image

**Endpoint**: `DELETE /api/images/{image_id}`

**Description**: Delete an image and all its annotations

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Response**: `204 No Content`

**Errors**:
- `404` - Image not found

**Note**: This CASCADE deletes all associated annotations

---

## Annotations API

Base path: `/api/annotations`

### Get Annotations for Image

**Endpoint**: `GET /api/annotations/{image_id}`

**Description**: Get all annotations for a specific image

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Response**:
```json
[
  {
    "id": 101,
    "image_id": 1,
    "category_id": 17,
    "category_name": "cat",
    "bbox": [120, 80, 200, 150],
    "points": null,
    "area": 30000.0,
    "confidence": 0.92,
    "status": "pending"
  },
  {
    "id": 102,
    "image_id": 1,
    "category_id": 17,
    "category_name": "cat",
    "bbox": null,
    "points": [[120,80], [320,80], [320,230], [120,230]],
    "area": 30000.0,
    "confidence": 0.88,
    "status": "pending"
  }
]
```

---

### Create Annotation

**Endpoint**: `POST /api/annotations`

**Description**: Create a new annotation

**Request Body** (Bounding Box):
```json
{
  "image_id": 1,
  "category_id": 17,
  "category_name": "cat",
  "bbox": [120, 80, 200, 150],
  "confidence": 0.95
}
```

**Request Body** (Polygon):
```json
{
  "image_id": 1,
  "category_id": 17,
  "category_name": "cat",
  "points": [[120,80], [320,80], [320,230], [120,230]],
  "confidence": 0.88
}
```

**Response**: `201 Created`
```json
{
  "id": 103,
  "image_id": 1,
  "category_id": 17,
  "category_name": "cat",
  "bbox": [120, 80, 200, 150],
  "confidence": 0.95,
  "status": "pending",
  "created_at": "2025-10-03T13:30:00"
}
```

**Validation Rules**:
- Either `bbox` OR `points` must be provided (not both)
- `bbox`: 4-element array [x, y, width, height]
- `points`: Array of [x, y] coordinates
- `confidence`: 0.0 to 1.0
- `category_id` and `category_name` are required

---

### Update Annotation

**Endpoint**: `PUT /api/annotations/{annotation_id}`

**Description**: Update an existing annotation

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `annotation_id` | integer | Yes | Annotation ID |

**Request Body** (any fields):
```json
{
  "bbox": [125, 85, 195, 145],
  "confidence": 0.98,
  "status": "approved"
}
```

**Response**: `200 OK`
```json
{
  "id": 103,
  "bbox": [125, 85, 195, 145],
  "confidence": 0.98,
  "status": "approved",
  ...
}
```

---

### Delete Annotation

**Endpoint**: `DELETE /api/annotations/{annotation_id}`

**Description**: Delete a specific annotation

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `annotation_id` | integer | Yes | Annotation ID |

**Response**: `204 No Content`

**Errors**:
- `404` - Annotation not found

---

## Review API

Base path: `/api/review`

### Get Review Queue

**Endpoint**: `GET /api/review/queue`

**Description**: Get images pending review, ordered by creation date

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Number of images |

**Response**:
```json
{
  "queue": [
    {
      "id": 1,
      "filename": "cat_001.jpg",
      "status": "pending",
      "annotation_count": 3,
      "created_at": "2025-10-03T12:34:56"
    }
  ],
  "total_pending": 45
}
```

---

### Approve Image

**Endpoint**: `POST /api/review/{image_id}/approve`

**Description**: Mark image as approved

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Response**: `200 OK`
```json
{
  "message": "Image approved",
  "image_id": 1,
  "status": "approved"
}
```

---

### Reject Image

**Endpoint**: `POST /api/review/{image_id}/reject`

**Description**: Mark image as rejected

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | integer | Yes | Image ID |

**Response**: `200 OK`
```json
{
  "message": "Image rejected",
  "image_id": 1,
  "status": "rejected"
}
```

---

## Export API

Base path: `/api/export`

### Get Export Formats

**Endpoint**: `GET /api/export/formats`

**Description**: List available export formats

**Response**:
```json
{
  "formats": [
    {
      "name": "COCO",
      "description": "MS COCO JSON format",
      "file_extension": ".json",
      "mime_type": "application/json"
    },
    {
      "name": "YOLO",
      "description": "YOLO TXT format",
      "file_extension": ".zip",
      "mime_type": "application/zip"
    },
    {
      "name": "Pascal VOC",
      "description": "Pascal VOC XML format",
      "file_extension": ".zip",
      "mime_type": "application/zip"
    }
  ]
}
```

---

### Get Export Statistics

**Endpoint**: `GET /api/export/statistics`

**Description**: Get dataset statistics before export

**Response**:
```json
{
  "total_images": 100,
  "total_annotations": 350,
  "images_by_status": {
    "pending": 45,
    "approved": 50,
    "rejected": 5
  },
  "category_distribution": [
    {"id": 17, "name": "cat", "count": 120},
    {"id": 18, "name": "dog", "count": 95},
    {"id": 1, "name": "person", "count": 135}
  ]
}
```

---

### Export COCO Format

**Endpoint**: `GET /api/export/coco`

**Description**: Export dataset in COCO JSON format

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `split` | string | No | all | all/approved/train/val/test |

**Response**: `200 OK`
- Content-Type: `application/json`
- Disposition: `attachment; filename="annotations_coco.json"`

**COCO Format**:
```json
{
  "info": {
    "description": "YOLO Dataset Builder Export",
    "version": "1.0",
    "date_created": "2025-10-03"
  },
  "images": [
    {
      "id": 1,
      "file_name": "cat_001.jpg",
      "width": 640,
      "height": 480
    }
  ],
  "annotations": [
    {
      "id": 101,
      "image_id": 1,
      "category_id": 17,
      "bbox": [120, 80, 200, 150],
      "area": 30000,
      "iscrowd": 0
    }
  ],
  "categories": [
    {
      "id": 17,
      "name": "cat",
      "supercategory": "animal"
    }
  ]
}
```

---

### Export YOLO Format

**Endpoint**: `GET /api/export/yolo`

**Description**: Export dataset in YOLO format (ZIP file)

**Response**: `200 OK`
- Content-Type: `application/zip`
- Disposition: `attachment; filename="yolo_export.zip"`

**ZIP Contents**:
```
yolo_export.zip
├── labels/
│   ├── cat_001.txt
│   ├── dog_001.txt
│   └── ...
├── classes.txt
└── data.yaml
```

**Label File Format** (`labels/cat_001.txt`):
```
0 0.5 0.4 0.3 0.3
1 0.7 0.6 0.2 0.25
```
Format: `<class_id> <x_center> <y_center> <width> <height>` (normalized 0-1)

**classes.txt**:
```
person
bicycle
car
...
```

**data.yaml**:
```yaml
names: ['person', 'bicycle', 'car', ...]
nc: 80
```

---

### Export Pascal VOC Format

**Endpoint**: `GET /api/export/voc`

**Description**: Export dataset in Pascal VOC XML format (ZIP file)

**Response**: `200 OK`
- Content-Type: `application/zip`
- Disposition: `attachment; filename="voc_export.zip"`

**ZIP Contents**:
```
voc_export.zip
└── annotations/
    ├── cat_001.xml
    ├── dog_001.xml
    └── ...
```

**XML Format** (`cat_001.xml`):
```xml
<annotation>
  <folder>images</folder>
  <filename>cat_001.jpg</filename>
  <size>
    <width>640</width>
    <height>480</height>
    <depth>3</depth>
  </size>
  <object>
    <name>cat</name>
    <pose>Unspecified</pose>
    <truncated>0</truncated>
    <difficult>0</difficult>
    <bndbox>
      <xmin>120</xmin>
      <ymin>80</ymin>
      <xmax>320</xmax>
      <ymax>230</ymax>
    </bndbox>
  </object>
</annotation>
```

---

## Templates API

Base path: `/api/templates`

### List Templates

**Endpoint**: `GET /api/templates`

**Description**: Get all annotation templates

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | null | Filter by category |
| `template_type` | string | No | null | Filter by type (bbox/polygon) |

**Response**:
```json
[
  {
    "id": 1,
    "name": "Person Standing (Medium)",
    "description": "Standard person standing",
    "category": "person",
    "template_type": "bbox",
    "bbox_data": {
      "x": 0,
      "y": 0,
      "width": 80,
      "height": 200,
      "unit": "absolute"
    },
    "polygon_data": null,
    "confidence": 0.9,
    "usage_count": 47,
    "created_at": "2025-10-01T10:00:00"
  }
]
```

---

### Get Template

**Endpoint**: `GET /api/templates/{template_id}`

**Description**: Get a specific template

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | integer | Yes | Template ID |

**Response**: `200 OK` (same as list item)

**Errors**:
- `404` - Template not found

---

### Create Template

**Endpoint**: `POST /api/templates`

**Description**: Create a new annotation template

**Request Body** (Bounding Box):
```json
{
  "name": "Car Side View Small",
  "description": "Small car from side",
  "category": "car",
  "template_type": "bbox",
  "bbox_data": {
    "x": 0,
    "y": 0,
    "width": 120,
    "height": 80,
    "unit": "absolute"
  },
  "confidence": 0.95
}
```

**Request Body** (Polygon):
```json
{
  "name": "Custom Polygon",
  "category": "person",
  "template_type": "polygon",
  "polygon_data": {
    "points": [[0,0], [50,0], [50,100], [0,100]],
    "unit": "absolute"
  },
  "confidence": 0.9
}
```

**Response**: `201 Created`
```json
{
  "id": 9,
  "name": "Car Side View Small",
  ...
}
```

**Validation**:
- `name` required
- `category` required
- `template_type` must be "bbox" or "polygon"
- Corresponding data field (`bbox_data` or `polygon_data`) required

---

### Update Template

**Endpoint**: `PUT /api/templates/{template_id}`

**Description**: Update template metadata (not dimensions)

**Request Body**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "confidence": 0.92
}
```

**Response**: `200 OK`

**Note**: Cannot change `template_type` or dimension data after creation

---

### Delete Template

**Endpoint**: `DELETE /api/templates/{template_id}`

**Description**: Delete a template

**Response**: `204 No Content`

---

### Increment Template Usage

**Endpoint**: `POST /api/templates/{template_id}/use`

**Description**: Increment usage counter (called when template is applied)

**Response**: `200 OK`
```json
{
  "message": "Usage count incremented"
}
```

---

### Get Template Categories

**Endpoint**: `GET /api/templates/categories/list`

**Description**: Get list of all unique categories in templates

**Response**:
```json
{
  "categories": ["person", "car", "dog", "cat", "bicycle"]
}
```

---

## SAM API

Base path: `/api/sam`

### Generate SAM Mask

**Endpoint**: `POST /api/sam/generate`

**Description**: Generate segmentation mask using SAM model

**Request Body**:
```json
{
  "image_path": "data/images/cat_001.jpg",
  "points": [
    {"x": 320, "y": 240, "label": 1},
    {"x": 100, "y": 100, "label": 0}
  ],
  "box": null
}
```

**Point Labels**:
- `1` - Foreground (include this)
- `0` - Background (exclude this)

**Response**: `200 OK`
```json
{
  "mask": "iVBORw0KGgoAAAANSUhEUgAA...", // Base64 PNG
  "polygon": [[120,80], [320,80], ...],
  "confidence": 0.92
}
```

**Errors**:
- `404` - Image not found
- `501` - SAM model not configured
- `500` - SAM generation failed

---

### Generate Mock SAM Mask

**Endpoint**: `POST /api/sam/generate-mock`

**Description**: Generate mock segmentation for testing (circular polygon)

**Request Body**:
```json
{
  "image_path": "data/images/cat_001.jpg",
  "points": [
    {"x": 320, "y": 240, "label": 1}
  ]
}
```

**Response**: `200 OK` (same format as real SAM)

**Use Case**: Testing SAM UI without model weights

---

### Get SAM Status

**Endpoint**: `GET /api/sam/status`

**Description**: Check SAM integration status

**Response**:
```json
{
  "mode": "api",
  "available": false,
  "model_loaded": false,
  "api_configured": false,
  "dependencies_installed": true
}
```

**Status Fields**:
- `mode`: "api" or "local"
- `available`: Whether SAM is ready to use
- `model_loaded`: (local mode) Model weights loaded
- `api_configured`: (api mode) API key configured
- `dependencies_installed`: Python packages installed

---

## Error Handling

### Error Response Format

All errors return JSON:
```json
{
  "detail": "Error message describing what went wrong",
  "status": "error"
}
```

### Common Error Codes

#### 400 Bad Request
**Causes**:
- Missing required fields
- Invalid data types
- Validation errors

**Example**:
```json
{
  "detail": "Validation error: confidence must be between 0 and 1",
  "status": "error"
}
```

#### 404 Not Found
**Causes**:
- Resource doesn't exist
- Invalid ID

**Example**:
```json
{
  "detail": "Image with id 999 not found",
  "status": "error"
}
```

#### 500 Internal Server Error
**Causes**:
- Database errors
- Unexpected exceptions
- Model inference failures

**Example**:
```json
{
  "detail": "Internal server error",
  "status": "error"
}
```

### Validation Errors (422)

Pydantic validation errors return detailed info:
```json
{
  "detail": [
    {
      "loc": ["body", "confidence"],
      "msg": "ensure this value is less than or equal to 1.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Examples

### Complete Annotation Workflow

```bash
# 1. List images
curl http://localhost:8000/api/images

# 2. Get specific image
curl http://localhost:8000/api/images/1

# 3. Create annotation
curl -X POST http://localhost:8000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "image_id": 1,
    "category_id": 17,
    "category_name": "cat",
    "bbox": [120, 80, 200, 150],
    "confidence": 0.95
  }'

# 4. Update annotation
curl -X PUT http://localhost:8000/api/annotations/101 \
  -H "Content-Type: application/json" \
  -d '{
    "confidence": 0.98,
    "status": "approved"
  }'

# 5. Approve image
curl -X POST http://localhost:8000/api/review/1/approve

# 6. Export to COCO
curl http://localhost:8000/api/export/coco > annotations.json
```

### Using Templates

```bash
# List templates
curl http://localhost:8000/api/templates

# Create template
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Person Small",
    "category": "person",
    "template_type": "bbox",
    "bbox_data": {
      "width": 40,
      "height": 100,
      "unit": "absolute"
    }
  }'

# Track usage
curl -X POST http://localhost:8000/api/templates/1/use
```

### SAM Integration

```bash
# Check SAM status
curl http://localhost:8000/api/sam/status

# Generate mock mask
curl -X POST http://localhost:8000/api/sam/generate-mock \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "data/images/cat_001.jpg",
    "points": [{"x": 320, "y": 240, "label": 1}]
  }'
```

---

## Rate Limiting

**Current**: No rate limiting
**Future**: 100 requests/minute per IP

---

## Versioning

**Current Version**: v1
**API Path**: `/api/...` (no version prefix yet)
**Future**: `/api/v2/...` when breaking changes occur

---

## CORS

**Allowed Origins**:
```
http://localhost:5173
http://localhost:3000
```

**Allowed Methods**: All
**Allowed Headers**: All

Production: Configure specific domain

---

**Document Status**: ✅ Complete
**Last Updated**: October 2025
**Interactive Docs**: http://localhost:8000/docs
