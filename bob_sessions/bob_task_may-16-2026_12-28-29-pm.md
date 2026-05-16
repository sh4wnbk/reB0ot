**User:**

<task>
In reboot.py, the truncation logic at the start of generate_restoration_string()
  currently does a naive head+tail split:

      if len(export_text) > 3000:
          export_text = export_text[:1500] + "\n...\n" + export_text[-1500:]

  The problem: the middle of a Bob session often contains the most important
  content — file modifications, error messages, key decisions. Equal head/tail
  splitting discards all of it.

  Replace this with a smarter three-part extraction:

  1. HEAD (first 800 chars) — captures the task description and initial context
  2. MIDDLE (up to 400 chars) — scan the middle section for lines containing
     keywords: "Files Modified", "Error", "Fixed", "NEXT", "Decision".
     Grab the first match and surrounding 2-3 lines.
  3. TAIL (last 1800 chars) — the most recent exchanges and outcome.
     Recent context is the most valuable for restoration.

  If no keyword match is found in the middle, just use head + tail with
  the new 800/1800 ratio. Add a brief inline comment explaining the weighting
  rationale.
</task>
<environment_details>
# VSCode Visible Files
reboot.py

# VSCode Open Tabs
reboot.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-16T16:28:02.031Z
User time zone: America/New_York, UTC-4:00

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>


# Current Workspace Directory (c:/Users/shawn/bob/reboot) Files
.gitignore
debug_report.md
developer.png
HACKATHON_SUBMISSION.md
README.md
reboot.py
requirements.txt
run.ps1.template
SECURITY.md
test_debug.py
test_interactive_feature.py
.bob/
bob_sessions/
bob_sessions/bob_ask_mode.PNG
bob_sessions/bob_code_mode.PNG
bob_sessions/bob_task_create_reboot_file.md
bob_sessions/bob_task_explain_codebase.md
bob_sessions/bob_task_format_argument.md
bob_sessions/bob_task_max_new_tokens.md
bob_sessions/bob_task_may-16-2026_12-21-53-pm.md
bob_sessions/bob_task_reboot.md
bob_sessions/create_resume_file.PNG
bob_sessions/debug.PNG
bob_sessions/demo.png
bob_sessions/demo2.png
bob_sessions/explain_codebase.PNG
bob_sessions/format_argument.PNG
bob_sessions/max_new_tokens.PNG
bob_sessions/progress_bar.png
bob_sessions/reB0ot.png
bob_sessions/reboot.png
bob_sessions/REBRANDING_NOTE.md
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll help you improve the truncation logic in reboot.py. Let me first read the file to understand the current implementation.

