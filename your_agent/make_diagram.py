"""Generate a PNG of the LangGraph state machine and save it as graph.png."""
from pathlib import Path

import your_agent  # noqa: F401 — triggers load_dotenv()
from your_agent.graph import build_graph


def main() -> None:
    graph = build_graph()
    png_bytes = graph.get_graph().draw_mermaid_png()
    out = Path("graph.png")
    out.write_bytes(png_bytes)
    print(f"Graph diagram saved → {out.resolve()}")


if __name__ == "__main__":
    main()
