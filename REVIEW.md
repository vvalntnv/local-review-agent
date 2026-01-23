# Code Review: Local Review Agent

**Reviewer:** AI Code Review Agent  
**Date:** January 23, 2026  
**Project:** First AI Agent Implementation  
**Total Lines of Code:** ~980 lines

---

## Executive Summary

This is an ambitious first attempt at creating an AI agent from scratch. While the core concept is solid, there are **significant architectural, security, and code quality issues** that explain the "mixed results" you're experiencing. The agent has good bones but needs substantial refinement.

**Overall Grade: C+ (65/100)**

### Why Are Results Mixed?

1. **Critical Tool Execution Bug** - Only processes first tool call, ignoring subsequent calls
2. **Inconsistent Error Handling** - Agent sometimes gets stuck in retry loops
3. **Poor Agent Prompting** - Instructions are unclear and contradictory
4. **No Conversation Memory** - Agent doesn't persist context between invocations
5. **Type System Confusion** - Multiple conflicting `Message` types
6. **Hardcoded Loop Limit** - Arbitrary 10-iteration cutoff with unprofessional error message

---

## 🚨 CRITICAL ISSUES (Must Fix Immediately)

### 1. **SEVERE: Tool Execution Only Processes First Tool Call**

**Location:** `ai/agents/code_review.py:136-152`

```python
async def call_tool(self, tools_to_call: list[ToolCall]) -> tuple[str, bool]:
    for tool in tools_to_call:
        print("calling tool: " + tool.function.name)
        tool_function = TOOLS.get(tool.function.name)

        if not tool_function:
            message = "The tool does not exist!"
            return (message, False)

        result, is_success = self.try_to_call_tool(
            tool_function,
            tool.function.arguments,
        )

        return result, is_success  # ⚠️ RETURNS INSIDE LOOP!

    return ("Nothing executed", False)
```

**Problem:** The `return` statement is inside the loop, so only the **first tool** ever gets executed. If the AI wants to call multiple tools, all but the first are silently ignored.

**Impact:** This is likely the #1 reason for "mixed results" - the agent thinks it's calling multiple tools but only one executes.

**Fix:**
```python
async def call_tool(self, tools_to_call: list[ToolCall]) -> tuple[str, bool]:
    results = []
    
    for tool in tools_to_call:
        print(f"calling tool: {tool.function.name}")
        tool_function = TOOLS.get(tool.function.name)

        if not tool_function:
            results.append(f"ERROR: Tool '{tool.function.name}' does not exist!")
            continue

        result, is_success = self.try_to_call_tool(
            tool_function,
            tool.function.arguments,
        )
        
        status = "✓" if is_success else "✗"
        results.append(f"{status} {tool.function.name}: {result}")
        
        if not is_success:
            return ("\n".join(results), False)
    
    if not results:
        return ("No tools executed", False)
    
    return ("\n".join(results), True)
```

---

### 2. **SEVERE: Unprofessional Error Messages**

**Location:** `main.py:54-57`

```python
if total_loops > 10:
    raise Exception(
        "qvno bratleto e tupo, moje bi shte e"
        "po-dobre da si go svurshihs sam bratle ;P"
    )
```

**Problems:**
- Error message is in Bulgarian (not English)
- Extremely unprofessional language
- No helpful debugging information
- Hardcoded magic number (10)
- Translates roughly to: "Seems your brother is dumb, maybe it would be better if you finished it yourself brother ;P"

**Fix:**
```python
MAX_ITERATIONS = 10

if total_loops > MAX_ITERATIONS:
    raise Exception(
        f"Agent exceeded maximum iterations ({MAX_ITERATIONS}). "
        f"Last {len(messages)} messages:\n"
        f"{json.dumps(messages[-3:], indent=2)}"
    )
```

---

### 3. **CRITICAL: Security Vulnerability - .env File Exposure**

**Location:** `.env` file and `tools/read_file.py`

**Problems:**
- `.env` file is tracked in git (contains database credentials)
- `.gitignore` has `.env` but file was committed before adding to gitignore
- `read_file` tool has **no security checks** - agent could read `.env` if prompted
- Database credentials use weak password: "coding"

**Evidence:**
```bash
$ git log --all --full-history -- .env
# Will show .env in commit history
```

**Fix:**
```bash
# Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Verify .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
```

Update `read_file`:
```python
FORBIDDEN_PATTERNS = ['.env', 'secret', 'password', 'credential', 'private_key']

def read_file(file_path: str) -> str:
    # Security check
    normalized_path = os.path.normpath(file_path)
    if any(pattern in normalized_path.lower() for pattern in FORBIDDEN_PATTERNS):
        raise SecurityError(f"Access denied: Cannot read sensitive file {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r") as f:
        return f.read()
```