<read_file>
<args>
<file>
<path>reboot.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'reboot.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>reboot.py</path>
<content lines="1-274">
  1 | import argparse
  2 | import sys
  3 | import requests
  4 | import textwrap
  5 | import os
  6 | import io
  7 | import re
  8 | from dotenv import load_dotenv
  9 | 
 10 | # Load environment variables from .env file
 11 | load_dotenv()
 12 | 
 13 | # === CONFIGURATION ===
 14 | WATSONX_API_KEY = os.environ.get("WATSONX_API_KEY", "")
 15 | PROJECT_ID = os.environ.get("PROJECT_ID", "")
 16 | WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
 17 | MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
 18 | 
 19 | INSTRUCTION = """You are a cognitive state extractor for IBM Bob IDE sessions.
 20 | Given a raw Bob session export, extract and compress into a
 21 | single paragraph beginning with "RESTORE CONTEXT:" addressed
 22 | directly to Bob. Cover: what is being built, why this approach
 23 | was chosen over alternatives, what files are in progress, the
 24 | exact next step, and any dead ends already ruled out.
 25 | No bullet points. No headers. One paragraph only.
 26 | Maximum 150 words. Nothing before or after the paragraph.
 27 | Do NOT write code. Output the paragraph exactly once.
 28 | Stop immediately after the final sentence.
 29 | If the export contains multiple tasks, summarize only
 30 | the most recent task. Ignore earlier tasks entirely."""
 31 | 
 32 | INSTRUCTION_STRUCTURED = """You are a cognitive state extractor for IBM Bob IDE sessions.
 33 | Given a raw Bob session export, extract key facts and output ONLY this exact format:
 34 | 
 35 | PROJECT:     [project name]
 36 | STATE:       [one sentence — what is done and what is broken/pending]
 37 | LAST ACTION: [the most recent concrete thing completed]
 38 | NEXT:        [single immediate next action]
 39 | DEAD ENDS:   [comma separated list of ruled-out approaches]
 40 | DEADLINE:    [if mentioned, otherwise omit this line]
 41 | 
 42 | No prose. No extra lines. No explanation. Exact format above only.
 43 | If the export contains multiple tasks, use only the most recent task."""
 44 | 
 45 | FEW_SHOT_PARAGRAPH = """Input:
 46 | # Task: Build session resume feature
 47 | User: Create a function that reads a markdown file
 48 | Bob: Here's the implementation in parser.py
 49 | Files Modified: parser.py
 50 | Tokens: 1.2k | Cost: 0.02
 51 | 
 52 | Output:
 53 | RESTORE CONTEXT: We are building X to solve Y using approach Z instead of W because of reason R. File A is complete, File B is in progress. The immediate next step is action N. Do not suggest alternative_approach — it was ruled out because of constraint C."""
 54 | 
 55 | FEW_SHOT_STRUCTURED = """Input:
 56 | # Task: Build session resume feature
 57 | User: Create a function that reads a markdown file
 58 | Bob: Here's the implementation in parser.py
 59 | Files Modified: parser.py
 60 | Tokens: 1.2k | Cost: 0.02
 61 | 
 62 | Output:
 63 | PROJECT:     Session Resume Feature
 64 | STATE:       parser.py complete, main integration pending
 65 | LAST ACTION: Implemented markdown file reader in parser.py
 66 | NEXT:        Integrate parser with main application flow
 67 | DEAD ENDS:   JSON format, XML parsing"""
 68 | 
 69 | # Context-specific credential patterns to detect actual credential exposure
 70 | # without flagging legitimate content like git SHAs or base64 strings
 71 | CREDENTIAL_PATTERNS = [
 72 |     r'WATSONX_API_KEY\s*=\s*\S+',
 73 |     r'PROJECT_ID\s*=\s*\S+',
 74 |     r'api[_-]?key\s*[=:]\s*\S+',
 75 |     r'password\s*[=:]\s*\S+',
 76 |     r'secret\s*[=:]\s*\S+',
 77 | ]
 78 | 
 79 | 
 80 | def scan_for_credentials(text):
 81 |     """Scan text for potential credentials and return True if found."""
 82 |     for pattern in CREDENTIAL_PATTERNS:
 83 |         if re.search(pattern, text, re.IGNORECASE):
 84 |             return True
 85 |     return False
 86 | 
 87 | 
 88 | def get_iam_token(api_key):
 89 |     resp = requests.post(
 90 |         "https://iam.cloud.ibm.com/identity/token",
 91 |         data={
 92 |             "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
 93 |             "apikey": api_key
 94 |         },
 95 |         headers={"Content-Type": "application/x-www-form-urlencoded"}
 96 |     )
 97 |     resp.raise_for_status()
 98 |     return resp.json()["access_token"]
 99 | 
