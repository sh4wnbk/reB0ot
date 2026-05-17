![reB0ot — Your brain shouldn't be your only backup](bob_sessions/images/blueprint.png)
*AI-generated image created with Google Gemini. IBM Bob character © IBM Corporation.*

# r⚡B0ot

**THE BLUEPRINT. FLOW STATE ONLY.**

Every developer knows the feeling: you open your IDE after a break and spend
the first 20 minutes just figuring out where you left off. **r⚡B0ot** fixes that.

> *"/snapshot before you leave. /reboot when you return."*

---

## What it does

**r⚡B0ot** reads an IBM Bob IDE session export and generates a **Restoration String** — a compressed snapshot of exactly where you were, what you were doing, what you already tried, and what to do next.

Two Bob commands. Zero context loss.

```
/snapshot    →   captures your session state before you leave
/reboot      →   restores that state the moment you return
```

Bob reads the Restoration String and picks up exactly where you left off — including dead ends you already ruled out, so you never retrace wasted steps.

---

## Bob Commands

The fastest path — no CLI required:

**Capture your session:**
```
/snapshot --note "your current thought or intent"
```
Runs `reboot.py` against the current session export, saves the Restoration String to `.bob/context/reboot_latest.md`.

**Restore your session:**
```
/reboot
```
Reads `.bob/context/reboot_latest.md` and restores full session context — project state, last action, next step, dead ends.

---

## How to export a Bob session

1. In Bob IDE: **Views → More Actions → History**
2. Select a task → click the **Export** icon
3. Save the `.md` file
4. Run `reboot.py` against it — or use `/snapshot` to do it automatically

---

## CLI Usage

**Requirements:**
- Python 3.11+
- IBM Cloud account with watsonx.ai access

**Setup:**
```bash
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

**Credentials:**
```powershell
# Copy the template and add your credentials
copy run.ps1.template run.ps1
# Edit run.ps1 with your actual API key and project ID
```

**Run:**
```powershell
# Structured output (recommended)
.\run.ps1 --export your_session_export.md --format structured

# Paragraph output
.\run.ps1 --export your_session_export.md --format paragraph

# Add a personal note to the card
.\run.ps1 --export your_session_export.md --format structured --note "picking this up after sprint review"

# Interactive mode — choose from multiple NEXT options
.\run.ps1 --export your_session_export.md --format structured --interactive

# Save output directly to file (UTF-8)
.\run.ps1 --export your_session_export.md --format structured --output .bob/context/reboot_latest.md
```

**Structured output:**
```
==================================================
PROJECT      reB0ot v2
STATE        Core features complete, testing done
LAST ACTION  Added smart truncation and credential scanner
NEXT         Commit and push to reB0ot repo
DEAD ENDS    None
NOTE         ready for submission
==================================================
```

---

## Showcase

![reB0ot in the flow — developers back in context instantly](bob_sessions/images/blueprint2.png)
*AI-generated image created with Google Gemini. IBM Bob character © IBM Corporation.*

![reB0ot team session snapshot — multiple projects, zero context loss](bob_sessions/images/blueprint3.png)
*AI-generated image created with Google Gemini. IBM Bob character © IBM Corporation.*

Real sessions from this project's own development:

![Task 1 — Feature development snapshot](bob_sessions/images/Task1.PNG)
![Task 2 — Bug investigation snapshot](bob_sessions/images/Task2.PNG)
![Task 3 — Architecture snapshot](bob_sessions/images/Task3.PNG)
![Task 4 — /reboot restoring context](bob_sessions/images/Task4.PNG)
![Task 5 — Multi-project context switch](bob_sessions/images/Task5.PNG)

---

## Security

**r⚡B0ot** scans every session export for potential credentials before sending anything to the API. If a real API key, password, or secret is detected, processing stops immediately. Placeholder values and code patterns are recognized and skipped automatically.

---

## Design Thinking

r⚡B0ot was ideated using IBM Enterprise Design Thinking.

The insight came from identifying the oldest unsolved problem in software development:

> *"Where was I?"*
>
> Every developer. Every day. Since the first line of code was ever written — before Git, before IDEs, before AI. Nothing has ever solved it. You close your laptop. You come back. The mental thread is gone. The *"I was about to try X,"* the *"I chose Y over Z because…"* — evaporated.

Bob already records everything. Every task, every decision, every generation. The session export is already required for judging. The raw material exists.

The **Hill**:

> **Developers using IBM Bob IDE** can restore full session context after any interruption — without manual reconstruction — **so that** time-to-productivity after a context switch drops from 20 minutes to under 5 seconds.

That Hill drove every feature decision: the Restoration String format, the `DEAD ENDS` field (capturing what not to retry), and the two-command workflow that requires zero CLI knowledge to use.

---

## How it was built

Built entirely using **IBM Bob IDE** — and built using itself. Every development session was exported and processed through r⚡B0ot. The `/reboot` command restored context at the start of every session. The `bob_sessions/` folder contains the complete development history — over 20 exported sessions from this project alone.

**Features built during IBM Bob Hackathon, May 15–17, 2026:**
- Smart three-part session truncation (head / keyword middle / tail)
- Precision credential scanner with placeholder and code-pattern detection
- `--interactive` mode for multi-option NEXT selection
- `--note` annotation flag
- `--output` flag for UTF-8 file export
- `/snapshot` and `/reboot` Bob commands
- 11-test suite with 100% pass rate

**Stack:**
- IBM Bob IDE — Code, Ask, Plan, Advanced, and Orchestrator modes
- watsonx.ai — `meta-llama/llama-3-3-70b-instruct`
- Python — CLI, API calls, card rendering

---

## Legal

This project is licensed under the [MIT License](LICENSE).

**IBM Bob™** and **watsonx.ai™** are trademarks of IBM Corporation. This project is not affiliated with, endorsed by, or sponsored by IBM Corporation beyond participation in the IBM Bob Hackathon (May 15–17, 2026).

AI-generated images in `bob_sessions/images/` were created using Google Gemini. The IBM Bob character depicted is the intellectual property of IBM Corporation.

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list of contributors.

---

*Built with IBM Bob. Powered by watsonx.ai.*