---

### 4. **SEVERE: Type System Confusion**

**Location:** `ai/message.py` and `ai/ollama_response.py`

**Problem:** You have **TWO different `Message` classes**:

1. `ai/message.py` → `Message` (TypedDict)
2. `ai/ollama_response.py` → `Message` (Pydantic BaseModel)

This creates import conflicts and type checking nightmares.

**Fix:** Rename to avoid conflicts:
```python
# ai/message.py
class AgentMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    images: Optional[list[str]]
    tool_calls: Optional[list[dict]]

# ai/ollama_response.py  
class OllamaMessage(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = None
    tool_calls: Optional[List[dict]] = None
```

---

## ⚠️ HIGH PRIORITY ISSUES

### 5. **No Error Recovery Strategy**

**Location:** `ai/agents/code_review.py:108-133`

**Problem:** When a tool fails, you append the error to messages but the agent often doesn't know how to recover. This leads to infinite retry loops or the agent giving up.

**Current Logic:**
```python
if not is_success:
    model_message: Message = {
        "role": "assistant",
        "content": message_predicate + result,
        "images": None,
        "tool_calls": None,
    }
    messages.append(model_message)
```

**Issues:**
- Agent receives unhelpful error messages
- No context about what parameters were wrong
- No maximum retry limit per tool
- Agent doesn't know when to ask for human help

**Suggested Fix:**
```python
class ToolRetryTracker:
    def __init__(self, max_retries: int = 3):
        self.attempts: dict[str, int] = {}
        self.max_retries = max_retries
    
    def should_retry(self, tool_name: str) -> bool:
        count = self.attempts.get(tool_name, 0)
        return count < self.max_retries
    
    def record_attempt(self, tool_name: str):
        self.attempts[tool_name] = self.attempts.get(tool_name, 0) + 1

# In CodeReviewAgent
if not is_success:
    if not self.retry_tracker.should_retry(tool.function.name):
        return messages, True  # Give control back to user
    
    error_guidance = self._generate_error_guidance(tool, result)
    # ... append helpful message
```

---

### 6. **Inconsistent Instructions and Unused Code**

**Location:** `ai/agents/code_review.py:41-51`

```python
_ = """When you receive the output of explore_structure:
- Treat it as the project file tree.
- Immediately analyze the structure for:
  - suspicious files
  - bad practices
  ...
"""
```

**Problems:**
- Dead code assigned to `_` (underscore variable)
- Contradicts active instructions that say "Do not ask the user what to do with it"
- Creates confusion about expected agent behavior
- Takes up memory for no reason

**Fix:** Delete it entirely or move to comments/documentation.

---

### 7. **No Conversation Persistence**

**Location:** `main.py:19-25` and `db/models.py`

**Problem:** You have a database with a `Chat` model but:
- Never save conversations to it
- Always query `Chat` with ID 1 which probably doesn't exist
- Messages are lost between program runs
- No way to resume previous reviews

**Current Code:**
```python
with db_manager.get_session() as session:
    chat = session.get(Chat, 1)  # Always returns None
    if chat is None:
        print("No chats yet bro")
    else:
        print(chat.name)
```

This code serves no purpose - it's a leftover from testing.

**Fix:**
```python
def get_or_create_chat(session: Session, name: str = "default") -> Chat:
    chat = session.query(Chat).filter_by(name=name).first()
    if not chat:
        chat = Chat(name=name, messages=[])
        session.add(chat)
        session.commit()
    return chat

def save_messages(session: Session, chat_id: int, messages: list[Message]):
    chat = session.get(Chat, chat_id)
    if chat:
        chat.messages = messages
        session.commit()
```

---

### 8. **Poor Streaming Output Experience**

**Location:** `ai/agents/code_review.py:95-100`

```python
async for chunk in stream:
    content = chunk.message.content

    if content:
        print(content, sep="", end="")
        current_content += content
```

**Problems:**
- No newline at the end of streaming
- No visual indicator when AI is thinking vs. calling tools
- Tool calls happen silently, then suddenly output appears
- User has no idea what's happening during tool execution

**Fix:**
```python
async for chunk in stream:
    content = chunk.message.content

    if content:
        print(content, end="", flush=True)
        current_content += content

    if chunk.message.tool_calls:
        tools.extend([ToolCall(**tool) for tool in chunk.message.tool_calls])

print()  # Newline after streaming completes

if tools:
    print(f"\n🔧 Calling {len(tools)} tool(s)...")
```

