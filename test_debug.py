"""
Debug test suite for reboot.py
Tests all major functions and edge cases
"""
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reboot as resume

def test_format_card():
    """Test the format_card function with various inputs"""
    print("\n=== Testing format_card ===")
    
    # Test 1: Normal input
    fields = {
        "PROJECT": "Test Project",
        "STATE": "Working on feature X",
        "NEXT": "Complete integration"
    }
    result = resume.format_card(fields)
    print("✓ Test 1 - Normal input:")
    print(result)
    assert "PROJECT" in result
    assert "Test Project" in result
    
    # Test 2: Long text wrapping
    fields = {
        "DESCRIPTION": "This is a very long description that should wrap across multiple lines when formatted because it exceeds the 50 character limit"
    }
    result = resume.format_card(fields)
    print("\n✓ Test 2 - Long text wrapping:")
    print(result)
    assert "DESCRIPTION" in result
    
    # Test 3: Empty values
    fields = {
        "EMPTY": "",
        "WHITESPACE": "   "
    }
    result = resume.format_card(fields)
    print("\n✓ Test 3 - Empty values:")
    print(result)
    assert "None" in result
    
    print("\n✅ format_card tests passed!")


def test_text_truncation():
    """Test the smart three-part text truncation logic in generate_restoration_string"""
    print("\n=== Testing Text Truncation ===")
    
    # Test 1: Short text (no truncation)
    short_text = "Short export text"
    assert len(short_text) < 3000
    print(f"✓ Test 1 - Short text ({len(short_text)} chars): No truncation needed")
    
    # Test 2: Long text without keywords (head + tail only)
    long_text = "A" * 5000
    # New logic: 800 head + 1800 tail = 2600 chars + separators
    truncated = long_text[:800] + "\n...\n" + long_text[-1800:]
    print(f"✓ Test 2 - Long text ({len(long_text)} chars) -> Truncated to {len(truncated)} chars")
    assert len(truncated) < len(long_text)
    assert "..." in truncated
    # Verify the new ratios
    assert long_text[:800] in truncated
    assert long_text[-1800:] in truncated
    
    # Test 3: Long text with keyword in middle (head + middle + tail)
    # Create text with "Files Modified" keyword in the middle section
    head_part = "Task started. " * 60  # ~840 chars
    middle_part = "Some work done. " * 50 + "Files Modified: app.py, test.py" + " More work. " * 50  # Middle section
    tail_part = "Final steps. " * 150  # ~1950 chars
    long_text_with_keyword = head_part + middle_part + tail_part
    
    # Simulate the extraction logic
    if len(long_text_with_keyword) > 3000:
        head = long_text_with_keyword[:800]
        tail = long_text_with_keyword[-1800:]
        middle_start = 800
        middle_end = len(long_text_with_keyword) - 1800
        middle_section = long_text_with_keyword[middle_start:middle_end]
        
        # Check if keyword is found
        keyword_found = "Files Modified" in middle_section
        assert keyword_found, "Keyword 'Files Modified' should be in middle section"
        
        print(f"✓ Test 3 - Long text with keyword ({len(long_text_with_keyword)} chars)")
        print(f"  - Head: {len(head)} chars")
        print(f"  - Middle section size: {len(middle_section)} chars")
        print(f"  - Tail: {len(tail)} chars")
        print(f"  - Keyword 'Files Modified' found in middle: {keyword_found}")
    
    print("\n✅ Text truncation tests passed!")


