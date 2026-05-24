import argparse
import sys
from datetime import datetime
from pathlib import Path

import your_agent  # noqa: F401 — triggers load_dotenv()
from your_agent.graph import build_graph


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text)[:60]


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Thumbnail Designer (Reflexion Agent)")
    parser.add_argument("topic", help='Video topic, e.g. "Why Python is the best language for AI"')
    parser.add_argument("--target-rating", type=int, default=8, help="Stop when critic scores >= this (default 8)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Hard cap on iterations (default 3)")
    parser.add_argument("--stream", action="store_true", help="Print each node update as it arrives")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = str(Path("outputs") / f"{timestamp}_{slugify(args.topic)}")

    initial_state = {
        "topic": args.topic,
        "search_summary": "",
        "strategy": {},
        "current_prompt": "",
        "image_path": "",
        "rating": 0,
        "critique": "",
        "iteration": 0,
        "target_rating": args.target_rating,
        "max_iterations": args.max_iterations,
        "output_dir": output_dir,
        "history": [],
    }

    graph = build_graph()

    if args.stream:
        for step in graph.stream(initial_state, stream_mode="updates"):
            for node_name, update in step.items():
                print(f"\n{'='*60}")
                print(f"Node: {node_name}")
                if not update:
                    continue
                for k, v in update.items():
                    if k == "history":
                        for rec in v:
                            print(f"  [history] iter={rec['iteration']} rating={rec['rating']}/10")
                            print(f"  critique: {rec['critique'][:120]}...")
                    elif k not in ("search_summary", "current_prompt"):
                        print(f"  {k}: {v}")
                    else:
                        preview = str(v)[:100].replace("\n", " ")
                        print(f"  {k}: {preview}...")
    else:
        final = graph.invoke(initial_state)
        print(f"\nDone! Best rating: {final['rating']}/10 after {final['iteration']} iteration(s).")
        print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