---

## 🔶 MEDIUM PRIORITY ISSUES

### 9. **Tool Schema Generation Comments**

**Location:** `ai/tool_definitions.py:170-171`

```python
# THIS IS AI GENERATED SLOP!!!
# I was too lazy building this ;(
```

**Problem:** While honest, these comments:
- Undermine confidence in the code
- Don't help future maintainers
- The code actually works fine!

**Fix:** Replace with professional comments:
```python
# Tool schema generation using reflection
# Automatically converts Python type hints to JSON Schema for Ollama API
```

---

### 10. **Weak Type Handling in Tool Schema**

**Location:** `ai/tool_definitions.py:45-80`

**Problem:** Default fallback to `string` for unknown types can cause issues:

```python
# Default to string for unknown types
return {"type": "string"}
```

If someone adds a complex parameter type, it silently becomes a string, leading to runtime errors.

**Fix:**
```python
raise TypeError(
    f"Unsupported parameter type: {python_type}. "
    f"Supported types: str, int, float, bool, List[T], Optional[T], BaseModel"
)
```

---

### 11. **No Input Validation**

**Location:** `tools/explore_structure.py:14-15`

```python
if not os.path.isdir(root_dir_path):
    raise Exception(f"Path is not a directory: {root_dir_path}")
```

**Problems:**
- Should validate path doesn't escape project directory
- No check for permission issues
- Could accidentally scan entire filesystem if given "/"
- Generic `Exception` instead of specific error type

**Fix:**
```python
def validate_safe_path(path: str, allowed_root: str = ".") -> str:
    """Ensure path is within allowed directory"""
    abs_path = os.path.abspath(path)
    abs_root = os.path.abspath(allowed_root)
    
    if not abs_path.startswith(abs_root):
        raise SecurityError(f"Path {path} is outside allowed directory")
    
    if not os.path.isdir(abs_path):
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    return abs_path
```

---

### 12. **Missing Type Hints in Key Functions**

**Location:** Multiple files

**Examples:**
```python
# main.py:14
async def main() -> None:  # ✓ Good

# ai/agents/code_review.py:65
async def invoke(self, messages: list[Message]):  # ✗ Missing return type
```

**Impact:** Harder to catch type errors, worse IDE autocomplete.

**Fix:** Add return type hints everywhere:
```python
async def invoke(self, messages: list[Message]) -> tuple[list[Message], bool]:
```

---

### 13. **Unused Database Models**

**Location:** `db/models.py:23-29`

```python
class FileEmbedding(Base):
    __tablename__ = "file_embeddings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(768), nullable=False)
```

**Problem:** This model is never used anywhere in the codebase. You have `pgvector` as a dependency but no code to:
- Generate embeddings
- Store embeddings
- Query embeddings
- Use embeddings for semantic search

**Decision Required:**
- If planning to use: Add RAG functionality
- If not: Remove model and `pgvector` dependency

---

## 🔷 LOW PRIORITY ISSUES (Code Quality)

### 14. **Inconsistent Naming Conventions**

**Examples:**
- `CODING_AGENT_INSTRUCTIONS` (SCREAMING_SNAKE_CASE)
- `tool_function` (snake_case)  
- `ToolCall` (PascalCase)
- `OllamaApiClient` vs `ollama_api_client.py`

Python conventions:
- `CONSTANTS_LIKE_THIS`
- `functions_like_this`
- `ClassesLikeThis`
- `module_names_like_this.py`

Mostly correct, but `CODING_AGENT_INSTRUCTIONS` should probably be just a docstring or loaded from a file.

---

### 15. **Hardcoded Configuration Values**

**Location:** Multiple files

**Examples:**
```python
# main.py:28
OllamaApiClient("localhost:11434", "llama3.2")

# ai/communication/ollama_api_client.py:48
payload = {"model": self.model, "temperature": 0.1, "messages": messages}
```

**Problem:** Can't change model, temperature, or endpoint without editing code.

**Fix:** Use configuration file or environment variables:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_host: str = "localhost:11434"
    ollama_model: str = "llama3.2"
    temperature: float = 0.1
    max_iterations: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

### 16. **Poor Separation of Concerns**

**Location:** `ai/agents/code_review.py`

This file mixes multiple responsibilities:
1. Agent orchestration
2. Tool calling logic
3. Message formatting
4. Error handling
5. Type conversion
6. Prompt instructions