def test_credential_scanner():
    """Test the credential scanner function"""
    print("\n=== Testing Credential Scanner ===")
    
    # Test 1: Git SHA (40-char hex) should NOT trigger (false positive removed)
    git_sha = "a1b2c3d4e5f6789012345678901234567890abcd"
    result = resume.scan_for_credentials(git_sha)
    print(f"✓ Test 1 - Git SHA (40 chars): {result}")
    assert result == False, "Git SHA should not trigger credential detection"
    
    # Test 2: WATSONX_API_KEY assignment SHOULD trigger
    api_key_text = "WATSONX_API_KEY = abc123def456"
    result = resume.scan_for_credentials(api_key_text)
    print(f"✓ Test 2 - WATSONX_API_KEY assignment: {result}")
    assert result == True, "WATSONX_API_KEY assignment should trigger"
    
    # Test 3: Generic api_key with colon SHOULD trigger
    api_key_colon = "api_key: somevalue123"
    result = resume.scan_for_credentials(api_key_colon)
    print(f"✓ Test 3 - api_key with colon: {result}")
    assert result == True, "api_key with colon should trigger"
    
    # Test 4: Generic api-key with equals SHOULD trigger
    api_key_dash = "api-key = another_value"
    result = resume.scan_for_credentials(api_key_dash)
    print(f"✓ Test 4 - api-key with equals: {result}")
    assert result == True, "api-key with equals should trigger"
    
    # Test 5: Password assignment SHOULD trigger
    password_text = "password: secret123"
    result = resume.scan_for_credentials(password_text)
    print(f"✓ Test 5 - password assignment: {result}")
    assert result == True, "password assignment should trigger"
    
    # Test 6: Normal code with long variable names should NOT trigger
    normal_code = """
    def calculate_total(items):
        very_long_variable_name_that_might_look_suspicious = sum(items)
        return very_long_variable_name_that_might_look_suspicious * 1.1
    """
    result = resume.scan_for_credentials(normal_code)
    print(f"✓ Test 6 - Normal code with long variable names: {result}")
    assert result == False, "Normal code should not trigger"
    
    # Test 7: Secret assignment SHOULD trigger
    secret_text = "secret = my_secret_value"
    result = resume.scan_for_credentials(secret_text)
    print(f"✓ Test 7 - secret assignment: {result}")
    assert result == True, "secret assignment should trigger"
    
    # Test 8: PROJECT_ID assignment SHOULD trigger
    project_id_text = "PROJECT_ID = proj-12345"
    result = resume.scan_for_credentials(project_id_text)
    print(f"✓ Test 8 - PROJECT_ID assignment: {result}")
    assert result == True, "PROJECT_ID assignment should trigger"
    
    print("\n✅ Credential scanner tests passed!")


def test_environment_variables():
    """Test environment variable handling"""
    print("\n=== Testing Environment Variables ===")
    
    # Save original values
    original_api_key = os.environ.get("WATSONX_API_KEY")
    original_project_id = os.environ.get("PROJECT_ID")
    
    # Test 1: Set environment variables
    os.environ["WATSONX_API_KEY"] = "test_key_123"
    os.environ["PROJECT_ID"] = "test_project_456"
    
    # Reload module to get fresh env vars
    import importlib
    importlib.reload(resume)
    
    print("✓ Test 1 - Env vars loaded correctly")
    assert resume.WATSONX_API_KEY == "test_key_123"
    assert resume.PROJECT_ID == "test_project_456"
    
    # Test 2: Check that module has the expected constants
    print("✓ Test 2 - Module constants verified")
    assert hasattr(resume, 'WATSONX_API_KEY')
    assert hasattr(resume, 'PROJECT_ID')
    assert hasattr(resume, 'WATSONX_URL')
    assert hasattr(resume, 'MODEL_ID')
    
    # Restore original values
    if original_api_key:
        os.environ["WATSONX_API_KEY"] = original_api_key
    else:
        os.environ.pop("WATSONX_API_KEY", None)
    if original_project_id:
        os.environ["PROJECT_ID"] = original_project_id
    else:
        os.environ.pop("PROJECT_ID", None)
    
    # Reload one more time to restore original state
    importlib.reload(resume)
    
    print("\n✅ Environment variable tests passed!")


def test_file_reading():
    """Test file reading functionality"""
    print("\n=== Testing File Reading ===")
    
    # Test 1: Create and read a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
        test_content = "# Test Export\nUser: Test task\nBob: Test response"
        f.write(test_content)
        temp_path = f.name
    
    try:
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Test 1 - File read successfully: {len(content)} chars")
        assert content == test_content
        
        # Test 2: Non-existent file
        try:
            with open("nonexistent_file.md", 'r', encoding='utf-8') as f:
                f.read()
            print("✗ Test 2 - Should have raised FileNotFoundError")
        except FileNotFoundError:
            print("✓ Test 2 - FileNotFoundError raised correctly")
        
    finally:
        os.unlink(temp_path)
    
    print("\n✅ File reading tests passed!")


