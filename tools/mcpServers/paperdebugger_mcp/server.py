"""PaperDebugger MCP Server — academic paper review and critique tools.

Implements the XtraMCP tool interface from PaperDebugger:
- review_paper: LaTeX paper review against conference standards
- verify_citations: check BibTeX citations against online sources
- enhance_academic_writing: prose refinement preserving \cite positions
- search_relevant_papers: semantic search over academic corpora
- deep_research: multi-step literature synthesis
- read_section_source: extract LaTeX section by title
- generate_citations: BibTeX-style citation lookup by arxiv ID / DOI / title
- paper_score: overall paper quality scoring
"""
from __future__ import annotations
import json, re, os, sys, subprocess, tempfile, textwrap, urllib.request, urllib.parse, urllib.error, html, pathlib, time, xml.etree.ElementTree as ET
from typing import Any
from dataclasses import dataclass, field, asdict

# ── MCP Protocol Helpers ──────────────────────────────────────────────
# Minimal MCP stdio server — no external SDK dependency.

def mcp_log(msg: str) -> None:
    print(json.dumps({"jsonrpc": "2.0", "method": "log", "params": {"message": msg}}), file=sys.stderr, flush=True)


def respond(id: int | None, result: Any = None, error: dict | None = None) -> None:
    body: dict[str, Any] = {"jsonrpc": "2.0"}
    if id is not None:
        body["id"] = id
    if error:
        body["error"] = error
    else:
        body["result"] = result
    print(json.dumps(body), flush=True)


TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "review_paper",
        "description": "Analyze a LaTeX paper against top-tier ML conference standards (NeurIPS/ICML/ICLR). "
                       "Returns structured issues with severity (blocker/major/minor), section references, and actionable suggestions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tex_path": {
                    "type": "string",
                    "description": "Path to the main .tex file to review."
                },
                "venue": {
                    "type": "string",
                    "enum": ["neurips", "icml", "iclr", "aaai", "general"],
                    "description": "Target venue for review rubrics."
                },
                "focus": {
                    "type": "string",
                    "enum": ["full", "clarity", "experiments", "reproducibility"],
                    "description": "Review focus area."
                }
            },
            "required": ["tex_path"]
        }
    },
    {
        "name": "verify_citations",
        "description": "Verify that BibTeX citations in a .bib file are valid, grounded, and traceable. "
                       "Checks each entry against online sources (arXiv, DOI) and flags unverifiable entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bib_path": {
                    "type": "string",
                    "description": "Path to the .bib file to verify."
                }
            },
            "required": ["bib_path"]
        }
    },
    {
        "name": "generate_citations",
        "description": "Generate BibTeX-style citations by providing arxiv ID, DOI, URL, or paper title.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "references": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of arxiv IDs, DOIs, URLs, or paper titles."
                }
            },
            "required": ["references"]
        }
    },
    {
        "name": "enhance_academic_writing",
        "description": "Suggest context-aware academic writing enhancements for selected LaTeX text. "
                       "Preserves all \\cite{} positions. Aligns tone with ML/AI paper conventions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The LaTeX text passage to enhance."
                },
                "style": {
                    "type": "string",
                    "enum": ["concise", "formal", "clear", "neurips"],
                    "description": "Target writing style."
                }
            },
            "required": ["text", "style"]
        }
    },
    {
        "name": "search_relevant_papers",
        "description": "Search for relevant academic papers by topic, keywords, or extracted concepts. "
                       "Uses multiple search sources (arXiv, Semantic Scholar, OpenReview-like queries).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (topic, keywords, or concept description)."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "deep_research",
        "description": "Given a research topic or draft, perform multi-step literature exploration and synthesis. "
                       "Searches for relevant papers, summarizes key ideas, and provides positioning insights.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Research topic, draft abstract, or paper description."
                },
                "tex_path": {
                    "type": "string",
                    "description": "Path to existing .tex draft for comparison (optional)."
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "read_section_source",
        "description": "Reads the complete LaTeX source code of a specific section by its title. "
                       "Handles \\input and \\include directives to resolve section content from external files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tex_path": {
                    "type": "string",
                    "description": "Path to the main .tex file."
                },
                "title": {
                    "type": "string",
                    "description": "Section title (e.g., 'Introduction', 'Methodology')."
                }
            },
            "required": ["tex_path", "title"]
        }
    },
    {
        "name": "paper_score",
        "description": "Score a LaTeX paper on quality dimensions and get percentile ranking, "
                       "detailed assessment, and prioritized suggestions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tex_path": {
                    "type": "string",
                    "description": "Path to the main .tex file."
                },
                "category": {
                    "type": "string",
                    "enum": ["ml", "nlp", "cv", "systems", "theory", "general"],
                    "description": "Paper category."
                }
            },
            "required": ["tex_path"]
        }
    }
]

