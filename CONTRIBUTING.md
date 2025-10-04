# Contributing to YOLO Dataset Builder

Thank you for your interest in contributing to YOLO Dataset Builder! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/yolo-dataset-builder.git
   cd yolo-dataset-builder
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/yolo-dataset-builder.git
   ```

## Development Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Running Development Servers

**Backend** (in `backend/` directory):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (in `frontend/` directory):
```bash
npm run dev
```

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Include a clear title and description
- Provide steps to reproduce the bug
- Include screenshots if applicable
- Specify your environment (OS, Python version, Node version)

### Suggesting Features

- Use the GitHub issue tracker with the "enhancement" label
- Clearly describe the feature and its use case
- Explain why this feature would be useful

### Contributing Code

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes** thoroughly

4. **Commit your changes** with clear, descriptive messages

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Document functions and classes with docstrings
- Keep functions focused and concise
- Use Pydantic models for data validation

**Example**:
```python
from typing import List, Optional
from pydantic import BaseModel

def get_image_by_id(image_id: int) -> Optional[dict]:
    """
    Retrieve an image by its ID.

    Args:
        image_id: The unique identifier of the image

    Returns:
        dict: Image data if found, None otherwise
    """
    # Implementation
    pass
```

### JavaScript/React (Frontend)

- Use functional components with hooks
- Follow ESLint configuration
- Use meaningful variable and function names
- Keep components focused and reusable
- Use PropTypes or TypeScript for type safety

**Example**:
```jsx
import { useState, useEffect } from 'react';

const ImageGallery = ({ onImageSelect }) => {
  const [images, setImages] = useState([]);

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    // Implementation
  };

  return (
    // JSX
  );
};

export default ImageGallery;
```

### File Organization

- **Backend**: Keep related functionality in separate modules under `app/api/`
- **Frontend**: Keep components in `src/components/`, utilities in `src/utils/`
- **Tests**: Mirror the structure of the code being tested

## Commit Guidelines

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat: Add batch annotation mode to editor

Implement batch annotation functionality that allows users to
apply the same label to multiple images efficiently.

Closes #123
```

```
fix: Resolve CORS issue in production deployment

Update nginx configuration to properly handle CORS headers
for API requests from the frontend.
```

### Best Practices

- Use present tense ("Add feature" not "Added feature")
- Keep subject line under 50 characters
- Capitalize the subject line
- Don't end subject line with a period
- Use the body to explain what and why, not how
- Reference issues and pull requests in the footer

## Pull Request Process

1. **Update documentation** if you've changed APIs or added features
2. **Add tests** for new functionality
3. **Ensure all tests pass**:
   ```bash
   # Backend tests
   python scripts/test-api.py

   # Frontend tests
   npm test
   ```
4. **Update CHANGELOG.md** with your changes
5. **Fill out the PR template** completely
6. **Request review** from maintainers
7. **Address review feedback** promptly
8. **Squash commits** if requested before merging

### PR Title Format

Follow the same format as commit messages:
```
feat: Add SAM integration for auto-segmentation
fix: Resolve image upload validation error
```

## Testing

### Backend Testing

Run the API test suite:
```bash
python scripts/test-api.py
```

Quick smoke test:
```bash
python scripts/quick-test.py
```

### Frontend Testing

```bash
npm test
npm run lint
```

### Manual Testing Checklist

- [ ] Upload images successfully
- [ ] Create annotations in all modes (View, Draw, Batch, SAM)
- [ ] Review and approve/reject annotations
- [ ] Export datasets in all formats (COCO, YOLO, VOC)
- [ ] Template management works correctly
- [ ] Statistics dashboard displays correctly

## Project Structure

```
yolo-dataset-builder/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API route modules
│   │   ├── db/          # Database utilities
│   │   ├── config.py    # Configuration
│   │   └── main.py      # App entry point
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── api/         # API client
│   │   └── hooks/       # Custom hooks
│   └── package.json
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── docker-compose.yml   # Docker orchestration
```

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Reach out to maintainers
- Check existing documentation in the `docs/` folder

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to YOLO Dataset Builder! 🚀
