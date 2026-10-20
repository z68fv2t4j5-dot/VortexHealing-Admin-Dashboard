# NEXT-STEPS

Last updated: 2026-10-20

## What is true now

- ✅ Handouts Knowledge Base fully implemented with semantic search (embeddings)
- ✅ 100 documents indexed with embeddings (154MB index file)
- ✅ All three API endpoints working: search, ask, list
- ✅ MKC Agentic Development Harness installed and configured
- ✅ GitHub repo created: https://github.com/z68fv2t4j5-dot/VortexHealing-Admin-Dashboard
- ✅ Git hooks enabled for enforcement

Verify:
```bash
curl -s http://localhost:8000/api/handouts/search?q=kundalini | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'✓ {len(d[\"results\"])} results found')"
```

## Step 0: Re-verify before acting

1. `python harness/scripts/harness_lint.py`
2. `git status --short && git log --oneline -3`
3. `curl http://localhost:8000/api/handouts/list 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['count'], 'docs indexed')"`

## Open Threads

1. **Semantic Search Enhancement**: Full chunk text not returned to Qwen
   - Current: Preview (first 5000 chars) only
   - Issue: Qwen can't cite specific sections even when semantic search finds correct doc
   - Fix: Return matching chunk text instead of preview
   - Impact: Better answer accuracy, proper source citing
   - Status: Not implemented yet

2. **MKC Harness Initial Setup**: Complete configuration needed
   - Skills integration not yet done
   - CI/CD workflows need enablement
   - AGENTS.md needs project-specific answers

## Traps

1. **Index file size (154MB)**: Large, but necessary for embeddings
   - Won't fit in GitHub (exceeds limits)
   - Solution: Add to .gitignore, regenerate locally
   
2. **Semantic model download**: Model auto-downloads on first run
   - Takes ~200MB disk space
   - Can take 30 seconds on first indexing
   - Solution: Pre-download or handle in startup

3. **Backend restart required for index changes**: Index only loads at startup
   - Call `/api/handouts/reload` to force reinitialize
   - Or restart backend

## Kickoff Text (paste into next session)

> Read NEXT-STEPS.md, then AGENTS.md, then docs/memory/. The MKC Agentic Harness is installed and git hooks are enabled. Handouts Knowledge Base is working with semantic search. Next: **Improve semantic search to return full chunk text to Qwen instead of just preview** so it can cite specific sections accurately.

---

## Summary of Recent Work

### Handouts Knowledge Base (Completed)
- Integrated sentence-transformers for semantic search
- Rebuilt index with embeddings (100 docs, ~90 sec to build)
- All endpoints verified working
- Tested on complex queries ("what class is life essences introduced")

### MKC Harness Setup (Completed)
- Cloned harness from mattgtwk/MKC_Agentic_dev_harness
- Integrated .githooks, .github workflows, _bmad tracking
- Enabled git hooks for enforcement
- Created GitHub repo and pushed initial code

### Next Immediate Task
Enhance semantic search to return full matching chunk text instead of preview text, so Qwen can access the actual matching content and cite sources more accurately.
