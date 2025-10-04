#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Testing Script for YOLO Dataset Builder
Tests all 22 API endpoints to verify functionality
"""

import requests
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
BASE_URL = "http://localhost:8000"
VERBOSE = True

# Test statistics
tests_passed = 0
tests_failed = 0
tests_skipped = 0

def print_test(name, status, message=""):
    """Print test result with color coding"""
    global tests_passed, tests_failed, tests_skipped

    if status == "PASS":
        tests_passed += 1
        symbol = "✓"
        color = "\033[92m"  # Green
    elif status == "FAIL":
        tests_failed += 1
        symbol = "✗"
        color = "\033[91m"  # Red
    else:  # SKIP
        tests_skipped += 1
        symbol = "⊘"
        color = "\033[93m"  # Yellow

    reset = "\033[0m"
    print(f"{color}{symbol} {name}{reset}")
    if message and VERBOSE:
        print(f"  {message}")

def test_endpoint(method, endpoint, data=None, expected_status=200, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            print_test(description, "SKIP", f"Unknown method: {method}")
            return None

        if response.status_code == expected_status:
            print_test(description, "PASS", f"{method} {endpoint} → {response.status_code}")
            return response
        else:
            print_test(description, "FAIL",
                      f"{method} {endpoint} → {response.status_code} (expected {expected_status})")
            if VERBOSE:
                print(f"  Response: {response.text[:200]}")
            return None

    except requests.exceptions.ConnectionError:
        print_test(description, "FAIL", f"Connection failed to {url}")
        return None
    except requests.exceptions.Timeout:
        print_test(description, "FAIL", f"Timeout connecting to {url}")
        return None
    except Exception as e:
        print_test(description, "FAIL", f"Error: {str(e)}")
        return None

def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("  YOLO Dataset Builder - API Testing")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # =========================================================================
    # 1. Health Check
    # =========================================================================
    print_header("1. Health Check")

    test_endpoint("GET", "/docs", expected_status=200,
                  description="GET /docs - API Documentation")

    # =========================================================================
    # 2. Images API (5 endpoints)
    # =========================================================================
    print_header("2. Images API (5 endpoints)")

    response = test_endpoint("GET", "/api/images", expected_status=200,
                            description="GET /api/images - List all images")

    # Check if we have any images
    has_images = False
    image_id = None
    if response:
        try:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                has_images = True
                image_id = data[0].get('id')
                print_test("Check: Images exist in database", "PASS",
                          f"Found {len(data)} image(s), first ID: {image_id}")
        except:
            pass

    if has_images and image_id:
        test_endpoint("GET", f"/api/images/{image_id}", expected_status=200,
                     description=f"GET /api/images/{image_id} - Get specific image")

        # Test update
        update_data = {"status": "pending"}
        test_endpoint("PUT", f"/api/images/{image_id}", data=update_data,
                     expected_status=200,
                     description=f"PUT /api/images/{image_id} - Update image")
    else:
        print_test("GET /api/images/{id} - Get specific image", "SKIP",
                  "No images in database")
        print_test("PUT /api/images/{id} - Update image", "SKIP",
                  "No images in database")

    # Test non-existent image
    test_endpoint("GET", "/api/images/99999", expected_status=404,
                 description="GET /api/images/99999 - Non-existent image (404)")

    # Delete endpoint (skip to avoid deleting data)
    print_test("DELETE /api/images/{id} - Delete image", "SKIP",
              "Skipped to preserve test data")

    # =========================================================================
    # 3. Annotations API (4 endpoints)
    # =========================================================================
    print_header("3. Annotations API (4 endpoints)")

    if has_images and image_id:
        response = test_endpoint("GET", f"/api/annotations/{image_id}",
                                expected_status=200,
                                description=f"GET /api/annotations/{image_id} - Get annotations for image")

        # Check if we have annotations
        annotation_id = None
        if response:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    annotation_id = data[0].get('id')
            except:
                pass

        # Test create annotation
        new_annotation = {
            "image_id": image_id,
            "category_id": 1,
            "category_name": "test",
            "bbox": [100, 100, 50, 50],
            "confidence": 0.95
        }
        create_response = test_endpoint("POST", "/api/annotations",
                                       data=new_annotation,
                                       expected_status=200,
                                       description="POST /api/annotations - Create annotation")

        if create_response:
            try:
                created = create_response.json()
                new_annotation_id = created.get('id')
                if new_annotation_id:
                    # Test update
                    update_data = {"confidence": 0.98}
                    test_endpoint("PUT", f"/api/annotations/{new_annotation_id}",
                                data=update_data, expected_status=200,
                                description=f"PUT /api/annotations/{new_annotation_id} - Update annotation")

                    # Test delete (clean up our test annotation)
                    test_endpoint("DELETE", f"/api/annotations/{new_annotation_id}",
                                expected_status=200,
                                description=f"DELETE /api/annotations/{new_annotation_id} - Delete annotation")
            except:
                print_test("Annotation CRUD operations", "FAIL",
                          "Failed to parse created annotation")
    else:
        print_test("Annotations API tests", "SKIP", "No images in database")

    # =========================================================================
    # 4. Review API (3 endpoints)
    # =========================================================================
    print_header("4. Review API (3 endpoints)")

    test_endpoint("GET", "/api/review/queue", expected_status=200,
                 description="GET /api/review/queue - Get review queue")

    if has_images and image_id:
        test_endpoint("POST", f"/api/review/{image_id}/approve",
                     expected_status=200,
                     description=f"POST /api/review/{image_id}/approve - Approve image")

        test_endpoint("POST", f"/api/review/{image_id}/reject",
                     expected_status=200,
                     description=f"POST /api/review/{image_id}/reject - Reject image")
    else:
        print_test("Review approve/reject", "SKIP", "No images in database")

    # =========================================================================
    # 5. Export API (5 endpoints)
    # =========================================================================
    print_header("5. Export API (5 endpoints)")

    test_endpoint("GET", "/api/export/formats", expected_status=200,
                 description="GET /api/export/formats - List export formats")

    test_endpoint("GET", "/api/export/statistics", expected_status=200,
                 description="GET /api/export/statistics - Export statistics")

    # Test COCO export
    response = test_endpoint("GET", "/api/export/coco?split=all",
                            expected_status=200,
                            description="GET /api/export/coco - Export COCO format")
    if response:
        try:
            coco_data = response.json()
            if 'images' in coco_data and 'annotations' in coco_data:
                print_test("COCO format validation", "PASS",
                          f"Valid COCO JSON with {len(coco_data.get('images', []))} images")
        except:
            print_test("COCO format validation", "FAIL", "Invalid JSON response")

    # YOLO and VOC exports return files, so we just check if they don't error
    test_endpoint("GET", "/api/export/yolo", expected_status=200,
                 description="GET /api/export/yolo - Export YOLO format")

    test_endpoint("GET", "/api/export/voc", expected_status=200,
                 description="GET /api/export/voc - Export Pascal VOC format")

    # =========================================================================
    # 6. Templates API (7 endpoints)
    # =========================================================================
    print_header("6. Templates API (7 endpoints)")

    response = test_endpoint("GET", "/api/templates", expected_status=200,
                            description="GET /api/templates - List templates")

    # Check if we have templates
    template_id = None
    if response:
        try:
            templates = response.json()
            if isinstance(templates, list) and len(templates) > 0:
                template_id = templates[0].get('id')
                print_test("Check: Templates exist", "PASS",
                          f"Found {len(templates)} template(s)")
        except:
            pass

    # Create a test template
    new_template = {
        "name": "Test Template",
        "category": "test",
        "template_type": "bbox",
        "bbox_data": {"x": 0, "y": 0, "width": 100, "height": 100},
        "confidence": 0.9
    }
    create_response = test_endpoint("POST", "/api/templates", data=new_template,
                                   expected_status=200,
                                   description="POST /api/templates - Create template")

    if create_response:
        try:
            created_template = create_response.json()
            new_template_id = created_template.get('id')

            if new_template_id:
                # Test get specific template
                test_endpoint("GET", f"/api/templates/{new_template_id}",
                            expected_status=200,
                            description=f"GET /api/templates/{new_template_id} - Get specific template")

                # Test update
                update_data = {"name": "Updated Test Template"}
                test_endpoint("PUT", f"/api/templates/{new_template_id}",
                            data=update_data, expected_status=200,
                            description=f"PUT /api/templates/{new_template_id} - Update template")

                # Test track usage
                test_endpoint("POST", f"/api/templates/{new_template_id}/use",
                            expected_status=200,
                            description=f"POST /api/templates/{new_template_id}/use - Track usage")

                # Test delete (clean up)
                test_endpoint("DELETE", f"/api/templates/{new_template_id}",
                            expected_status=200,
                            description=f"DELETE /api/templates/{new_template_id} - Delete template")
        except:
            print_test("Template CRUD operations", "FAIL",
                      "Failed to parse created template")

    # Test search (with empty query should return all)
    test_endpoint("GET", "/api/templates/search?query=",
                 expected_status=200,
                 description="GET /api/templates/search - Search templates")

    # =========================================================================
    # 7. SAM API (3 endpoints)
    # =========================================================================
    print_header("7. SAM API (3 endpoints)")

    test_endpoint("GET", "/api/sam/status", expected_status=200,
                 description="GET /api/sam/status - SAM status")

    # Test mock SAM generation
    sam_request = {
        "image_id": image_id if image_id else 1,
        "points": [[100, 100]],
        "labels": [1]
    }
    test_endpoint("POST", "/api/sam/generate-mock", data=sam_request,
                 expected_status=200,
                 description="POST /api/sam/generate-mock - Generate mock SAM mask")

    # Real SAM endpoint (likely to fail if not configured)
    print_test("POST /api/sam/generate - Generate real SAM mask", "SKIP",
              "Real SAM requires model configuration")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Test Summary")

    total_tests = tests_passed + tests_failed + tests_skipped
    pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests:  {total_tests}")
    print(f"✓ Passed:     {tests_passed} ({pass_rate:.1f}%)")
    print(f"✗ Failed:     {tests_failed}")
    print(f"⊘ Skipped:    {tests_skipped}")

    if tests_failed == 0:
        print("\n\033[92m✓ All tests passed!\033[0m")
        return 0
    else:
        print(f"\n\033[91m✗ {tests_failed} test(s) failed\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(main())
