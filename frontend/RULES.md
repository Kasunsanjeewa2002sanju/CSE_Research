# PERMANENT RULES

FR1 NO HARDCODED DOMAIN DATA. Static text is allowed only for interface chrome (navigation labels, page headings, button labels, form labels, short explanatory microcopy). Everything else must come from the backend API: numbers, dates, series, category and stage lists, model names, metric names and definitions, thresholds, disclaimers, refresh intervals, feed lists, status values and colour-coded statuses (mapped from API enums).
FR2 ONLY URLs IN CONFIG. The only configuration is URLs in .env (VITE_API_BASE_URL and optionally VITE_WS_BASE_URL). Read them only in src/lib/env.ts with validation. No API keys or secrets in the frontend, ever.
FR3 NO MOCK DATA IN src/. Test fixtures live only in tests/ and are never imported by src/. If the backend is unavailable the UI shows a proper error state; it does not fall back to fake values.
FR4 CONTRACT FIRST. Types come from the backend OpenAPI schema when available. Every API response is validated with Zod at the boundary. A mismatch renders a visible "contract error" component and logs details; never a silent fallback.
FR5 HONEST UI. Always show sample sizes (n), uncertainty intervals, evidence strength, data-as-of dates and stale flags when the API supplies them. Show "historical association, not causation" and the disclaimers that the API provides. Every metric has a definition tooltip from the API glossary.
FR6 ACCESSIBILITY. WCAG 2.1 AA: keyboard navigation, visible focus, ARIA labels on charts (with a data-table alternative), reduced-motion support, colour never the only cue.
FR7 PERFORMANCE. Route-level code splitting, virtualised long tables, memoised chart options, request cancellation, sensible caching.
FR8 CODE QUALITY. Strict TypeScript, feature-based modules, no component over 300 lines, unit tests for formatters and API adapters.
FR9 GAPS ARE REPORTED, NOT FAKED. When the backend lacks something the UI needs, write the exact request and response proposal to frontend/docs/backend-gaps.md and show an empty state saying the data is not available from the backend.
FR10 STAGE DISCIPLINE. Do only the current stage. End with STAGE_REPORT.md (done, files, screenshots list, problems, open decisions) and STOP.
