"""
ArXivLens Benchmark & Evaluation Suite.
Misst Latenzen, Hit-Rates und den Re-Ranking-Effekt von FlashRank im Vergleich zu BM25 und Dense Search.
"""

import sys
import time
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from src.ingestion.pdf_parser import PaperChunk
from src.retrieval.bm25_index import BM25SearchIndex
from src.retrieval.hybrid import HybridSearchEngine, SearchResult
from src.retrieval.reranker import FlashRankReranker

def run_benchmark():
    print("\n" + "=" * 65)
    print("🔬 ARXIVLENS: RETRIEVAL & RE-RANKING BENCHMARK REPORT")
    print("=" * 65)

    # 1. Synthetischen wissenschaftlichen Korpus anlegen
    sample_chunks = [
        PaperChunk(
            chunk_id="chunk_attention",
            paper_id="1706.03762",
            title="Attention Is All You Need",
            section="Architecture",
            page_number=3,
            text="An attention function can be described as mapping a query and a set of key-value pairs to an output. We compute the matrix of outputs as Softmax(QK^T / sqrt(d_k)) * V."
        ),
        PaperChunk(
            chunk_id="chunk_bleu",
            paper_id="1706.03762",
            title="Attention Is All You Need",
            section="Experiments",
            page_number=5,
            text="On the WMT 2014 English-to-German translation task, the big transformer model achieves a BLEU score of 28.4, outperforming the existing best models by more than 2.0 BLEU."
        ),
        PaperChunk(
            chunk_id="chunk_rag_intro",
            paper_id="2005.11401",
            title="RAG for Knowledge-Intensive NLP",
            section="Introduction",
            page_number=1,
            text="Retrieval-Augmented Generation (RAG) models combine pre-trained parametric memory (seq2seq generator) with non-parametric memory (dense vector index of Wikipedia)."
        ),
        PaperChunk(
            chunk_id="chunk_hardware",
            paper_id="1706.03762",
            title="Attention Is All You Need",
            section="Training",
            page_number=6,
            text="We trained our models on one machine with 8 NVIDIA P100 GPUs. For base models, each training step took about 0.4 seconds."
        )
    ]

    # 2. BM25 Index vorbereiten
    t0 = time.perf_counter()
    bm25 = BM25SearchIndex()
    bm25.add_chunks(sample_chunks)
    bm25_index_time = (time.perf_counter() - t0) * 1000

    # 3. Test-Queries evaluieren
    test_queries = [
        {"query": "What BLEU score did the transformer achieve?", "target_id": "chunk_bleu"},
        {"query": "How is the scaled dot-product attention computed?", "target_id": "chunk_attention"},
        {"query": "What is the difference between parametric and non-parametric memory in RAG?", "target_id": "chunk_rag_intro"}
    ]

    hybrid = HybridSearchEngine(rrf_k=60)
    reranker = FlashRankReranker()

    print(f"\n[✓] Indexierung abgeschlossen in {bm25_index_time:.2f} ms")
    print("\nEvaluierung der Testanfragen:")
    print("-" * 65)
    print(f"{'Query':<35} | {'BM25 Hit':<10} | {'Re-Rank Score':<12}")
    print("-" * 65)

    latencies = []
    for item in test_queries:
        q = item["query"]
        target = item["target_id"]

        t_start = time.perf_counter()
        
        # BM25 Search
        bm_res = bm25.search(q, top_k=3)
        bm_hit = any(r["chunk_id"] == target for r in bm_res)

        # Simuliertes RRF
        fused = hybrid.fuse(dense_results=[], bm25_results=bm_res, top_k=3)

        # FlashRank Re-Ranking
        reranked = reranker.rerank(query=q, results=fused, top_k=2)
        latency = (time.perf_counter() - t_start) * 1000
        latencies.append(latency)

        best_score = reranked[0].rerank_score if reranked else 0.0
        hit_str = "PASS" if bm_hit else "MISS"
        print(f"{q[:33]:<35} | {hit_str:<10} | {best_score:<12.4f}")

    avg_lat = sum(latencies) / len(latencies)
    print("-" * 65)
    print(f"📊 Durchschnittliche Pipeline-Latenz (BM25 + FlashRank): {avg_lat:.2f} ms")
    print("=" * 65)
    print("✅ Benchmark erfolgreich beendet.\n")

if __name__ == "__main__":
    run_benchmark()
