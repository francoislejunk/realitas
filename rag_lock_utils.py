from __future__ import annotations

from typing import Any, Iterable, List, Optional

import os
import re


def get_category_context_for_llm(
    rag_system: Any,
    *,
    query: str,
    category: Any,
    max_tokens: int = 400,
    include_related: bool = True,
) -> str:
    if not rag_system or not category:
        return ""

    try:
        return rag_system.get_context_for_llm(
            query=query,
            max_tokens=max_tokens,
            category_filter=category,
            include_related=include_related,
        ) or ""
    except Exception:
        return ""


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    v = str(raw).strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return default


def _cat_value(cat: Any) -> str:
    try:
        return str(getattr(cat, "value"))
    except Exception:
        return str(cat)


def _budget_for_category(cat: Any, fallback: int) -> int:
    # REALITAS_RAG_MAXTOKENS_DEFAULT overrides the default if set.
    try:
        raw_default = os.getenv("REALITAS_RAG_MAXTOKENS_DEFAULT")
        if raw_default is not None and str(raw_default).strip():
            fallback = int(str(raw_default).strip())
    except Exception:
        pass

    key = _cat_value(cat).upper()
    key = "".join([ch if (ch.isalnum() or ch == "_") else "_" for ch in key])
    env_name = f"REALITAS_RAG_MAXTOKENS_{key}"
    try:
        raw = os.getenv(env_name)
        if raw is None or not str(raw).strip():
            return int(fallback)
        return int(str(raw).strip())
    except Exception:
        return int(fallback)


def get_multi_category_context_for_llm(
    rag_system: Any,
    *,
    query: str,
    categories: Iterable[Any],
    max_tokens_per_category: int = 250,
    include_related: bool = True,
    header: Optional[str] = None,
) -> str:
    if not rag_system:
        return ""

    trace = _env_bool("REALITAS_RAG_TRACE", False)
    disable_style = _env_bool("REALITAS_DISABLE_STYLE_RAG", False)
    parts: List[str] = []
    for cat in list(categories or []):
        if not cat:
            continue

        if disable_style:
            cv = _cat_value(cat)
            if cv in ("culture", "narration_style_tone"):
                continue

        budget = _budget_for_category(cat, max_tokens_per_category)
        ctx = get_category_context_for_llm(
            rag_system,
            query=query,
            category=cat,
            max_tokens=budget,
            include_related=include_related,
        )
        if ctx and ctx.strip():
            if trace:
                cv = _cat_value(cat)
                if cv in ("culture", "narration_style_tone"):
                    snippet = ctx.strip().replace("\n", " ")
                    snippet = snippet[:300] + ("..." if len(snippet) > 300 else "")
                    approx_tokens = max(1, int(len(ctx) / 4))
                    print(f"[RAG_TRACE] cat={cv} budget={budget} approx_tokens={approx_tokens} query={query[:120]!r} snippet={snippet!r}")
            parts.append(ctx.strip())

    if not parts:
        return ""

    body = "\n\n".join(parts)
    if header:
        return f"\n**{header}:**\n{body}\n"

    return body


def extract_rag_list_items(
    text: Any,
    *,
    bullet_prefixes: Iterable[str] = ("-", "•", "*"),
    allow_numbered: bool = True,
) -> List[str]:
    if not text:
        return []

    prefixes = tuple([p for p in (bullet_prefixes or []) if p])
    out: List[str] = []

    for raw in str(text).splitlines():
        s = (raw or "").strip()
        if not s:
            continue

        had_prefix = False
        for p in prefixes:
            if s.startswith(p):
                s = s[len(p):].strip()
                had_prefix = True
                break

        if not had_prefix and allow_numbered:
            m = re.match(r"^(?:\(?\d+\)?[\.)]|[a-zA-Z][\.)])\s+", s)
            if m:
                s = s[m.end():].strip()
                had_prefix = True

        if not had_prefix:
            continue
        if not s:
            continue
        if s not in out:
            out.append(s)

    return out


def extract_rag_section_list_items(
    text: Any,
    *,
    header_prefix: str,
    bullet_prefixes: Iterable[str] = ("-", "•", "*"),
    allow_numbered: bool = True,
) -> List[str]:
    if not text or not header_prefix:
        return []

    prefixes = tuple([p for p in (bullet_prefixes or []) if p])
    in_section = False
    out: List[str] = []

    for raw_ln in str(text).splitlines():
        ln = (raw_ln or "").strip()

        if not ln:
            if in_section:
                break
            continue

        if not in_section and ln.lower().startswith((header_prefix or "").strip().lower()):
            in_section = True
            continue

        if not in_section:
            continue

        had_prefix = False
        for p in prefixes:
            if ln.startswith(p):
                ln = ln[len(p):].strip()
                had_prefix = True
                break

        if not had_prefix and allow_numbered:
            m = re.match(r"^(?:\(?\d+\)?[\.)]|[a-zA-Z][\.)])\s+", ln)
            if m:
                ln = ln[m.end():].strip()
                had_prefix = True

        if not had_prefix:
            if ':' in ln:
                break
            continue

        if ln and ln not in out:
            out.append(ln)

    return out
