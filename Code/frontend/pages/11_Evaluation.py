import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import json
import os
import pandas as pd
from rag.prompts import get_qa_prompt
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Benchmark Evaluation Runner")
st.markdown("Execute the automated benchmark against 20 ground-truth domain questions from `Input_Data/evaluation/evaluation_questions.json`.")

eval_file_path = Path('c:/TARA/Input_Data/evaluation/evaluation_questions.json')
if not eval_file_path.exists():
    eval_file_path = Path(__file__).parent.parent.parent / "Input_Data" / "evaluation" / "evaluation_questions.json"

if st.button("Run Evaluation", type="primary"):
    if not eval_file_path.exists():
        st.error(f"Evaluation benchmark file not found at {eval_file_path}")
    else:
        try:
            with open(eval_file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                
            results = []
            progress = st.progress(0)
            status_text = st.empty()
            
            total_attempted = len(questions)
            completed = 0
            retrieval_successes = 0
            concept_matches = 0
            latencies = []
            failures = 0

            for i, q in enumerate(questions):
                query = q.get('question', '')
                category = q.get('category', 'general')
                expected_elements = q.get('expected_elements', [])
                status_text.text(f"Evaluating ({i+1}/{total_attempted}): [{category}] {query[:60]}...")
                
                t_start = time.time()
                try:
                    citations = retriever.retrieve(query, 5, None)
                    context_chunks = [c.chunk_text for c in citations]
                    prompt = get_qa_prompt(query, context_chunks)
                    answer = llm_client.generate(prompt, "You are an automotive cybersecurity evaluator AI.")
                    dur = time.time() - t_start
                    latencies.append(dur)
                    completed += 1

                    if citations and len(citations) > 0:
                        retrieval_successes += 1

                    # Check expected elements in answer
                    answer_lower = answer.lower()
                    matched_elements = [el for el in expected_elements if el.lower() in answer_lower]
                    if len(expected_elements) > 0:
                        concept_coverage = len(matched_elements) / len(expected_elements)
                    else:
                        concept_coverage = 1.0
                    
                    if concept_coverage >= 0.5:
                        concept_matches += 1

                    results.append({
                        "ID": q.get('id', i+1),
                        "Category": category,
                        "Question": query,
                        "Retrieved Chunks": len(citations),
                        "Concept Coverage": f"{int(concept_coverage * 100)}%",
                        "Latency (s)": round(dur, 2),
                        "Top Source": citations[0].document_name if citations else "None",
                        "Answer Preview": (answer[:120] + "...") if len(answer) > 120 else answer
                    })
                except Exception as ex:
                    failures += 1
                    latencies.append(time.time() - t_start)
                    results.append({
                        "ID": q.get('id', i+1),
                        "Category": category,
                        "Question": query,
                        "Retrieved Chunks": 0,
                        "Concept Coverage": "0%",
                        "Latency (s)": 0.0,
                        "Top Source": "Failed",
                        "Answer Preview": f"Error: {ex}"
                    })

                progress.progress((i + 1) / total_attempted)
                
            status_text.empty()
            progress.empty()
            
            # Aggregate metrics
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            retrieval_pct = round((retrieval_successes / total_attempted) * 100, 1) if total_attempted else 0.0
            concept_pct = round((concept_matches / total_attempted) * 100, 1) if total_attempted else 0.0

            st.success(f"Evaluation completed: {completed}/{total_attempted} evaluated successfully.")
            
            # Compute element-level coverage average
            per_q_coverage = []
            for r in results:
                cov_str = r.get("Concept Coverage", "0%")
                try:
                    per_q_coverage.append(float(cov_str.replace("%", "")) / 100.0)
                except ValueError:
                    per_q_coverage.append(0.0)
            avg_element_coverage_pct = round((sum(per_q_coverage) / len(per_q_coverage)) * 100, 1) if per_q_coverage else 0.0
            threshold_pct_questions = concept_pct  # already computed: % questions >= 50% coverage

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Attempted", str(total_attempted))
            col2.metric("Completed", str(completed))
            col3.metric("Retrieval (non-empty)", f"{retrieval_pct}%",
                        help="% questions where retriever returned ≥1 chunk. Non-empty retrieval ≠ relevant or accurate.")
            col4.metric("Avg Element Coverage", f"{avg_element_coverage_pct}%",
                        help="Average keyword match rate against expected_elements. Keyword matching ≠ semantic correctness.")
            col5.metric("Avg Latency", f"{avg_latency}s")
            col6.metric("Failed / Unsupported", str(failures))

            st.caption(
                "ℹ️ **Metric Definitions** — "
                "'Retrieval (non-empty)': retriever returned ≥1 chunk; does not confirm relevance or accuracy. "
                "'Avg Element Coverage': keyword match rate against synthetic expected_elements; "
                "this is not validated semantic correctness. "
                "Results are grounded in synthetic knowledge-base documents only."
            )

            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)
            
            output_dir = Path('c:/TARA/Evaluation_Results')
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / 'ui_eval_out.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            from backend.database.connection import log_audit_event
            log_audit_event(
                action="benchmark_evaluation",
                user="security_engineer",
                details=f"Evaluated {total_attempted} questions. Retrieval: {retrieval_pct}%, Coverage: {concept_pct}%, Failures: {failures}"
            )
                
        except Exception as e:
            st.error(f"Error during evaluation: {e}")