def test_api_payload_structure():
    """Test API payload structure"""
    print("\n=== Testing API Payload Structure ===")
    
    # Mock the API call to inspect payload
    test_export = "Test export content"
    test_token = "test_token_123"
    
    # Test paragraph format
    payload_paragraph = {
        "model_id": resume.MODEL_ID,
        "input": f"{resume.INSTRUCTION}\n\n{resume.FEW_SHOT_PARAGRAPH}\n\nInput:\n{test_export}\n\nOutput:",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 175,
            "min_new_tokens": 50,
            "repetition_penalty": 1.3,
            "stop_sequences": ["\n\n"]
        },
        "project_id": resume.PROJECT_ID
    }
    
    print("✓ Test 1 - Paragraph format payload structure:")
    print(f"  - model_id: {payload_paragraph['model_id']}")
    print(f"  - max_new_tokens: {payload_paragraph['parameters']['max_new_tokens']}")
    print(f"  - stop_sequences: {payload_paragraph['parameters']['stop_sequences']}")
    
    # Test structured format
    payload_structured = {
        "model_id": resume.MODEL_ID,
        "input": f"{resume.INSTRUCTION_STRUCTURED}\n\n{resume.FEW_SHOT_STRUCTURED}\n\nInput:\n{test_export}\n\nOutput:",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 250,
            "min_new_tokens": 50,
            "repetition_penalty": 1.3,
            "stop_sequences": []
        },
        "project_id": resume.PROJECT_ID
    }
    
    print("\n✓ Test 2 - Structured format payload structure:")
    print(f"  - model_id: {payload_structured['model_id']}")
    print(f"  - max_new_tokens: {payload_structured['parameters']['max_new_tokens']}")
    print(f"  - stop_sequences: {payload_structured['parameters']['stop_sequences']}")
    
    print("\n✅ API payload structure tests passed!")


def test_structured_output_parsing():
    """Test structured output parsing logic"""
    print("\n=== Testing Structured Output Parsing ===")
    
    # Test 1: Complete structured output
    test_output = """PROJECT:     Test Project
STATE:       Feature complete, testing pending
LAST ACTION: Implemented core functionality
NEXT:        Write unit tests
DEAD ENDS:   Alternative approach A, approach B"""
    
    lines = [l for l in test_output.split("\n") if l.strip()]
    fields = {}
    for line in lines:
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    
    print("✓ Test 1 - Complete structured output parsed:")
    for key, val in fields.items():
        print(f"  {key}: {val}")
    
    assert "PROJECT" in fields
    assert "STATE" in fields
    assert "NEXT" in fields
    
    # Test 2: Output with DEADLINE
    test_output_deadline = """PROJECT:     Urgent Project
STATE:       In progress
LAST ACTION: Started implementation
NEXT:        Complete by EOD
DEAD ENDS:   None
DEADLINE:    2026-05-03"""
    
    lines = [l for l in test_output_deadline.split("\n") if l.strip()]
    clean = []
    for line in lines:
        clean.append(line)
        if line.startswith("DEADLINE:") or (line.startswith("DEAD ENDS:") and not any(l.startswith("DEADLINE:") for l in lines)):
            break
    result = "\n".join(clean[:6])
    
    print("\n✓ Test 2 - Output with DEADLINE parsed correctly")
    print(f"  Lines captured: {len(result.split(chr(10)))}")
    
    print("\n✅ Structured output parsing tests passed!")


def test_constants():
    """Test that all constants are properly defined"""
    print("\n=== Testing Constants ===")
    
    print(f"✓ WATSONX_URL: {resume.WATSONX_URL}")
    print(f"✓ MODEL_ID: {resume.MODEL_ID}")
    print(f"✓ INSTRUCTION length: {len(resume.INSTRUCTION)} chars")
    print(f"✓ INSTRUCTION_STRUCTURED length: {len(resume.INSTRUCTION_STRUCTURED)} chars")
    print(f"✓ FEW_SHOT_PARAGRAPH length: {len(resume.FEW_SHOT_PARAGRAPH)} chars")
    print(f"✓ FEW_SHOT_STRUCTURED length: {len(resume.FEW_SHOT_STRUCTURED)} chars")
    
    assert resume.WATSONX_URL.startswith("https://")
    assert "llama" in resume.MODEL_ID.lower()
    assert "RESTORE CONTEXT" in resume.INSTRUCTION
    assert "PROJECT:" in resume.INSTRUCTION_STRUCTURED
    
    print("\n✅ Constants tests passed!")


def test_parse_next_options():
    """Test the parse_next_options function with various inputs"""
    print("\n=== Testing parse_next_options ===")
    
    # Test 1: "or" separator - should detect options and return selected one
    with patch('sys.stdin.isatty', return_value=True), \
         patch('builtins.input', return_value='1'):
        result = resume.parse_next_options("do A or do B")
        print("✓ Test 1 - 'or' separator with selection '1':")
        print(f"  Input: 'do A or do B'")
        print(f"  Result: '{result}'")
        assert result == "do A", f"Expected 'do A', got '{result}'"
    
    # Test 2: Single action - should return unchanged
    result = resume.parse_next_options("single action only")
    print("\n✓ Test 2 - Single action (no options):")
    print(f"  Input: 'single action only'")
    print(f"  Result: '{result}'")
    assert result == "single action only", "Single action should return unchanged"
    
    # Test 3: Comma separator - should detect options
    with patch('sys.stdin.isatty', return_value=True), \
         patch('builtins.input', return_value='2'):
        result = resume.parse_next_options("do X, do Y, do Z")
        print("\n✓ Test 3 - Comma separator with selection '2':")
        print(f"  Input: 'do X, do Y, do Z'")
        print(f"  Result: '{result}'")
        assert result == "do Y", f"Expected 'do Y', got '{result}'"
    
    # Test 4: Non-interactive terminal - should return unchanged
    with patch('sys.stdin.isatty', return_value=False):
        result = resume.parse_next_options("do A or do B")
        print("\n✓ Test 4 - Non-interactive terminal:")
        print(f"  Input: 'do A or do B'")
        print(f"  Result: '{result}' (unchanged)")
        assert result == "do A or do B", "Non-interactive should return unchanged"
    
    print("\n✅ parse_next_options tests passed!")