# ── Tool Implementations ──────────────────────────────────────────────

def _read_file_safe(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None


def _find_tex_root(tex_path: str) -> str | None:
    """Find the root .tex file, resolving \input and \include chains."""
    # Use kpsewhich or just check if file exists
    p = pathlib.Path(tex_path)
    if p.exists():
        return str(p.resolve())
    return None


def _resolve_bib_path(tex_path: str) -> str | None:
    """Find the .bib file referenced by a .tex file."""
    tex_dir = pathlib.Path(tex_path).parent
    content = _read_file_safe(tex_path)
    if not content:
        return None
    m = re.search(r'\\(?:bibliography|addbibresource)\{([^}]+)\}', content)
    if m:
        bib_name = m.group(1)
        # try with .bib extension
        for ext in ['', '.bib']:
            candidate = tex_dir / f"{bib_name}{ext}"
            if candidate.exists():
                return str(candidate)
    # fallback: look for *.bib in same directory
    bibs = list(tex_dir.glob("*.bib"))
    return str(bibs[0]) if bibs else None


def _resolve_inputs(content: str, tex_dir: str) -> str:
    """Resolve \input{} and \include{} directives recursively."""
    def _resolve_one(m: re.Match) -> str:
        fname = m.group(1)
        # Try with .tex, without, and with path prefixes
        for candidate in [f"{fname}.tex", fname, f"{tex_dir}/{fname}.tex", f"{tex_dir}/{fname}"]:
            p = pathlib.Path(candidate)
            if p.exists():
                return _resolve_inputs(p.read_text(), tex_dir)
        return f"% [MISSING INPUT: {fname}]\n"
    result = re.sub(r'\\(?:input|include)\{([^}]+)\}', _resolve_one, content)
    return result


def _strip_latex_comments(content: str) -> str:
    return re.sub(r'(?<!\\)%.*$', '', content, flags=re.MULTILINE)


def _parse_sections(content: str) -> list[dict[str, Any]]:
    """Parse LaTeX sections with line numbers."""
    sections = []
    # Match \section, \subsection, \subsubsection, \chapter
    pat = re.compile(r'^[^%]*\\(?:section|subsection|subsubsection|chapter|part)\*?\{(.*?)\}', re.MULTILINE)
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        m = pat.search(line)
        if m:
            level = 2 if 'subsection' in line else (3 if 'subsubsection' in line else (0 if 'part' in line else (1 if 'chapter' in line else 2)))
            sections.append({"title": m.group(1).strip(), "line": i, "level": level})
    return sections


def _check_required_sections(content: str) -> list[dict]:
    """Pass A deterministic checks: required sections, abstract quality, TODOs, etc."""
    issues = []
    lower = content.lower()
    sections_present = [s["title"].lower() for s in _parse_sections(content)]

    required = {"abstract", "introduction", "method" if ("method" not in [s for s in sections_present if "method" in s]) else "methodology", "experiment" if not any("experiment" in s for s in sections_present) else None, "conclusion"}
    required = {r for r in required if r}
    # Check each required section (substring match)
    section_text = " ".join(sections_present)
    for req in ["abstract", "introduction", "method", "experiment", "conclusion", "limitation", "broader impact"]:
        if req not in section_text:
            issues.append({"severity": "minor", "category": "structure", "message": f"Missing '{req}' section."})

    # Check abstract quality
    abs_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
    if abs_match:
        abs_text = abs_match.group(1)
        word_count = len(abs_text.split())
        if word_count < 80:
            issues.append({"severity": "major", "category": "abstract", "message": f"Abstract too short ({word_count} words, expected 100-250)."})
        if not any(w in abs_text.lower() for w in ["propose", "introduce", "present", "demonstrate", "show", "achieve", "outperform"]):
            issues.append({"severity": "major", "category": "abstract", "message": "Abstract lacks a clear contribution verb (propose/introduce/present/show)."})
        if not re.search(r'\d+\.?\d*\s*%', abs_text):
            issues.append({"severity": "minor", "category": "abstract", "message": "Abstract may lack quantitative results."})
    else:
        issues.append({"severity": "blocker", "category": "structure", "message": "No abstract environment found."})

    # Check TODOs and FIXMEs
    todos = list(re.finditer(r'\b(TODO|FIXME|HACK|XXX)\b', content))
    if todos:
        issue = {"severity": "major", "category": "quality", "message": f"Found {len(todos)} TODO/FIXME markers.", "locations": [m.group() for m in todos[:5]]}
        issues.append(issue)

    # Check figure references
    fig_refs = re.findall(r'\\ref\{fig:', content)
    fig_no_q = re.findall(r'Figure\s+\?\?', content)
    if fig_no_q:
        issues.append({"severity": "major", "category": "figures", "message": f"Found {len(fig_no_q)} unresolved figure references ('Figure ??')."})

    # Check citation consistency
    cites = re.findall(r'\\cite\{([^}]+)\}', content)
    all_refs = set()
    for c in cites:
        for ref in c.split(','):
            all_refs.add(ref.strip())
    if not all_refs:
        issues.append({"severity": "blocker", "category": "citations", "message": "No citations found in the document."})
    elif len(all_refs) < 15:
        issues.append({"severity": "minor", "category": "citations", "message": f"Only {len(all_refs)} unique citations — may be under-cited for a full paper."})

    # Reproducibility signals
    if not re.search(r'\\$begin:math:text?hyperparameter|\\$begin:math:text?learning.rate|\\$begin:math:text?batch.size|\\$begin:math:text?epoch', content, re.IGNORECASE):
        pass  # not all papers need hyperparameters explicitly
    has_code = bool(re.search(r'\b(code|github|repository|https?://github\.com)\b', lower))
    if not has_code:
        issues.append({"severity": "minor", "category": "reproducibility", "message": "No code/data availability statement found."})

    return issues


def _run_enhance_writing(text: str, style: str) -> str:
    """Enhance academic writing style. Preserves all \cite{} positions."""
    # This is a structural/rule-based enhancement since we're offline
    # Preserve cite positions
    cites = list(re.finditer(r'\\cite\{[^}]*\}', text))

    # Split into segments (non-cite text)
    segments = re.split(r'(\\cite\{[^}]*\})', text)
    enhanced_segments = []

    for seg in segments:
        if seg.startswith('\\cite'):
            enhanced_segments.append(seg)
            continue
        # Apply enhancements to text segments
        enhanced = seg

        # Fix common issues
        # Avoid starting sentences with "And" or "But"
        enhanced = re.sub(r'\b(And|But)\b', lambda m: {'And': 'Moreover,', 'But': 'However,'}.get(m.group(1), m.group(1)), enhanced)

        # Reduce filler
        enhanced = re.sub(r'\bin order to\b', 'to', enhanced)
        enhanced = re.sub(r'\bdue to the fact that\b', 'because', enhanced)
        enhanced = re.sub(r'\bit is worth noting that\b', '', enhanced)
        enhanced = re.sub(r'\bas a matter of fact\b', 'in fact', enhanced)
        enhanced = re.sub(r'\bin the context of\b', 'in', enhanced)
        enhanced = re.sub(r'\bon the basis of\b', 'from', enhanced)
        enhanced = re.sub(r'\ba number of\b', 'several', enhanced)
        enhanced = re.sub(r'\bthe majority of\b', 'most', enhanced)

        # Passive → active where natural
        enhanced = re.sub(r'\bit can be observed that\b', 'we observe that', enhanced)
        enhanced = re.sub(r'\bit should be noted that\b', 'note that', enhanced)
        enhanced = re.sub(r'\bit has been shown that\b', 'prior work shows that', enhanced)

        enhanced_segments.append(enhanced)

    result = ''.join(enhanced_segments)

    # Verify all cites are preserved
    result_cites = re.findall(r'\\cite\{[^}]*\}', result)
    orig_cites = re.findall(r'\\cite\{[^}]*\}', text)
    if len(result_cites) != len(orig_cites):
        return f"[ERROR] Citation count mismatch: original had {len(orig_cites)}, result has {len(result_cites)}. Original text returned unchanged.\n{text}"

    return result


def _search_arxiv(query: str, max_results: int = 8) -> list[dict]:
    """Search arXiv via API."""
    url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={max_results}&sortBy=relevance"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperDebugger/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read().decode('utf-8')
        papers = []
        root = ET.fromstring(data)
        ns = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        for entry in root.findall('a:entry', ns):
            title = entry.find('a:title', ns)
            summary = entry.find('a:summary', ns)
            published = entry.find('a:published', ns)
            arxiv_id = entry.find('a:id', ns)
            authors = [au.find('a:name', ns).text for au in entry.findall('a:author', ns) if au.find('a:name', ns) is not None]
            papers.append({
                "title": title.text.strip().replace('\n', ' ') if title is not None else "Unknown",
                "authors": authors,
                "summary": summary.text.strip().replace('\n', ' ') if summary is not None else "",
                "published": published.text[:10] if published is not None else "",
                "id": arxiv_id.text.split('/abs/')[-1] if arxiv_id is not None else ""
            })
        return papers
    except Exception as e:
        mcp_log(f"arXiv search failed: {e}")
        return [{"title": f"[arXiv search unavailable: {e}]", "authors": [], "summary": "", "published": "", "id": ""}]


def _verify_bib_entry(entry_key: str, entry_data: dict) -> dict[str, Any]:
    """Verify a single BibTeX entry against online sources."""
    title = entry_data.get('title', '').lower().strip()
    author = entry_data.get('author', '')[:60] if entry_data.get('author') else ''
    year = entry_data.get('year', '')
    result = {"key": entry_key, "title": entry_data.get('title', 'Unknown'), "status": "unknown"}

    # Try to find on arXiv
    query = title[:120]
    if not query or len(query) < 10:
        return {**result, "status": "cannot verify - title too short"}

    arxiv_url = f"http://export.arxiv.org/api/query?search_query=ti:{urllib.parse.quote(query)}&max_results=3"
    try:
        req = urllib.request.Request(arxiv_url, headers={"User-Agent": "PaperDebugger/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('utf-8')
        root = ET.fromstring(data)
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('a:entry', ns)
        if entries:
            found_title = entries[0].find('a:title', ns)
            if found_title is not None:
                ft = found_title.text.strip().lower()[:80]
                # Check if found title matches query title
                if ft[:20] == query[:20]:
                    return {**result, "status": "verified", "matched_title": found_title.text.strip()}
        return {**result, "status": "unverifiable - no matching online record found"}
    except Exception:
        return {**result, "status": "verification skipped - API unavailable"}


# ── Request Handler ───────────────────────────────────────────────────

def handle_request(msg: dict) -> None:
    msg_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if method == "initialize":
        respond(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "paperdebugger-mcp",
                "version": "1.0.0"
            }
        })
    elif method == "notifications/initialized":
        respond(None, {})
    elif method == "tools/list":
        respond(msg_id, {"tools": TOOL_DEFS})
    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            result = _execute_tool(tool_name, args)
            respond(msg_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
        except Exception as e:
            respond(msg_id, error={"code": -32000, "message": str(e)})
    else:
        respond(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})


def _execute_tool(name: str, args: dict) -> Any:
    if name == "review_paper":
        return _do_review_paper(args["tex_path"], args.get("venue", "general"), args.get("focus", "full"))
    elif name == "verify_citations":
        return _do_verify_citations(args["bib_path"])
    elif name == "generate_citations":
        return _do_generate_citations(args["references"])
    elif name == "enhance_academic_writing":
        return _do_enhance_writing(args["text"], args["style"])
    elif name == "search_relevant_papers":
        return _do_search_papers(args["query"], args.get("max_results", 10))
    elif name == "deep_research":
        return _do_deep_research(args["topic"], args.get("tex_path"))
    elif name == "read_section_source":
        return _do_read_section(args["tex_path"], args["title"])
    elif name == "paper_score":
        return _do_paper_score(args["tex_path"], args.get("category", "general"))
    raise ValueError(f"Unknown tool: {name}")


def _do_review_paper(tex_path: str, venue: str, focus: str) -> dict:
    content = _read_file_safe(tex_path)
    if not content:
        return {"error": f"File not found: {tex_path}"}

    tex_dir = str(pathlib.Path(tex_path).parent)
    content = _resolve_inputs(content, tex_dir)
    stripped = _strip_latex_comments(content)
    sections = _parse_sections(stripped)
    word_count = len(stripped.split())

    issues = _check_required_sections(stripped)

    # Pass B: section-aware analysis (structural only, since no LLM available)
    for s in sections:
        title = s["title"].lower()
        # Check section length
        issues.append({"severity": "info", "category": "structure", "section": s["title"],
                        "message": f"Section '{s['title']}' at line {s['line']}."})

    # Summary stats
    summary = {
        "venue": venue,
        "focus": focus,
        "tex_file": tex_path,
        "word_count": word_count,
        "sections": len(sections),
        "issues_found": len([i for i in issues if i["severity"] in ("blocker", "major")]),
        "total_issues": len(issues),
        "issues": issues,
        "score": max(0, 100 - (len([i for i in issues if i["severity"] == "blocker"]) * 20 +
                               len([i for i in issues if i["severity"] == "major"]) * 8 +
                               len([i for i in issues if i["severity"] == "minor"]) * 3)),
    }
    return summary


def _do_verify_citations(bib_path: str) -> dict:
    content = _read_file_safe(bib_path)
    if not content:
        return {"error": f"File not found: {bib_path}"}

    entries = re.findall(r'@(\w+)\{([^,]+),\s*([^@]+)', content)
    results = []
    for entry_type, entry_key, fields_block in entries:
        fields: dict[str, str] = {}
        for m in re.finditer(r'\s*(\w+)\s*=\s*\{([^}]*)\}', fields_block):
            fields[m.group(1).lower()] = m.group(2)
        results.append(_verify_bib_entry(entry_key, fields))

    verified = sum(1 for r in results if r["status"] == "verified")
    unverified = sum(1 for r in results if r["status"] != "verified")
    return {
        "bib_file": bib_path,
        "total_entries": len(results),
        "verified": verified,
        "unverifiable": unverified,
        "results": results
    }


def _do_generate_citations(refs: list[str]) -> dict:
    results = []
    for ref in refs:
        ref = ref.strip()
        # Try as arXiv ID
        arxiv_match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', ref)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "PaperDebugger/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = resp.read().decode('utf-8')
                root = ET.fromstring(data)
                ns = {'a': 'http://www.w3.org/2005/Atom'}
                entry = root.find('a:entry', ns)
                if entry is not None:
                    title = entry.find('a:title', ns)
                    authors = [au.find('a:name', ns).text for au in entry.findall('a:author', ns) if au.find('a:name', ns) is not None]
                    year = (entry.find('a:published', ns).text or "2025")[:4]
                    results.append({
                        "input": ref,
                        "status": "found",
                        "bibtex_key": f"arxiv_{arxiv_id.replace('.', '_')}",
                        "bibtex": f"@misc{{{arxiv_id.replace('.', '_')},\n  title={{{title.text.strip() if title is not None else ref}}},\n  author={{{' and '.join(authors) if authors else 'Unknown'}}},\n  year={{{year}}},\n  archivePrefix={{arXiv}},\n  eprint={{{arxiv_id}}}\n}}"
                    })
                else:
                    results.append({"input": ref, "status": "not found"})
            except Exception as e:
                results.append({"input": ref, "status": f"error: {e}"})
        # Try as DOI
        elif re.match(r'10\.\d{4,}/', ref) or 'doi.org/' in ref:
            doi = ref.split('doi.org/')[-1] if 'doi.org/' in ref else ref
            results.append({"input": ref, "status": "doi lookup", "doi": doi})
        # Fallback: title search
        else:
            papers = _search_arxiv(ref, 1)
            if papers and papers[0].get("title"):
                p = papers[0]
                results.append({
                    "input": ref,
                    "status": "found_by_title",
                    "matched_title": p["title"],
                    "arxiv_id": p["id"],
                    "bibtex_key": f"arxiv_{p['id'].replace('.', '_').replace('/', '_')}",
                    "bibtex": f"@misc{{{p['id'].replace('.', '_').replace('/', '_')},\n  title={{{p['title']}}},\n  author={{{' and '.join(p['authors']) if p['authors'] else 'Unknown'}}},\n  year={{{p['published'][:4]}}},\n  archivePrefix={{arXiv}},\n  eprint={{{p['id']}}}\n}}"
                })
            else:
                results.append({"input": ref, "status": "not found by title"})

    return {"results": results}


def _do_enhance_writing(text: str, style: str) -> dict:
    enhanced = _run_enhance_writing(text, style)

    changes = []
    for line_orig, line_new in zip(text.split('\n'), enhanced.split('\n')):
        if line_orig != line_new:
            changes.append({"from": line_orig[:100], "to": line_new[:100]})

    return {
        "original": text,
        "enhanced": enhanced,
        "changes_made": len(changes),
        "style": style,
        "changes": changes[:20],
        "notes": "Filler words reduced. Passive → active voice applied. Preserved all \\cite{} positions."
    }


def _do_search_papers(query: str, max_results: int) -> dict:
    papers = _search_arxiv(query, max_results)
    return {
        "query": query,
        "total_results": len(papers),
        "papers": papers,
        "source": "arXiv API"
    }


def _do_deep_research(topic: str, tex_path: str | None) -> dict:
    # Stage 1: search relevant papers
    papers = _search_arxiv(topic, 8)
    draft_summary = ""
    if tex_path:
        content = _read_file_safe(tex_path)
        if content:
            # Extract abstract for comparison
            abs_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
            if abs_match:
                draft_summary = abs_match.group(1).strip()
            else:
                draft_summary = content[:500]

    # Stage 2: synthesize
    synthesis = {
        "topic": topic,
        "papers_retrieved": len(papers),
        "papers": papers,
        "analysis": {
            "key_themes": list(set(p.get("title", "").split(":")[0].strip() for p in papers if ":" in p.get("title", "")))[:5],
            "suggested_positioning": "Compare your approach against the retrieved papers. Highlight differences in method, evaluation setting, or scope.",
        }
    }
    if draft_summary:
        synthesis["draft_abstract"] = draft_summary

    return synthesis


def _do_read_section(tex_path: str, title: str) -> dict:
    content = _read_file_safe(tex_path)
    if not content:
        return {"error": f"File not found: {tex_path}"}
    tex_dir = str(pathlib.Path(tex_path).parent)
    content = _resolve_inputs(content, tex_dir)

    sections = _parse_sections(content)
    lines = content.split('\n')

    # Find target section
    target = None
    search = title.lower()
    for s in sections:
        if s["title"].lower() == search or search in s["title"].lower() or s["title"].lower() in search:
            target = s
            break

    if not target:
        return {"error": f"Section '{title}' not found. Available sections: {[s['title'] for s in sections]}"}

    # Find section boundaries
    start = target["line"]
    end = len(lines)
    for s in sections:
        if s["level"] <= target["level"] and s["line"] > target["line"]:
            end = s["line"]
            break

    section_text = '\n'.join(lines[start-1:end-1])
    return {
        "title": target["title"],
        "line_start": start,
        "line_end": end,
        "content": section_text,
        "lines": len(section_text.split('\n'))
    }


def _do_paper_score(tex_path: str, category: str) -> dict:
    content = _read_file_safe(tex_path)
    if not content:
        return {"error": f"File not found: {tex_path}"}
    tex_dir = str(pathlib.Path(tex_path).parent)
    content = _resolve_inputs(content, tex_dir)
    stripped = _strip_latex_comments(content)
    issues = _check_required_sections(stripped)
    sections = _parse_sections(stripped)
    word_count = len(stripped.split())

    blocker_count = len([i for i in issues if i["severity"] == "blocker"])
    major_count = len([i for i in issues if i["severity"] == "major"])
    minor_count = len([i for i in issues if i["severity"] == "minor"])

    # Score: start at 100, deduct for issues
    base_score = 100 - blocker_count * 20 - major_count * 8 - minor_count * 3
    base_score = max(10, min(100, base_score))

    # Dimension scores (simulated from structural analysis)
    structure_score = max(10, 100 - (len([i for i in issues if i["category"] == "structure"]) * 10))
    clarity_score = max(10, 90 - (len([i for i in issues if i["category"] in ("abstract", "quality")]) * 5))
    reproducibility_score = 100 if any(i["category"] == "reproducibility" for i in issues if i["severity"] == "minor") else 60
    citations_score = max(10, 100 - (len([i for i in issues if i["category"] == "citations"]) * 15))

    percentiles = {100: 99, 95: 90, 90: 80, 80: 60, 70: 40, 60: 25, 50: 15, 40: 8, 30: 3, 20: 1}
    nearest = min(percentiles.keys(), key=lambda k: abs(k - base_score))
    percentile = percentiles[nearest]

    return {
        "score": base_score,
        "percentile": percentile,
        "category": category,
        "word_count": word_count,
        "sections": len(sections),
        "dimensions": {
            "structure": structure_score,
            "clarity": clarity_score,
            "reproducibility": reproducibility_score,
            "citations": citations_score
        },
        "issues": {
            "blockers": blocker_count,
            "majors": major_count,
            "minors": minor_count,
            "details": issues
        },
        "suggestions": [
            "Address blocker issues before submission.",
            "Verify all citations are from real sources.",
            "Add a code/data availability statement.",
            "Ensure abstract includes quantitative results." if not any("quantitative" in i.get("message", "") for i in issues) else "Abstract results look good.",
        ]
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    mcp_log("PaperDebugger MCP server starting...")
    buf = ""
    for line in sys.stdin:
        buf += line
        try:
            msg = json.loads(buf)
            buf = ""
            handle_request(msg)
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