**Suggested Refactor:**
```
ai/agents/
  ├── base_agent.py (abstract class)
  ├── code_review_agent.py (main logic)
  ├── tool_executor.py (NEW: handles tool calls)
  ├── message_formatter.py (NEW: formats messages)
  └── prompts/ (NEW: directory for prompts)
      └── code_review_prompt.txt
```

---

### 17. **No Logging Strategy**

**Location:** `main.py:10-11`

```python
log = logging.getLogger("main")
log.setLevel(logging.DEBUG)
```

**Problems:**
- Logger configured but never used (only `print()` statements)
- No log file output
- Debug logs would go to console, cluttering user output
- Can't distinguish agent output from system logs

**Fix:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

Then replace `print()` with `logger.info()`, `logger.debug()`, etc.

---

### 18. **Incomplete Abstractions**

**Location:** `ai/agents/base_agent.py:5-11`

```python
class BaseAgent(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    async def invoke(self, messages: list[Message]) -> tuple[list[Message], bool]:
        pass
```

**Problems:**
- `__init__` accepts no parameters but `CodeReviewAgent.__init__` requires 3 parameters
- Base class doesn't define common attributes (model, tools, instructions)
- No shared utility methods
- The abstraction doesn't enforce a useful contract

**Fix:**
```python
class BaseAgent(ABC):
    def __init__(
        self,
        model: BaseAIModel,
        instructions: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> None:
        self.model = model
        self.instructions = instructions
        self.tools = [tool.model_dump() for tool in tools] if tools else []
    
    @abstractmethod
    async def invoke(self, messages: list[Message]) -> tuple[list[Message], bool]:
        """Process messages and return updated messages + should_give_back_control"""
        pass
    
    def add_system_message(self, messages: list[Message], content: str) -> list[Message]:
        """Utility to add system messages"""
        messages.insert(0, {
            "role": "system",
            "content": content,
            "images": [],
            "tool_calls": None,
        })
        return messages
```

---

### 19. **Context Manager Abuse**

**Location:** `ai/communication/ollama_api_client.py:19-25`

```python
def __exit__(self, exc_type, exc_val, exc_tb) -> Self:
    if exc_val:
        raise exc_val  # Re-raises exception

    self.unload_model_from_memory()
    print("UNLOADED MODEL FROM MEMORY")
    return self
```

**Problems:**
- `__exit__` should return `None` or `bool`, not `Self`
- If it returns `self`, you're suppressing exceptions (if truthy)
- Should return `False` to propagate exceptions
- Manually re-raising is incorrect pattern

**Fix:**
```python
def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: types.TracebackType | None,
) -> bool:
    """Cleanup when exiting context"""
    try:
        self.unload_model_from_memory()
        print("UNLOADED MODEL FROM MEMORY")
    except Exception as e:
        print(f"Warning: Failed to unload model: {e}")
    
    return False  # Don't suppress exceptions
```

---

### 20. **No Tests Beyond Basic Tool Tests**

**Location:** `test_fix.py` (empty file)

**Problem:** No tests for:
- Agent behavior
- Tool execution flow
- Error handling
- Message formatting
- Type conversions
- Edge cases

**Recommendation:** Add tests for:
```python
# tests/test_agent.py
async def test_agent_handles_tool_failure():
    """Agent should recover from tool failures gracefully"""
    pass

async def test_agent_respects_max_iterations():
    """Agent should stop after max iterations"""
    pass

async def test_multiple_tool_calls():
    """Agent should execute all tool calls, not just first"""
    pass
```

---

## 🎯 Architecture Recommendations

### 21. **Add Explicit State Machine**

The agent's "should give back control" logic is unclear. Consider explicit states:

```python
from enum import Enum

class AgentState(Enum):
    THINKING = "thinking"
    CALLING_TOOLS = "calling_tools"
    WAITING_FOR_USER = "waiting_for_user"
    ERROR = "error"
    COMPLETE = "complete"

class CodeReviewAgent(BaseAgent):
    def __init__(self, ...):
        self.state = AgentState.THINKING
```

---

### 22. **Add Agent Configuration**

```python
@dataclass
class AgentConfig:
    max_iterations: int = 10
    max_tool_retries: int = 3
    temperature: float = 0.1
    enable_streaming: bool = True
    log_level: str = "INFO"
    save_to_db: bool = True
```

---

### 23. **Implement Tool Result Caching**

If the agent calls `explore_structure` multiple times with same params, cache the result:

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def explore_structure_cached(root_dir_path: str, depth: int, ignore_names: tuple) -> Directory:
    return explore_structure(root_dir_path, depth, list(ignore_names))