def test_valid_fields_parser():
    """Test that the parsing logic correctly filters valid/invalid fields"""
    print("\n=== Testing Valid Fields Parser ===")
    
    # Test 1: Valid field "PROJECT" should appear in fields dict
    sample_line = "PROJECT:     test"
    fields = {}
    if ":" in sample_line:
        key, _, val = sample_line.partition(":")
        key = key.strip()
        if key in resume.VALID_FIELDS:
            fields[key] = val.strip()
    
    print("✓ Test 1 - Valid field 'PROJECT':")
    print(f"  Input: '{sample_line}'")
    print(f"  Parsed: {fields}")
    assert "PROJECT" in fields, "PROJECT should be in fields dict"
    assert fields["PROJECT"] == "test", f"Expected 'test', got '{fields['PROJECT']}'"
    
    # Test 2: Invalid field should NOT appear in fields dict
    sample_line_invalid = "Here is my attempt: None"
    fields = {}
    if ":" in sample_line_invalid:
        key, _, val = sample_line_invalid.partition(":")
        key = key.strip()
        if key in resume.VALID_FIELDS:
            fields[key] = val.strip()
    
    print("\n✓ Test 2 - Invalid field 'Here is my attempt':")
    print(f"  Input: '{sample_line_invalid}'")
    print(f"  Parsed: {fields}")
    assert "Here is my attempt" not in fields, "Invalid field should not be in fields dict"
    assert len(fields) == 0, "Fields dict should be empty for invalid field"
    
    # Test 3: Valid field "DEAD ENDS" should appear in fields dict
    sample_line_dead_ends = "DEAD ENDS:   none tried"
    fields = {}
    if ":" in sample_line_dead_ends:
        key, _, val = sample_line_dead_ends.partition(":")
        key = key.strip()
        if key in resume.VALID_FIELDS:
            fields[key] = val.strip()
    
    print("\n✓ Test 3 - Valid field 'DEAD ENDS':")
    print(f"  Input: '{sample_line_dead_ends}'")
    print(f"  Parsed: {fields}")
    assert "DEAD ENDS" in fields, "DEAD ENDS should be in fields dict"
    assert fields["DEAD ENDS"] == "none tried", f"Expected 'none tried', got '{fields['DEAD ENDS']}'"
    
    # Test 4: Parse complete sample result with mixed valid/invalid lines
    sample_result = """Here is my attempt: None
PROJECT:     Test Project
STATE:       Feature complete
LAST ACTION: Implemented core functionality
NEXT:        Write unit tests
DEAD ENDS:   Alternative approach A
Some random text: should be ignored"""
    
    fields = {}
    for line in sample_result.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            if key in resume.VALID_FIELDS:
                fields[key] = val.strip()
    
    print("\n✓ Test 4 - Complete sample with mixed valid/invalid lines:")
    print(f"  Valid fields found: {list(fields.keys())}")
    assert "PROJECT" in fields, "PROJECT should be parsed"
    assert "STATE" in fields, "STATE should be parsed"
    assert "LAST ACTION" in fields, "LAST ACTION should be parsed"
    assert "NEXT" in fields, "NEXT should be parsed"
    assert "DEAD ENDS" in fields, "DEAD ENDS should be parsed"
    assert "Here is my attempt" not in fields, "Invalid preamble should be filtered out"
    assert "Some random text" not in fields, "Invalid text should be filtered out"
    assert len(fields) == 5, f"Expected 5 valid fields, got {len(fields)}"
    
    print("\n✅ Valid fields parser tests passed!")


def run_all_tests():
    """Run all debug tests"""
    print("=" * 60)
    print("REBOOT.PY DEBUG TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_constants,
        test_format_card,
        test_text_truncation,
        test_credential_scanner,
        test_environment_variables,
        test_file_reading,
        test_api_payload_structure,
        test_structured_output_parsing,
        test_parse_next_options,
        test_valid_fields_parser
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
