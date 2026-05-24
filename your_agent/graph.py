from langgraph.graph import END, START, StateGraph

from .nodes import critic, generator, prompt_writer, saver, should_continue, strategy, web_search
from .state import ThumbnailState


def build_graph() -> StateGraph:
    graph = StateGraph(ThumbnailState)

    graph.add_node("web_search", web_search)
    graph.add_node("strategy", strategy)
    graph.add_node("prompt_writer", prompt_writer)
    graph.add_node("generator", generator)
    graph.add_node("critic", critic)
    graph.add_node("saver", saver)

    graph.add_edge(START, "web_search")
    graph.add_edge("web_search", "strategy")
    graph.add_edge("strategy", "prompt_writer")
    graph.add_edge("prompt_writer", "generator")
    graph.add_edge("generator", "critic")
    graph.add_conditional_edges(
        "critic",
        should_continue,
        {"prompt_writer": "prompt_writer", "saver": "saver"},
    )
    graph.add_edge("saver", END)

    return graph.compile()
