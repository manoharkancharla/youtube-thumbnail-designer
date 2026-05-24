# Assignment 1: YouTube Thumbnail Designer (Reflexion Agent)

A LangGraph-based agent that iteratively designs and refines YouTube thumbnails using DALL-E 3 and GPT-4o vision critique.

## Architecture

```
START → web_search → prompt_writer → generator → critic ─┐
                         ↑                                │  (rating < target AND iteration < max)
                         └────────── should_continue ◄───┤
                                           │              (rating >= target OR iteration >= max)
                                           ↓
                                         saver → END
```

5 nodes + 1 conditional edge (`should_continue`) implement the reflexion loop.

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   # or with uv:
   uv sync
   ```

## Usage

```bash
# Basic run
python -m your_agent.main "Why Python is the best language for AI"

# Stream live node updates
python -m your_agent.main "Why Python is the best language for AI" --stream

# Custom thresholds
python -m your_agent.main "..." --target-rating 9 --max-iterations 5

# Generate graph diagram
python -m your_agent.make_diagram
```

## Output

Each run creates `outputs/<timestamp>_<topic>/`:
- `iter_1.png`, `iter_2.png`, … — one PNG per iteration
- `final.png` — the highest-rated thumbnail
- `report.md` — full history: prompt used, score, and critique per iteration

