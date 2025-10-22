# 🤖 UnifyVision - Autonomous Visual Agent

An autonomous visual agent that understands tasks in natural language, automatically generates an action plan, and executes it step by step by interacting with your screen.

## ✨ Features

**Automatic Planning:**
- GPT-4o-mini generates a complete step plan from your instruction
- Understands complex tasks like "send an email", "search on Google", etc.
- No need to specify each step, the agent deduces it

**Multi-Step Execution:**
- Screen capture for each click action
- Visual analysis with GPT-4o-mini Vision API
- Supported actions: `click`, `type` (with loop support), `press`, `wait`
- Grid system for higher precision in detection
- Error handling with flow continuation

**Professional Architecture:**
- Modular design with separation of concerns
- Robust error handling with custom exceptions
- Professional logging system
- Type hints throughout the codebase
- Unit tests for core functionality

## 📁 Project Structure

```
UnifyVision/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Centralized configuration
│   ├── exceptions.py         # Custom exceptions
│   ├── logger.py             # Logging system
│   ├── screen_capture.py     # Screen capture functionality
│   ├── grid_system.py        # Grid overlay system
│   ├── openai_client.py      # OpenAI API client
│   ├── planner.py            # Plan generation
│   ├── actions.py            # Action execution (click, type, etc.)
│   └── executor.py           # Plan executor
├── tests/
│   ├── __init__.py
│   ├── test_config.py        # Configuration tests
│   └── test_planner.py       # Planning tests
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Requirements

### Required Packages
The following packages are already in `requirements.txt`:
- `openai>=1.0.0`
- `pyautogui>=0.9.54`
- `pillow>=10.0.0`
- `mss>=9.0.0`
- `pyperclip>=1.8.2`

### Optional Packages
- `keyboard>=0.13.5` - Allows canceling with ESC during execution
  ```bash
  pip3 install keyboard
  ```
  **Note**: If not installed, the agent will work but you can only cancel with Ctrl+C or PyAutoGUI's failsafe

## ⚙️ Configuration

1. **⚠️ IMPORTANT**: Set the OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Never hardcode your API key in the code**. The code only accepts the API key from environment variables for security.

2. On macOS, grant accessibility permissions:
   - Go to **System Preferences** → **Security & Privacy** → **Privacy**
   - Select **Accessibility** in the left list
   - Add Terminal (or your terminal app) to the list of allowed applications

## 📖 Usage

```bash
python main.py
```

The program will ask you to describe the complete task you want to perform:

```
🎯 What task do you want to execute?: Send an email to john@test.com with subject "Meeting" and message "See you tomorrow"
```

## 🔄 Program Flow

1. **🧠 Planning** - GPT-4o-mini generates a step plan in JSON
2. **📋 Review** - Shows the generated plan for your review
3. **🚀 Execution** - Executes each step of the plan:
   - For `click`: Capture screen → Vision API → Click
   - For `type`: Write the text
   - For `press`: Press the key
   - For `wait`: Wait N seconds
4. **📊 Summary** - Shows execution statistics
5. **🗑️ Cleanup** - Removes temporary files

## 💡 Task Examples

**Emails:**
- `Send an email to john@test.com with subject "Hello"`
- `Draft a new email for maria@company.com`

**Navigation:**
- `Open a new tab and search Python on Google`
- `Click the settings button`

**Simple Tasks:**
- `Click the Play button`
- `Write "Hello world" in the search field`

**Complex Tasks:**
The agent understands complete sequences and generates steps automatically. For example, for "send an email" it understands that it should:
1. Click Compose button
2. Click recipient field
3. Write email
4. Navigate to subject
5. Write subject
6. Etc.

## 🎮 Controls

- **ESC**: Cancels plan execution at any time (requires `keyboard` package installed)
- **Ctrl+C**: Interrupts the program completely
- **Mouse to top-left corner**: PyAutoGUI failsafe (cancels immediately)

## 🏗️ Architecture

### Module Overview

**Config** (`src/config.py`)
- Centralized configuration management
- Environment variable handling
- Validation of required settings

**Exceptions** (`src/exceptions.py`)
- Custom exception hierarchy
- Specific error types for different failure modes

**Logger** (`src/logger.py`)
- Professional logging with emoji support
- Configurable log levels
- Optional file logging

**Screen Capture** (`src/screen_capture.py`)
- Screenshot functionality
- Display scaling detection (Retina support)
- Image encoding for API calls
- Screen change detection

**Grid System** (`src/grid_system.py`)
- Grid overlay generation
- Element location using grid cells
- Coordinate calculation from cell data
- Caching for performance

**OpenAI Client** (`src/openai_client.py`)
- Responses API integration
- Chat Completions for planning
- Automatic retry logic

**Planner** (`src/planner.py`)
- Plan generation from user instructions
- Plan validation
- JSON extraction from responses

**Actions** (`src/actions.py`)
- Individual action execution
- Multi-click pattern for reliability
- Clipboard-based typing
- Screen change verification

**Executor** (`src/executor.py`)
- Complete plan execution
- Error handling and recovery
- Execution statistics
- Temporary file cleanup

### Planning Agent

GPT-4o-mini receives your instruction and generates a structured plan using **common flow patterns**.

The agent knows the typical flows of:
- **Send email**: Compose → Recipient → Subject → Body → Send
- **Web search**: Click on bar → Write → Enter/Search
- **Forms**: Fill fields → Submit

**Input:** "Send an email to john@test.com with subject Hello"

**Output (Generated JSON):**
```json
[
  {"action": "click", "target": "button to compose email"},
  {"action": "wait", "seconds": 1},
  {"action": "click", "target": "text field for recipient"},
  {"action": "type", "text": "john@test.com"},
  {"action": "press", "key": "tab"},
  {"action": "type", "text": "Hello"},
  {"action": "click", "target": "message body area"},
  {"action": "type", "text": "Content ", "loop": true, "loop_duration": 3},
  {"action": "click", "target": "send button"}
]
```

**Note**: The model does NOT use exact button names (avoids hardcoding "Compose", "New", etc.), but generic visual descriptions that work across multiple interfaces.

### Type Action with Loop

The `type` action now supports writing repeatedly:

```json
{
  "action": "type",
  "text": "Text to repeat ",
  "loop": true,
  "loop_duration": 5,
  "delay_between": 0.3
}
```

**Parameters:**
- `text`: Text to write
- `loop`: `true` to activate repeat mode (optional, default: `false`)
- `loop_duration`: Duration in seconds (optional, default: 5)
- `delay_between`: Delay between repetitions in seconds (optional, default: 0.3)

### Execution Loop

Each plan step is executed sequentially:
- **Click**: Screenshot → GPT-4o-mini Vision → Coordinates → PyAutoGUI click
- **Type**: PyAutoGUI writes the text character by character
- **Press**: PyAutoGUI presses the specified key
- **Wait**: Sleep for N seconds

## 🧪 Testing

Run the test suite:

```bash
python -m unittest discover tests
```

Run specific test file:

```bash
python -m unittest tests.test_config
python -m unittest tests.test_planner
```

## ⚡ Advantages of This Approach

- **No Fine-Tuning**: Everything works with intelligent prompting
- **Native Context**: GPT-4o already knows how common apps work
- **Flexible**: Works with any application (Gmail, Slack, browsers, etc.)
- **Self-Correcting**: Continues executing even if a step fails
- **Transparent**: You see the plan before it executes
- **Maintainable**: Clean modular architecture
- **Robust**: Professional error handling and logging

## 📝 Technical Notes

- The `screen.png` file is created/deleted for each click action
- `pyautogui.FAILSAFE = True`: Move mouse to corner cancels
- `pyautogui.PAUSE = 0.5s`: Safety pause between actions
- There's a 0.5s pause between each plan step
- The agent continues executing even if a step fails
- All configuration is centralized in `src/config.py`
- Custom exceptions provide clear error messages

## 🐛 Troubleshooting

### "OPENAI_API_KEY not found"
```bash
export OPENAI_API_KEY='sk-...'
```

### "Permission denied" on macOS
Grant accessibility permissions to Terminal in System Preferences.

### Plan is generated incorrectly
- **Problem**: Model hardcodes exact names ("Compose button") that don't exist
  - **Solution**: The new system uses flow patterns. If it still happens, check the prompt in `src/openai_client.py`
- **Problem**: Steps out of order or missing steps
  - **Solution**: Be more explicit in your instruction. Instead of "send an email", say "draft and send an email to X with subject Y"
- **Problem**: Model generates invalid JSON
  - **Solution**: This is rare with the current prompt. Check logs and report the case

### Steps fail
- Make sure the app is visible on screen
- Some elements take time to load, add `wait` in your instruction
- Check the logs to see what coordinates were detected
- Review the grid overlay in temporary files if available

## 📈 Improvements Implemented

✅ **Removed numpy** - No longer necessary, reducing dependencies
✅ **API key security** - Only accepts keys from environment variables
✅ **Type with loop** - Ability to write repeatedly with duration control
✅ **Clean code** - Refactored search functions, eliminating duplication
✅ **Better cleanup** - All temporary files are removed correctly
✅ **No numpy in verification** - Uses only PIL to compare captures
✅ **ESC cancellation** - Option to cancel execution by pressing ESC (optional, requires `keyboard`)
✅ **Input always required** - User must always specify the task to execute
✅ **Modular architecture** - Clean separation of concerns
✅ **Professional logging** - Structured logging with levels
✅ **Custom exceptions** - Specific error types for better handling
✅ **Type hints** - Full type annotations
✅ **Unit tests** - Basic test coverage

## 📄 License

This project is provided as-is for educational and automation purposes.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows the existing architecture
- New features include tests
- Documentation is updated
- Type hints are included
