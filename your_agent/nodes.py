import base64
import shutil
from pathlib import Path

from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field

from .prompts import CRITIC_SYSTEM, PROMPT_WRITER_SYSTEM, STRATEGY_SYSTEM
from .state import IterationRecord, ThumbnailState
from .tools import search_web


# ─── Structured output schemas ───────────────────────────────────────────────

class StrategyOutput(BaseModel):
    main_subject: str = Field(..., description="The primary visual subject — specific, not generic")
    topic_symbols: list[str] = Field(..., description="2-3 iconic visual symbols tied to the topic (logos, icons, objects)")
    emotion: str = Field(..., description="Emotional tone the thumbnail should evoke")
    background: str = Field(..., description="Background setting and atmosphere")
    style: str = Field(..., description="Visual style: hyper-realistic, bold graphic design, etc.")
    text_overlay: str = Field(..., description="Short punchy text (max 5 words) for the thumbnail")
    text_placement: str = Field(..., description="Where the text goes and how it contrasts")
    attention_hook: str = Field(..., description="The curiosity or emotion trigger that compels a click")
    color_palette: str = Field(..., description="2-3 dominant colours and why they fit the topic")


class CriticOutput(BaseModel):
    rating: int = Field(..., ge=1, le=10, description="Score from 1 (terrible) to 10 (exceptional)")
    critique: str = Field(..., description="Actionable critique: what to fix in the next iteration")


# ─── Nodes ──────────────────────────────────────────────────────────────────

def web_search(state: ThumbnailState) -> dict:
    topic = state["topic"]
    query = f"YouTube thumbnail design ideas hooks visual style for: {topic}"
    summary = search_web(query)
    return {"search_summary": summary}


def strategy(state: ThumbnailState) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    structured_llm = llm.with_structured_output(StrategyOutput)

    from langchain_core.messages import HumanMessage, SystemMessage
    result: StrategyOutput = structured_llm.invoke([
        SystemMessage(content=STRATEGY_SYSTEM),
        HumanMessage(content=f"Video topic: {state['topic']}\n\nWeb research:\n{state['search_summary']}"),
    ])
    return {"strategy": result.model_dump()}


def prompt_writer(state: ThumbnailState) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)

    s = state.get("strategy") or {}
    strategy_text = ""
    if s:
        symbols = ", ".join(s.get("topic_symbols", []))
        strategy_text = (
            f"\n\nVisual blueprint:\n"
            f"- Main subject: {s.get('main_subject', '')}\n"
            f"- Topic symbols to include: {symbols}\n"
            f"- Emotion: {s.get('emotion', '')}\n"
            f"- Background: {s.get('background', '')}\n"
            f"- Style: {s.get('style', '')}\n"
            f"- Text overlay: \"{s.get('text_overlay', '')}\" — {s.get('text_placement', '')}\n"
            f"- Attention hook: {s.get('attention_hook', '')}\n"
            f"- Color palette: {s.get('color_palette', '')}\n"
        )

    user_content = f"Video topic: {state['topic']}\n\nWeb research:\n{state['search_summary']}{strategy_text}"
    if state.get("critique"):
        user_content += (
            f"\n\nPrevious attempt scored {state['rating']}/10.\n"
            f"Critique to address:\n{state['critique']}\n\n"
            "Write a new, improved prompt that fixes every point above."
        )

    from langchain_core.messages import HumanMessage, SystemMessage
    response = llm.invoke([
        SystemMessage(content=PROMPT_WRITER_SYSTEM),
        HumanMessage(content=user_content),
    ])
    return {"current_prompt": response.content.strip()}


def generator(state: ThumbnailState) -> dict:
    client = OpenAI()
    iteration = state.get("iteration", 0) + 1
    output_dir = state["output_dir"]

    response = client.images.generate(
        model="gpt-image-1",
        prompt=state["current_prompt"],
        size="1536x1024",
        quality="medium",
        n=1,
    )

    image_bytes = base64.b64decode(response.data[0].b64_json)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    image_path = str(Path(output_dir) / f"iter_{iteration}.png")
    Path(image_path).write_bytes(image_bytes)

    return {"image_path": image_path, "iteration": iteration}


def critic(state: ThumbnailState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    structured_llm = llm.with_structured_output(CriticOutput)

    img_b64 = base64.b64encode(Path(state["image_path"]).read_bytes()).decode()

    from langchain_core.messages import HumanMessage, SystemMessage
    result: CriticOutput = structured_llm.invoke([
        SystemMessage(content=CRITIC_SYSTEM),
        HumanMessage(content=[
            {"type": "text", "text": (
                f"Topic: {state['topic']}\n"
                f"Prompt used: {state['current_prompt']}\n\n"
                "Rate this YouTube thumbnail strictly. Return structured output only."
            )},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        ]),
    ])

    record: IterationRecord = {
        "iteration": state["iteration"],
        "prompt": state["current_prompt"],
        "image_path": state["image_path"],
        "rating": result.rating,
        "critique": result.critique,
    }

    return {
        "rating": result.rating,
        "critique": result.critique,
        "history": [record],
    }


def saver(state: ThumbnailState) -> dict:
    output_dir = Path(state["output_dir"])
    history = state["history"]

    best = max(history, key=lambda r: r["rating"])
    final_path = output_dir / "final.png"
    shutil.copy(best["image_path"], final_path)

    lines = [
        f"# YouTube Thumbnail Report",
        f"",
        f"**Topic:** {state['topic']}",
        f"**Best score:** {best['rating']}/10 (iteration {best['iteration']})",
        f"**Total iterations:** {state['iteration']}",
        f"",
        f"---",
        f"",
    ]
    for record in history:
        lines += [
            f"## Iteration {record['iteration']}",
            f"",
            f"**Score:** {record['rating']}/10",
            f"",
            f"**Prompt:**",
            f"",
            f"> {record['prompt']}",
            f"",
            f"**Critique:**",
            f"",
            f"{record['critique']}",
            f"",
            f"**Image:** `{Path(record['image_path']).name}`",
            f"",
            f"---",
            f"",
        ]

    (output_dir / "report.md").write_text("\n".join(lines))
    print(f"\nSaved final thumbnail → {final_path}")
    print(f"Saved report         → {output_dir / 'report.md'}")
    return {}


# ─── Conditional edge ────────────────────────────────────────────────────────

def should_continue(state: ThumbnailState) -> str:
    rating = state.get("rating", 0)
    iteration = state.get("iteration", 0)
    target = state.get("target_rating", 8)
    max_iter = state.get("max_iterations", 3)

    if rating >= target or iteration >= max_iter:
        return "saver"
    return "prompt_writer"
