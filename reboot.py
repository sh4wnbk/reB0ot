import argparse
import sys
import requests
import textwrap
import os
import io
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIGURATION ===
WATSONX_API_KEY = os.environ.get("WATSONX_API_KEY", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")
WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
MODEL_ID = "meta-llama/llama-3-3-70b-instruct"

INSTRUCTION = """You are a cognitive state extractor for IBM Bob IDE sessions.
Given a raw Bob session export, extract and compress into a
single paragraph beginning with "RESTORE CONTEXT:" addressed
directly to Bob. Cover: what is being built, why this approach
was chosen over alternatives, what files are in progress, the
exact next step, and any dead ends already ruled out.
No bullet points. No headers. One paragraph only.
Maximum 150 words. Nothing before or after the paragraph.
Do NOT write code. Output the paragraph exactly once.
Stop immediately after the final sentence.
If the export contains multiple tasks, summarize only
the most recent task. Ignore earlier tasks entirely."""

INSTRUCTION_STRUCTURED = """You are a cognitive state extractor for IBM Bob IDE sessions.
Given a raw Bob session export, extract key facts and output ONLY this exact format:

PROJECT:     [project name]
STATE:       [one sentence — what is done and what is broken/pending]
LAST ACTION: [the most recent concrete thing completed]
NEXT:        [single immediate next action]
DEAD ENDS:   [comma separated list of ruled-out approaches]
DEADLINE:    [if mentioned, otherwise omit this line]

No prose. No extra lines. No explanation. Exact format above only.
If the export contains multiple tasks, use only the most recent task."""

FEW_SHOT_PARAGRAPH = """Input:
# Task: Build session resume feature
User: Create a function that reads a markdown file
Bob: Here's the implementation in parser.py
Files Modified: parser.py
Tokens: 1.2k | Cost: 0.02

Output:
RESTORE CONTEXT: We are building X to solve Y using approach Z instead of W because of reason R. File A is complete, File B is in progress. The immediate next step is action N. Do not suggest alternative_approach — it was ruled out because of constraint C."""

FEW_SHOT_STRUCTURED = """Input:
# Task: Build session resume feature
User: Create a function that reads a markdown file
Bob: Here's the implementation in parser.py
Files Modified: parser.py
Tokens: 1.2k | Cost: 0.02

Output:
PROJECT:     Session Resume Feature
STATE:       parser.py complete, main integration pending
LAST ACTION: Implemented markdown file reader in parser.py
NEXT:        Integrate parser with main application flow
DEAD ENDS:   JSON format, XML parsing"""

# Valid field names for structured output parsing
VALID_FIELDS = {"PROJECT", "STATE", "LAST ACTION", "NEXT", "DEAD ENDS", "DEADLINE", "NOTE"}

# Context-specific credential patterns to detect actual credential exposure
# without flagging legitimate content like git SHAs or base64 strings
CREDENTIAL_PATTERNS = [
    r'WATSONX_API_KEY\s*=\s*\S+',
    r'PROJECT_ID\s*=\s*\S+',
    r'api[_-]?key\s*[=:]\s*\S+',
    r'password\s*[=:]\s*\S+',
    r'secret\s*[=:]\s*\S+',
]

# Smart truncation constants for export text processing
HEAD_CHARS = 800
MIDDLE_CHARS = 400
TAIL_CHARS = 1800
MAX_EXPORT_CHARS = HEAD_CHARS + MIDDLE_CHARS + TAIL_CHARS


def scan_for_credentials(text):
    """Scan text for potential credentials and return True if found.
    
    Skips matches that contain placeholder-like text such as:
    'your-', 'your_', 'example', 'placeholder', 'here', 'change-me', 'xxx'
    """
    placeholder_indicators = [
        "your-", "your_", "example", "placeholder",
        "here", "change-me", "xxx", "os.environ", "environ.get",
        "getenv", "environ[",
        "config.", "secrets.", "$", ": str", ": int", ": dict", ": list", ": bool",
    ]
    
    for pattern in CREDENTIAL_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            matched_text = match.group(0).lower()
            # Check if the matched text contains any placeholder indicators
            is_placeholder = any(indicator in matched_text for indicator in placeholder_indicators)
            if not is_placeholder:
                return True
    return False


def get_iam_token(api_key):
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def format_card(fields: dict) -> str:
    separator = "=" * 50
    lines = [separator]
    for key, val in fields.items():
        wrapped = textwrap.wrap(val.strip(), 50) if val.strip() else ["None"]
        lines.append(f"{key:<12} {wrapped[0]}")
        for continuation in wrapped[1:]:
            lines.append(f"{'':12} {continuation}")
    lines.append(separator)
    return "\n".join(lines)


def generate_restoration_string(export_text, token, fmt="paragraph"):
    # Strip workspace metadata blocks — file listings, cost, timestamps, never restoration-relevant
    export_text = re.sub(r'<environment_details>.*?</environment_details>', '', export_text, flags=re.DOTALL)

    # Smart three-part extraction: HEAD (task context) + MIDDLE (key events) + TAIL (recent outcome)
    # Weighting: HEAD_CHARS/MIDDLE_CHARS/TAIL_CHARS — recent context is most valuable for restoration
    if len(export_text) > MAX_EXPORT_CHARS:
        head = export_text[:HEAD_CHARS]
        tail = export_text[-TAIL_CHARS:]
        
        # Extract middle section and search for important keywords
        middle_start = HEAD_CHARS
        middle_end = len(export_text) - TAIL_CHARS
        middle_section = export_text[middle_start:middle_end]
        
        # Keywords that indicate important content
        keywords = ["Files Modified", "Error", "Fixed", "NEXT", "Decision"]
        middle_extract = ""
        
        # Search for first keyword match with surrounding context
        for keyword in keywords:
            match_pos = middle_section.find(keyword)
            if match_pos != -1:
                # Find line boundaries around the match (2-3 lines of context)
                lines = middle_section[:match_pos + 200].split('\n')
                start_line = max(0, len(lines) - 4)  # 3 lines before + match line
                
                # Get surrounding lines
                context_start = middle_section.rfind('\n', 0, match_pos - 100) + 1
                if context_start == 0:
                    context_start = 0
                context_end = middle_section.find('\n', match_pos + 300)
                if context_end == -1:
                    context_end = match_pos + MIDDLE_CHARS
                
                middle_extract = middle_section[context_start:context_end]
                # Limit to MIDDLE_CHARS
                if len(middle_extract) > MIDDLE_CHARS:
                    middle_extract = middle_extract[:MIDDLE_CHARS]
                break
        
        # Assemble final text
        if middle_extract:
            export_text = head + "\n...\n" + middle_extract + "\n...\n" + tail
        else:
            # No keyword match found, use head + tail with new ratio
            export_text = head + "\n...\n" + tail
    instruction = INSTRUCTION if fmt == "paragraph" else INSTRUCTION_STRUCTURED
    few_shot = FEW_SHOT_PARAGRAPH if fmt == "paragraph" else FEW_SHOT_STRUCTURED
    prompt = f"{instruction}\n\n{few_shot}\n\nInput:\n{export_text}\n\nOutput:"

    payload = {
        "model_id": MODEL_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 175 if fmt == "paragraph" else 250,
            "min_new_tokens": 50,
            "repetition_penalty": 1.3,
            "stop_sequences": [] if fmt == "structured" else ["\n\n"]
        },
        "project_id": PROJECT_ID
    }

    try:
        resp = requests.post(
            f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            raise SystemExit("Error: API access denied (403). Check your WATSONX_API_KEY and PROJECT_ID.")
        elif e.response.status_code == 429:
            raise SystemExit("Error: Rate limit hit (429). Wait a moment and try again.")
        else:
            raise SystemExit(f"Error: API call failed ({e.response.status_code}): {e}")
    result = resp.json()["results"][0]["generated_text"].strip()
    
    if fmt == "structured":
        lines = [l for l in result.split("\n") if l.strip()]
        clean = []
        for line in lines:
            clean.append(line)
            if line.startswith("DEADLINE:") or (line.startswith("DEAD ENDS:") and not any(l.startswith("DEADLINE:") for l in lines)):
                break
        result = "\n".join(clean[:6])
    return result


def parse_next_options(next_value):
    """
    Parse NEXT field for multiple options and prompt user to select one.
    
    Args:
        next_value: The NEXT field value that may contain multiple options
        
    Returns:
        The selected option string, or the original value if no selection made
    """
    # Check if NEXT contains multiple options (or, comma, or multiple sentences)
    has_or = " or " in next_value.lower()
    has_comma = "," in next_value
    has_multiple_sentences = next_value.count(".") > 1 or next_value.count(";") > 0
    
    if not (has_or or has_comma or has_multiple_sentences):
        return next_value
    
    # Parse options
    options = []
    if has_or:
        # Split by 'or' (case insensitive)
        options = re.split(r'\s+or\s+', next_value, flags=re.IGNORECASE)
    elif has_comma:
        options = [opt.strip() for opt in next_value.split(",")]
    else:  # Multiple sentences
        # Split by period or semicolon
        options = [opt.strip() for opt in re.split(r'[.;]', next_value) if opt.strip()]
    
    if len(options) <= 1:
        return next_value
    
    # Display numbered menu
    print("\nMultiple NEXT options detected:")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    # Check if stdin is a TTY (interactive terminal)
    if not sys.stdin.isatty():
        print("\n(Non-interactive terminal detected — skipping selection)")
        print()  # Empty line before card
        return next_value
    
    # Prompt for selection
    while True:
        try:
            choice = input(f"\nSelect option (1-{len(options)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                selected = options[choice_num - 1]
                print()  # Empty line before card
                return selected
            else:
                print(f"Please enter a number between 1 and {len(options)}")
        except (ValueError, KeyboardInterrupt):
            print("\nKeeping original NEXT value")
            print()  # Empty line before card
            return next_value


def main():
    # Set stdout to UTF-8 encoding to handle Unicode characters
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Check environment variables at runtime, not at module load time
    if not WATSONX_API_KEY or not PROJECT_ID:
        print("Error: WATSONX_API_KEY and PROJECT_ID environment variables must be set.")
        print("Run: $env:WATSONX_API_KEY='your-key'")
        print("Run: $env:PROJECT_ID='your-project-id'")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="reB0ot - generate a Restoration String from a Bob session export.")
    parser.add_argument("--export", required=True, help="Path to the Bob session export .md file")
    parser.add_argument("--format", choices=["paragraph", "structured"],
                        default="paragraph", help="Output format")
    parser.add_argument("--note", required=False, default=None,
                        help="Optional human context — your current thought or intent")
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive mode: prompt to select from multiple NEXT options")
    parser.add_argument("--output", required=False, default=None,
                        help="Save Restoration String to this file path (UTF-8)")
    args = parser.parse_args()

    try:
        with open(args.export, "r", encoding="utf-8") as f:
            export_text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.export}")
        sys.exit(1)

    # Scan for credentials before processing
    if scan_for_credentials(export_text):
        print("⚠️  WARNING: Potential credentials detected in export file.")
        print("Review the file before processing. Exiting for security.")
        sys.exit(1)

    print("Authenticating with IBM Cloud...")
    token = get_iam_token(WATSONX_API_KEY)

    print("Generating Restoration String...\n")
    result = generate_restoration_string(export_text, token, args.format)

    # Prepare the output string
    result_output = ""
    if args.format == "structured":
        fields = {}
        for line in result.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                # Only accept lines where the key matches a valid field name
                if key in VALID_FIELDS:
                    fields[key] = val.strip()
                # Skip any line whose key is not in VALID_FIELDS (prevents preamble leak)
        if args.note:
            fields["NOTE"] = args.note
        
        # Interactive mode: parse NEXT field for multiple options
        if args.interactive and "NEXT" in fields:
            fields["NEXT"] = parse_next_options(fields["NEXT"])
        
        result_output = format_card(fields)
        print(result_output)
    else:
        result_output = "=" * 60 + "\n" + result + "\n" + "=" * 60
        print(result_output)
    
    # Save to file if --output is specified
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result_output)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

# Made with Bob
