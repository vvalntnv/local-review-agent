"""Test suite for the tools module"""

import os
import sys
import tempfile
import shutil

# Add parent directory to path so we can import tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.explore_structure import explore_structure
from tools.read_file import read_file
from tools.write_review import write_review


def test_explore_structure():
    """Test the explore_structure tool"""
    print("\n=== Testing explore_structure ===")

    # Test with current directory
    try:
        result = explore_structure(
            ".", depth=1, ignore_names=[r"^\.git$", r"^__pycache__$", r"^\.venv$"]
        )
        print(f"✓ Successfully explored directory structure")
        print(f"  Found {len(result.files)} files")
        print(f"  Found {len(result.children)} subdirectories")

        # Test with small depth
        result2 = explore_structure(".", depth=0)
        print(f"✓ Handled depth 0 correctly")

    except Exception as e:
        print(f"✗ explore_structure failed: {e}")
        return False

    return True


def test_read_file():
    """Test the read_file tool"""
    print("\n=== Testing read_file ===")

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Test content\nLine 2")
        temp_file = f.name

    try:
        content = read_file(temp_file)
        assert content == "Test content\nLine 2", "Content mismatch"
        print(f"✓ Successfully read file content")

        # Test with non-existent file
        try:
            read_file("non_existent_file.txt")
            print(f"✗ Should have raised error for non-existent file")
            return False
        except FileNotFoundError:
            print(f"✓ Correctly raised error for non-existent file")

    except Exception as e:
        print(f"✗ read_file failed: {e}")
        return False
    finally:
        os.unlink(temp_file)

    return True


def test_write_review():
    """Test the write_review tool"""
    print("\n=== Testing write_review ===")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    review_file = os.path.join(temp_dir, "test_review.md")

    try:
        review_content = "# Test Review\n\nThis is a test review."
        write_review(review_content, review_file)

        # Verify the file was created and content matches
        assert os.path.exists(review_file), "Review file was not created"

        with open(review_file, "r") as f:
            written_content = f.read()

        assert written_content == review_content, "Written content doesn't match"
        print(f"✓ Successfully wrote review to file")

    except Exception as e:
        print(f"✗ write_review failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

    return True


if __name__ == "__main__":
    print("Running tool tests...")

    results = []
    results.append(("explore_structure", test_explore_structure()))
    results.append(("read_file", test_read_file()))
    results.append(("write_review", test_write_review()))

    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