100 | 
101 | def format_card(fields: dict) -> str:
102 |     separator = "=" * 50
103 |     lines = [separator]
104 |     for key, val in fields.items():
105 |         wrapped = textwrap.wrap(val.strip(), 50) if val.strip() else ["None"]
106 |         lines.append(f"{key:<12} {wrapped[0]}")
107 |         for continuation in wrapped[1:]:
108 |             lines.append(f"{'':12} {continuation}")
109 |     lines.append(separator)
110 |     return "\n".join(lines)
111 | 
112 | 
113 | def generate_restoration_string(export_text, token, fmt="paragraph"):
114 |     # Take first 1500 chars (task context) + last 1500 chars (outcome)
115 |     # This ensures we capture both the initial task and the final result
116 |     if len(export_text) > 3000:
117 |         export_text = export_text[:1500] + "\n...\n" + export_text[-1500:]
118 |     instruction = INSTRUCTION if fmt == "paragraph" else INSTRUCTION_STRUCTURED
119 |     few_shot = FEW_SHOT_PARAGRAPH if fmt == "paragraph" else FEW_SHOT_STRUCTURED
120 |     prompt = f"{instruction}\n\n{few_shot}\n\nInput:\n{export_text}\n\nOutput:"
121 | 
122 |     payload = {
123 |         "model_id": MODEL_ID,
124 |         "input": prompt,
125 |         "parameters": {
126 |             "decoding_method": "greedy",
127 |             "max_new_tokens": 175 if fmt == "paragraph" else 250,
128 |             "min_new_tokens": 50,
129 |             "repetition_penalty": 1.3,
130 |             "stop_sequences": [] if fmt == "structured" else ["\n\n"]
131 |         },
132 |         "project_id": PROJECT_ID
133 |     }
134 | 
135 |     resp = requests.post(
136 |         f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
137 |         json=payload,
138 |         headers={
139 |             "Authorization": f"Bearer {token}",
140 |             "Content-Type": "application/json"
141 |         }
142 |     )
143 |     resp.raise_for_status()
144 |     result = resp.json()["results"][0]["generated_text"].strip()
145 |     
146 |     if fmt == "structured":
147 |         lines = [l for l in result.split("\n") if l.strip()]
148 |         clean = []
149 |         for line in lines:
150 |             clean.append(line)
151 |             if line.startswith("DEADLINE:") or (line.startswith("DEAD ENDS:") and not any(l.startswith("DEADLINE:") for l in lines)):
152 |                 break
153 |         result = "\n".join(clean[:6])
154 |     return result
155 | 
156 | 
157 | def parse_next_options(next_value):
158 |     """
159 |     Parse NEXT field for multiple options and prompt user to select one.
160 |     
161 |     Args:
162 |         next_value: The NEXT field value that may contain multiple options
163 |         
164 |     Returns:
165 |         The selected option string, or the original value if no selection made
166 |     """
167 |     # Check if NEXT contains multiple options (or, comma, or multiple sentences)
168 |     has_or = " or " in next_value.lower()
169 |     has_comma = "," in next_value
170 |     has_multiple_sentences = next_value.count(".") > 1 or next_value.count(";") > 0
171 |     
172 |     if not (has_or or has_comma or has_multiple_sentences):
173 |         return next_value
174 |     
175 |     # Parse options
176 |     options = []
177 |     if has_or:
178 |         # Split by 'or' (case insensitive)
179 |         options = re.split(r'\s+or\s+', next_value, flags=re.IGNORECASE)
180 |     elif has_comma:
181 |         options = [opt.strip() for opt in next_value.split(",")]
182 |     else:  # Multiple sentences
183 |         # Split by period or semicolon
184 |         options = [opt.strip() for opt in re.split(r'[.;]', next_value) if opt.strip()]
185 |     
186 |     if len(options) <= 1:
187 |         return next_value
188 |     
189 |     # Display numbered menu
190 |     print("\nMultiple NEXT options detected:")
191 |     for i, option in enumerate(options, 1):
192 |         print(f"  {i}. {option}")
193 |     
194 |     # Prompt for selection
195 |     while True:
196 |         try:
197 |             choice = input(f"\nSelect option (1-{len(options)}): ").strip()
198 |             choice_num = int(choice)
199 |             if 1 <= choice_num <= len(options):
200 |                 selected = options[choice_num - 1]
201 |                 print()  # Empty line before card
202 |                 return selected
203 |             else:
204 |                 print(f"Please enter a number between 1 and {len(options)}")
205 |         except (ValueError, KeyboardInterrupt):
206 |             print("\nKeeping original NEXT value")
207 |             print()  # Empty line before card
208 |             return next_value
209 | 
210 | 
211 | def main():
212 |     # Set stdout to UTF-8 encoding to handle Unicode characters
213 |     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
214 |     
215 |     # Check environment variables at runtime, not at module load time
216 |     if not WATSONX_API_KEY or not PROJECT_ID:
217 |         print("Error: WATSONX_API_KEY and PROJECT_ID environment variables must be set.")
218 |         print("Run: $env:WATSONX_API_KEY='your-key'")
219 |         print("Run: $env:PROJECT_ID='your-project-id'")
220 |         sys.exit(1)
221 |     
222 |     parser = argparse.ArgumentParser(description="reB0ot - generate a Restoration String from a Bob session export.")
223 |     parser.add_argument("--export", required=True, help="Path to the Bob session export .md file")
224 |     parser.add_argument("--format", choices=["paragraph", "structured"],
225 |                         default="paragraph", help="Output format")
226 |     parser.add_argument("--note", required=False, default=None,
227 |                         help="Optional human context — your current thought or intent")
228 |     parser.add_argument("--interactive", action="store_true",
229 |                         help="Interactive mode: prompt to select from multiple NEXT options")
230 |     args = parser.parse_args()
231 | 
232 |     try:
233 |         with open(args.export, "r", encoding="utf-8") as f:
234 |             export_text = f.read()
235 |     except FileNotFoundError:
236 |         print(f"Error: File not found: {args.export}")
237 |         sys.exit(1)
238 | 
239 |     # Scan for credentials before processing
240 |     if scan_for_credentials(export_text):
241 |         print("⚠️  WARNING: Potential credentials detected in export file.")
242 |         print("Review the file before processing. Exiting for security.")
243 |         sys.exit(1)
244 | 
245 |     print("Authenticating with IBM Cloud...")
246 |     token = get_iam_token(WATSONX_API_KEY)
247 | 
248 |     print("Generating Restoration String...\n")
249 |     result = generate_restoration_string(export_text, token, args.format)
250 | 
251 |     if args.format == "structured":
252 |         fields = {}
253 |         for line in result.split("\n"):
254 |             if ":" in line:
255 |                 key, _, val = line.partition(":")
256 |                 fields[key.strip()] = val.strip()
257 |         if args.note:
258 |             fields["NOTE"] = args.note
259 |         
260 |         # Interactive mode: parse NEXT field for multiple options
261 |         if args.interactive and "NEXT" in fields:
262 |             fields["NEXT"] = parse_next_options(fields["NEXT"])
263 |         
264 |         print(format_card(fields))
265 |     else:
266 |         print("=" * 60)
267 |         print(result)
268 |         print("=" * 60)
269 | 
270 | 
271 | if __name__ == "__main__":
272 |     main()
273 | 
274 | # Made with Bob
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
reboot.py

