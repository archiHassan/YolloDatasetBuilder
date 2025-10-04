# User Guide
## YOLO Dataset Builder - Complete User Manual

**Version**: 1.0
**Last Updated**: October 2025
**Target Audience**: Annotators, Dataset Creators, ML Engineers

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Image Management](#image-management)
3. [Annotation Workflow](#annotation-workflow)
4. [Review Process](#review-process)
5. [Using Templates](#using-templates)
6. [SAM Auto-Segmentation](#sam-auto-segmentation)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Exporting Datasets](#exporting-datasets)
9. [Tips & Best Practices](#tips-best-practices)

---

## Getting Started

### Accessing the Application

**Development Mode**:
```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

**Production Mode**:
```
Application: http://your-domain.com
```

### First Login
Currently, there is no authentication. Simply navigate to the URL and start working.

### Main Interface Overview
```
┌─────────────────────────────────────────────────┐
│  YOLO Dataset Builder                    [Docs] │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Home] [Statistics]                           │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Image 1 │ │  Image 2 │ │  Image 3 │       │
│  │  [View]  │ │  [View]  │ │  [View]  │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│                                                 │
│  [< Prev]  Page 1 of 5  [Next >]              │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Image Management

### Uploading Images

#### Manual Upload
1. Navigate to the data directory: `data/images/`
2. Copy your images to this folder
3. Refresh the web interface
4. Images will appear in the gallery

#### Batch Upload (Future Feature)
- Drag and drop multiple images
- Upload from ZIP file
- Import from URL

### Viewing Image Gallery

**Image Gallery Features**:
- **Grid View**: See multiple images at once
- **Pagination**: Navigate through pages
- **Status Badges**:
  - 🟡 Pending (not reviewed)
  - 🟢 Approved (reviewed and accepted)
  - 🔴 Rejected (reviewed and rejected)

**Gallery Actions**:
- Click image → Open viewer
- Click "View" button → Open annotation editor

### Image Information
Each image card shows:
- Filename
- Dimensions (width × height)
- Annotation count
- Review status

---

## Annotation Workflow

### Opening the Annotation Editor

1. From the gallery, click any image
2. You'll see the annotation editor with the image loaded
3. Existing annotations (if any) are displayed as overlays

### Editor Interface

```
┌────────────────────────────────────────────────┐
│ Toolbar: [View] [Draw] [Batch] [SAM] [...]    │
├────────────────────────────────────────────────┤
│                                                │
│           [Image with Annotations]             │
│                                                │
│                                                │
├────────────────────────────────────────────────┤
│ Annotation List:                               │
│ ☑ person (95%)                                 │
│ ☐ car (88%)                                    │
└────────────────────────────────────────────────┘
```

### Annotation Modes

#### 1. View Mode (👁 View)
**Purpose**: Inspect and select annotations

**Actions**:
- Click annotation → Select it
- Drag annotation → Move it
- Drag handles → Resize bounding box
- Delete key → Remove annotation

**Visual Feedback**:
- Selected annotation: Black border (thicker)
- Unselected: Colored border (category color)
- Resize handles: Black squares at corners

#### 2. Draw Mode (✏ Draw)
**Purpose**: Create new annotations

**Bounding Box (Rectangle)**:
1. Click "Draw" button
2. Select "Rectangle" mode
3. Choose category from dropdown
4. Click and drag on image to draw box
5. Release to create annotation
6. Automatically returns to View mode

**Polygon**:
1. Click "Draw" button
2. Select "Polygon" mode
3. Choose category
4. Click points to create polygon vertices
5. Click first point (green) to close polygon
6. Polygon is created

**Canceling**:
- Press `Esc` to cancel drawing
- Click "View" to exit Draw mode

#### 3. Batch Mode (☑ Batch)
**Purpose**: Select and modify multiple annotations

**Usage**:
1. Click "Batch" button
2. Click annotations to select them (checkboxes appear)
3. Use batch operations:
   - Change category for all selected
   - Delete all selected
   - `Ctrl+A` to select all

**Visual Feedback**:
- Selected annotations have checkboxes
- Batch controls appear in toolbar

#### 4. SAM Mode (🎯 SAM)
**Purpose**: Auto-segment objects using AI

**Usage**:
1. Click "SAM" button
2. Click on the object you want to segment
3. Wait for processing (~2 seconds)
4. Polygon annotation is created automatically
5. Edit polygon if needed

**Advanced**:
- `Shift+Click` → Mark background (exclude area)
- Multiple clicks → Refine segmentation

---

## Annotation Types

### Bounding Box
**Format**: Rectangle defined by `[x, y, width, height]`

**Best For**:
- Objects with rectangular shapes
- Quick annotation
- Standard object detection

**Creating**:
- Draw mode → Rectangle → Click & drag

**Editing**:
- Select → Drag to move
- Select → Drag corners to resize

### Polygon
**Format**: Series of points `[[x1,y1], [x2,y2], ...]`

**Best For**:
- Irregular shaped objects
- Precise boundaries
- Instance segmentation

**Creating**:
- Draw mode → Polygon → Click points → Close
- SAM mode → Click object

**Editing**:
- Select → Drag entire polygon
- Select → Drag individual points

### Converting Between Types
1. Select annotation
2. Click "⬡ To Polygon" or "▭ To BBox"
3. Annotation is converted

---

## Review Process

### Review Workflow

```
Upload → Auto-Annotate → Review → Export
            │              │
            └─────────────┘
              (Pending)
```

### Reviewing an Image

1. **Open image** in annotation editor
2. **Inspect annotations**:
   - Check if objects are correctly labeled
   - Verify bounding boxes are accurate
   - Look for missed objects
3. **Edit if needed**:
   - Add missing annotations
   - Delete incorrect ones
   - Adjust boundaries
4. **Approve or Reject**:
   - Click "✓ Approve" if good
   - Click "✗ Reject" if needs work

### Review Status

**Pending** (🟡):
- Newly uploaded or auto-annotated
- Needs human review

**Approved** (🟢):
- Reviewed and accepted
- Ready for export

**Rejected** (🔴):
- Needs corrections
- Not included in exports

### Review Queue

Access via "Statistics" page:
- Shows count of pending/approved/rejected
- Filter by status
- Priority queue (oldest first)

---

## Using Templates

### What are Templates?

Templates are pre-defined annotation shapes you can quickly apply to images, saving time on repetitive objects.

### Viewing Templates

1. Click "📐 Templates" button in annotation editor
2. Template Manager opens
3. Browse available templates

### Applying a Template

1. Open Template Manager
2. Find desired template (e.g., "Person Standing Medium")
3. Click "Apply" button
4. Template annotation appears at image center
5. Drag to position it correctly
6. Edit size if needed

### Creating Custom Templates

1. Open Template Manager
2. Click "+ New Template"
3. Fill form:
   - **Name**: Descriptive name (e.g., "Car Side View Small")
   - **Category**: Object type (e.g., "car")
   - **Type**: Bounding Box or Polygon
   - **Dimensions**: Width and height in pixels
   - **Confidence**: Default confidence (0.0-1.0)
4. Click "Create"

### Template Features

**Default Templates** (8 included):
- Person Standing (Small, Medium, Large)
- Car Side View
- Car Front/Rear View
- Dog Standing
- Cat Sitting
- Bicycle Side View

**Template Management**:
- Edit existing templates
- Delete unused templates
- Track usage count (most used appear first)

---

## SAM Auto-Segmentation

### What is SAM?

SAM (Segment Anything Model) is an AI that can automatically segment any object you click on, creating precise polygon annotations.

### Using SAM

#### Basic Usage
1. Click "🎯 SAM" button
2. Click on the object center
3. Wait 1-3 seconds
4. Polygon annotation is created

#### Advanced Usage

**Foreground Points** (include this object):
- Normal click on object

**Background Points** (exclude this area):
- `Shift+Click` on areas to exclude

**Example**:
```
To segment a person:
1. Click person's torso (foreground)
2. Shift+click background behind person
3. SAM generates precise outline
```

### SAM Modes

**Mock Mode** (Current):
- Generates circular polygon for testing
- Fast response (~100ms)
- No model weights needed

**Real Mode** (After setup):
- Uses actual SAM model
- Precise segmentation
- Slower (~2 seconds)

### Enabling Real SAM

See [Production Deployment Guide](../development/PRODUCTION_READY.md) for SAM setup instructions.

---

## Keyboard Shortcuts

### Essential Shortcuts (Top 10)

| Shortcut | Action |
|----------|--------|
| `Esc` | Cancel/Exit current mode |
| `Delete` | Delete selected annotation |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Y` | Redo action |
| `Ctrl+S` | Save changes |
| `C` | Copy selected annotation |
| `X` | Cut selected annotation |
| `Ctrl+V` | Paste annotation |
| `Space` | Toggle annotation visibility |
| `?` | Show help/shortcuts |

### All Shortcuts (20+)

#### General
- `Esc` - Cancel current operation, exit mode
- `?` - Show keyboard shortcuts help
- `Space` - Toggle annotation visibility on/off
- `Ctrl+S` - Save changes to database

#### Undo/Redo
- `Ctrl+Z` - Undo last action
- `Ctrl+Y` - Redo (or `Ctrl+Shift+Z`)

#### Selection
- `Tab` - Cycle through annotations (next)
- `Shift+Tab` - Cycle backwards through annotations
- Click annotation - Select it

#### Editing
- `Delete` or `Backspace` - Delete selected annotation
- `C` - Copy selected annotation
- `X` - Cut selected annotation (copy + delete)
- `Ctrl+V` - Paste annotation
- `Ctrl+D` - Duplicate selected annotation

#### Movement (with annotation selected)
- `←` - Move annotation left 1px
- `→` - Move annotation right 1px
- `↑` - Move annotation up 1px
- `↓` - Move annotation down 1px
- `Shift+Arrow` - Move 10px in that direction

#### Confidence Adjustment
- `+` or `=` - Increase confidence by 0.1
- `-` or `_` - Decrease confidence by 0.1

#### Modes
- `V` - Switch to View mode
- `Ctrl+D` - Switch to Draw mode
- `Ctrl+B` - Switch to Batch mode
- `R` - Rectangle tool (in Draw mode)
- `P` - Polygon tool (in Draw mode)

#### Category Selection (in Draw mode)
- `1` - Select category 1 (person)
- `2` - Select category 2 (car)
- `3` - Select category 3 (dog)
- ... up to `9` - Select category 9

#### Batch Mode
- `Ctrl+A` - Select all annotations
- Click annotations - Toggle selection

### Keyboard Shortcut Tips

1. **Shortcuts disabled in text fields** - They won't interfere with typing
2. **Context-aware** - Some shortcuts only work in specific modes
3. **Press `?` anytime** - See the help modal with all shortcuts
4. **Combination shortcuts** - Hold `Ctrl` or `Shift` for combos

---

## Exporting Datasets

### Export Formats

The system supports 3 major dataset formats:

#### 1. COCO Format (JSON)
**Best for**: PyTorch, Detectron2, MMDetection

**Output**:
- `annotations_coco.json` - Single JSON file
- Contains images, annotations, categories

**Structure**:
```json
{
  "images": [...],
  "annotations": [...],
  "categories": [...]
}
```

#### 2. YOLO Format (TXT + ZIP)
**Best for**: YOLOv5, YOLOv8, Ultralytics

**Output**:
- `yolo_export.zip` containing:
  - `labels/*.txt` - One file per image
  - `classes.txt` - Category names
  - `data.yaml` - Configuration file

**Label Format** (per line):
```
<class_id> <x_center> <y_center> <width> <height>
```
All values normalized (0-1)

#### 3. Pascal VOC Format (XML + ZIP)
**Best for**: TensorFlow Object Detection API

**Output**:
- `voc_export.zip` containing:
  - `annotations/*.xml` - One XML per image

**XML Structure**:
```xml
<annotation>
  <object>
    <name>cat</name>
    <bndbox>
      <xmin>120</xmin>
      <ymin>80</ymin>
      <xmax>320</xmax>
      <ymax>230</ymax>
    </bndbox>
  </object>
</annotation>
```

### How to Export

#### Via Statistics Page

1. Navigate to "Statistics" page
2. Scroll to "Export Dataset" section
3. Click desired format button:
   - "Export COCO" → Downloads JSON
   - "Export YOLO" → Downloads ZIP
   - "Export Pascal VOC" → Downloads ZIP
4. File downloads to browser's download folder

#### What Gets Exported

**Default**: All approved annotations
**Status filtering**: Only images with status = "approved"

To export specific subset:
1. Mark images as "approved"
2. Run export
3. Only approved images are included

### Export Statistics

Before exporting, check statistics:
- **Total Images**: How many images
- **Total Annotations**: How many annotations
- **By Category**: Distribution across categories
- **By Status**: Pending/Approved/Rejected counts

---

## Tips & Best Practices

### Annotation Quality

#### DO:
✅ **Be consistent** - Use same categories across images
✅ **Be precise** - Tight bounding boxes, accurate polygons
✅ **Label everything** - Don't miss objects
✅ **Use polygons for irregular objects** - Better than bboxes
✅ **Review your work** - Always check before approving
✅ **Use templates** - Speed up repetitive objects

#### DON'T:
❌ **Don't rush** - Quality over speed
❌ **Don't leave gaps** - Label all visible objects
❌ **Don't use wrong categories** - Double-check labels
❌ **Don't make huge boxes** - Keep them tight
❌ **Don't forget confidence** - Adjust if uncertain

### Workflow Optimization

#### For Speed:
1. **Use keyboard shortcuts** - Learn the top 10
2. **Use templates** - For common objects
3. **Use SAM** - For complex shapes
4. **Batch operations** - Group similar edits
5. **Copy/paste** - Duplicate similar annotations

#### For Quality:
1. **Zoom in** - Check details
2. **Toggle visibility** - See image without annotations (`Space`)
3. **Review twice** - First pass quick, second pass careful
4. **Use polygon mode** - For precise boundaries
5. **Adjust confidence** - Reflect your certainty

### Common Workflows

#### New Dataset from Scratch
```
1. Upload images → data/images/
2. Run auto-annotation (backend pipeline)
3. Review each image in web interface
4. Fix/add/delete annotations
5. Approve when satisfied
6. Export to desired format
```

#### Correcting Auto-Annotations
```
1. Open image in editor
2. Check each annotation
3. Delete false positives
4. Add missed objects (Draw mode)
5. Adjust boundaries (drag)
6. Save and approve
```

#### Creating Templates
```
1. Annotate one perfect example
2. Note dimensions (e.g., 80×200)
3. Create template with those dimensions
4. Use template on similar objects
5. Adjust position/size as needed
```

---

## Troubleshooting

### Common Issues

#### Images not appearing
**Problem**: Uploaded images don't show in gallery
**Solution**:
- Check files are in `data/images/`
- Refresh browser
- Check file formats (JPG, PNG supported)
- Check backend server is running

#### Annotations not saving
**Problem**: Changes disappear after refresh
**Solution**:
- Always click "💾 Save" button
- Check for error messages
- Verify backend connection
- Check browser console for errors

#### SAM not working
**Problem**: Clicking doesn't generate polygon
**Solution**:
- Check backend is running
- Currently using mock SAM (generates circles)
- For real SAM, download model weights
- Check console for error messages

#### Slow performance
**Problem**: Interface is laggy
**Solution**:
- Reduce number of annotations per image
- Close other browser tabs
- Clear browser cache
- Restart backend server

### Getting Help

1. **Check API Docs**: http://localhost:8000/docs
2. **Check Backend Logs**: Terminal where server is running
3. **Check Browser Console**: F12 → Console tab
4. **Check GitHub Issues**: Report bugs there

---

## Appendix

### Supported Image Formats
- JPG/JPEG
- PNG
- BMP
- TIFF

### Browser Compatibility
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

Minimum: Modern browser with ES6 support

### System Requirements

**Client**:
- Modern web browser
- 4GB RAM minimum
- Internet connection (or local network)

**Server**:
- 8GB RAM minimum (for AI models)
- 10GB disk space
- Python 3.11+

---

## Glossary

**Annotation**: Label/box/polygon marking an object in an image

**Bounding Box (BBox)**: Rectangle around an object

**Category**: Type of object (person, car, dog, etc.)

**COCO Format**: Common Objects in Context - standard JSON format

**Confidence**: Probability/certainty score (0.0-1.0)

**Polygon**: Multi-point shape (more precise than bbox)

**SAM**: Segment Anything Model - AI for auto-segmentation

**Template**: Reusable pre-defined annotation shape

**YOLO**: You Only Look Once - object detection framework

---

**Document Status**: ✅ Complete
**Last Updated**: October 2025
**For Support**: See GitHub Issues
