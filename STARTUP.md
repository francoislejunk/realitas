# Realitas Neo - Setup Guide

## For Cascade AI Assistant
If you're reading this as an AI assistant, follow these steps in order to set up the project for the user.

---

## Prerequisites
- **Python 3.11+** must be installed
- **OpenRouter API Key** required (get from https://openrouter.ai/)

---

## Step-by-Step Setup

### Step 1: Create Virtual Environment
Run this command in the project root folder:
```bash
python -m venv .venv
```

### Step 2: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\.venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of the terminal prompt.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs all required packages. Wait for it to complete.

### Step 4: Check/Create the `.env` File
Check if a `.env` file already exists in the project root. If it does, skip to Step 5.

If no `.env` file exists, create one with this content:
```
OPENROUTER_API_KEY=your_api_key_here
```

**IMPORTANT:** Replace `your_api_key_here` with your actual OpenRouter API key from https://openrouter.ai/

### Step 5: Load Worldbuilding Lore
```bash
python WORLD_BUILDER/realitas_lore.py
```

Expected output:
```
✅ Successfully loaded 27 lore entries!
```

### Step 6: Run the Simulation
```bash
python MAIN/redesigned_main.py
```

---

## Troubleshooting

### "Module not found" errors
Ensure virtual environment is activated, then reinstall:
```bash
pip install -r requirements.txt
```

### "OPENROUTER_API_KEY not set" error
Create the `.env` file as described in Step 4.

### PowerShell script execution blocked (Windows)
Run this command first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "python" command not found
- Try `python3` instead of `python`
- Or add Python to your system PATH

### API errors / Empty responses
- Check your OpenRouter API key is valid
- Check you have credits in your OpenRouter account
- Check your internet connection

---

## Quick Verification Checklist

Run these commands to verify setup:

```bash
# Check Python version (should be 3.11+)
python --version

# Check virtual environment is active (should show package list)
pip list

# Check .env file exists
# Windows: dir .env
# Mac/Linux: ls -la .env

# Test RAG system
python -c "from WORLD_BUILDER.worldbuilding_rag import WorldbuildingRAGSystem; print('RAG OK')"
```

---

## File Structure Overview

```
Realitas Neo/
├── .venv/                  # Virtual environment (created in Step 1)
├── .env                    # API keys (created in Step 4)
├── MAIN/
│   └── redesigned_main.py  # Main entry point
├── WORLD_BUILDER/
│   ├── realitas_lore.py    # Worldbuilding content
│   └── worldbuilding_rag.py # RAG system
├── agents/                 # AI agents (creator, narrator, conductor)
├── simulation_data/        # Session saves and worldbuilding cache
├── requirements.txt        # Python dependencies
└── STARTUP.md              # This file
```

---

## For Cascade: Automated Setup Commands

If the user asks you to set up the project, run these commands in sequence:

1. `python -m venv .venv` (in project root)
2. Activate venv (platform-specific)
3. `pip install -r requirements.txt`
4. Create `.env` file with user's API key
5. `python WORLD_BUILDER/realitas_lore.py`
6. `python MAIN/redesigned_main.py` (non-blocking, to start the simulation)

---

## Support

If you encounter issues not covered here, check:
1. Python version is 3.11 or higher
2. All dependencies installed successfully
3. `.env` file exists with valid API key
4. Virtual environment is activated
5. Lore was loaded successfully

---

*Last updated: December 2025*