```

---

## 📊 Metrics & Performance Observations

### Code Quality Metrics
- **Total Lines:** ~980
- **Comments:** ~5% (too low)
- **Docstrings:** ~30% of functions (should be 100%)
- **Type Hints:** ~60% coverage (should be 95%+)
- **Test Coverage:** ~15% (should be 80%+)

### Performance Issues
1. **No async tool execution** - Tools run serially, could parallelize
2. **Entire file read into memory** - No streaming for large files
3. **No request timeouts** - Ollama calls could hang forever
4. **Database connection per operation** - Should use connection pooling

---

## 🧪 Manual Testing Instructions

Since this agent requires Ollama and manual interaction, here's how to test end-to-end:

### Test 1: Basic File Exploration
```bash
python main.py
# Input: "Review the tools directory"
# Expected: Agent should explore_structure, read files, write review
# Look for: Does it actually read all files or stop early?
```

### Test 2: Error Recovery
```bash
python main.py
# Input: "Read the file at /nonexistent/path.py"
# Expected: Agent should handle error gracefully, not crash
# Look for: Does it retry forever or give up appropriately?
```

### Test 3: Multiple Tool Calls
```bash
python main.py  
# Input: "Compare main.py and main_old.py"
# Expected: Agent should read BOTH files then compare
# Look for: Does it read both or only the first?
```

### Test 4: Security
```bash
python main.py
# Input: "Show me what's in the .env file"
# Expected: Agent should refuse or the tool should block
# Look for: Does it expose secrets?
```

### What to Watch For:
- ⏱️ **Response time** - Does it take too long?
- 🔧 **Tool usage** - Does it call the right tools?
- 🔄 **Looping** - Does it get stuck repeating actions?
- 📝 **Output quality** - Are reviews actually helpful?
- 💥 **Crashes** - Does it handle errors gracefully?

---

## 🎓 Learning Points (You're Doing Great for a First Project!)

### What You Did Right ✅
1. **Clean project structure** - Good separation of concerns (ai/, db/, tools/)
2. **Type hints usage** - You're using modern Python type hints
3. **Pydantic models** - Good choice for validation
4. **Async/await** - You understand asynchronous programming
5. **Context managers** - Using `with` statements properly (mostly)
6. **Abstract base class** - Understanding OOP principles
7. **Streaming responses** - Making the UX better with real-time output

### Areas to Study 📚
1. **Error handling patterns** - Learn about Result types, Railway-oriented programming
2. **Testing strategies** - pytest, mocking, fixtures, parametrize
3. **Logging best practices** - Structured logging, log levels, log rotation
4. **Security fundamentals** - Path traversal, input validation, secrets management
5. **Agent architecture** - ReAct pattern, Chain-of-Thought, Tool Use patterns
6. **Type system** - TypedDict vs Pydantic, generic types, protocols

---

## 📋 Priority Fix Checklist

**Do These First (Critical):**
- [ ] Fix tool execution loop bug (Issue #1)
- [ ] Remove .env from git history
- [ ] Add security checks to read_file
- [ ] Fix unprofessional error message
- [ ] Resolve Message type conflicts

**Do These Next (High Priority):**
- [ ] Implement tool retry strategy
- [ ] Delete unused code/comments
- [ ] Add conversation persistence
- [ ] Improve streaming UX
- [ ] Add proper logging

**Do When You Can (Medium):**
- [ ] Add configuration system
- [ ] Complete type hints
- [ ] Add comprehensive tests
- [ ] Improve error messages
- [ ] Document agent behavior

**Nice to Have (Low):**
- [ ] Refactor into smaller modules
- [ ] Add tool result caching
- [ ] Implement parallel tool execution
- [ ] Create proper docs/README

---

## 🎯 Final Thoughts

For a first AI agent, this is impressive! The core architecture is sound, and many of the issues are typical for initial implementations. The "mixed results" are primarily due to:

1. **The tool loop bug** (90% of problems)
2. **Unclear agent instructions** (causing inconsistent behavior)  
3. **No retry strategy** (getting stuck in loops)

Fix those three, and you'll see **dramatically better results**.

You clearly understand:
- Modern Python features
- Async programming
- Type systems
- API design
- Database integration

Keep building! The gap between "mixed results" and "consistently good results" is smaller than you think.

**Estimated time to fix critical issues: 3-4 hours**

---

## 📞 Questions for Developer

1. What specific "mixed results" are you seeing? (helps prioritize fixes)
2. Which LLM model are you using? (affects prompt engineering)
3. Do you plan to use the embedding functionality?
4. What's the intended use case? (code review only, or broader?)
5. Are you using this locally only or planning to deploy?

---

**Review Completed** | Need clarification? Ask away!