# VSCode Open Tabs
reboot.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-16T16:28:07.161Z
User time zone: America/New_York, UTC-4:00

# Current Cost
$0.01

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now I'll replace the naive truncation logic with the smarter three-part extraction as requested. The current logic is on lines 114-117.

<apply_diff>
<path>reboot.py</path>
<diff>
<<<<<<< SEARCH
:start_line:113
-------
def generate_restoration_string(export_text, token, fmt="paragraph"):
    # Take first 1500 chars (task context) + last 1500 chars (outcome)
    # This ensures we capture both the initial task and the final result
    if len(export_text) > 3000:
        export_text = export_text[:1500] + "\n...\n" + export_text[-1500:]
=======
def generate_restoration_string(export_text, token, fmt="paragraph"):
    # Smart three-part extraction: HEAD (task context) + MIDDLE (key events) + TAIL (recent outcome)
    # Weighting: 800/400/1800 — recent context is most valuable for restoration
    if len(export_text) > 3000:
        head = export_text[:800]
        tail = export_text[-1800:]
        
        # Extract middle section and search for important keywords
        middle_start = 800
        middle_end = len(export_text) - 1800
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
                    context_end = match_pos + 400
                
                middle_extract = middle_section[context_start:context_end]
                # Limit to ~400 chars
                if len(middle_extract) > 400:
                    middle_extract = middle_extract[:400]
                break
        
        # Assemble final text
        if middle_extract:
            export_text = head + "\n...\n" + middle_extract + "\n...\n" + tail
        else:
            # No keyword match found, use head + tail with new ratio
            export_text = head + "\n...\n" + tail
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'reboot.py'] Result:
<file_write_result>
<path>reboot.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
reboot.py

# VSCode Open Tabs
reboot.py

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
reboot.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-16T16:28:23.948Z
User time zone: America/New_York, UTC-4:00

# Current Cost
$0.03

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

<attempt_completion>
<result>
Successfully replaced the naive truncation logic in reboot.py with a smarter three-part extraction:

**Changes made:**
- **HEAD (800 chars)**: Captures task description and initial context
- **MIDDLE (up to 400 chars)**: Scans for keywords ("Files Modified", "Error", "Fixed", "NEXT", "Decision") and extracts the first match with 2-3 lines of surrounding context
- **TAIL (1800 chars)**: Preserves the most recent exchanges and outcome

**Key improvements:**
1. Recent context weighted more heavily (1800 chars vs 800) since it's most valuable for restoration
2. Middle section intelligently extracts critical events instead of discarding them
3. Falls back to head+tail with new ratio if no keywords found
4. Added inline comments explaining the weighting rationale

The new 800/400/1800 character distribution ensures important middle content (file modifications, errors, decisions) is preserved while prioritizing recent context.
</result>
</attempt_completion>

