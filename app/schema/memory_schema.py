"""
Memory tools for the ReAct agent loop.
search_knowledge_base and retrieve_memory have been removed —
document questions route through the RAG pipeline before the ReAct loop,
and three-layer memory is pre-loaded into the model preamble by the orchestrator.
"""
memory_schema = []
