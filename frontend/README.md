# Colombo Stock Exchange (CSE) Research Platform — Frontend

A university-grade econometric research platform visualizing the relationship between Sri Lankan political events, news, and Colombo Stock Exchange (CSE) All Share Price Index (ASPI) dynamics.

Built strictly under **Permanent Rules FR1 through FR10** defined in [RULES.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/RULES.md).

---

## 1. Permanent Rules Summary

| Rule | Title | Mandate |
|---|---|---|
| **FR1** | **No Hardcoded Domain Data** | Only interface chrome (labels, headers, microcopy) is static. All metrics, sample sizes ($n$), dates, model names, and statuses originate from the backend API. |
| **FR2** | **Only URLs in Config** | Only `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` in `.env`. Validated at runtime via `src/lib/env.ts`. Zero secrets or keys. |
| **FR3** | **No Mock Data in `src/`** | Test fixtures live only in `tests/` and are never imported into `src/`. If backend is unavailable, the UI renders `<BackendUnavailable />`. |
| **FR4** | **Contract First** | OpenAPI schemas define types. Every response is validated at runtime with Zod. Mismatches render `<ContractError />`. |
| **FR5** | **Honest UI** | Mandatory display of sample sizes ($n$), uncertainty intervals, evidence strength, as-of dates, stale flags, and API glossary definitions. |
| **FR6** | **Accessibility** | WCAG 2.1 AA compliance: full keyboard navigation, visible focus rings, ARIA labels with alternative data tables on all charts, and reduced-motion support. |
| **FR7** | **Performance** | Route-level code splitting, virtualized tables, memoized chart configurations, sensible React Query caching, and request cancellation. |
| **FR8** | **Code Quality** | Strict TypeScript, feature-based modularity, zero components exceeding 300 lines, comprehensive unit and smoke tests. |
| **FR9** | **Gaps Reported, Not Faked** | Missing backend capabilities are formally recorded in `docs/backend-gaps.md` and rendered as `<EmptyState message="Data not available from backend" />`. |
| **FR10** | **Stage Discipline** | Strict stage-by-stage progression. Each stage concludes with a verified `STAGE_REPORT.md` before stopping. |

---

## 2. Architecture & Directory Structure

```
frontend/
├── RULES.md                      # Permanent rules FR1-FR10 (verbatim)
├── README.md                     # Architecture and setup guide
├── .env.example                  # Validated URLs configuration
├── package.json                  # Scripts, dependencies, and tooling
├── vite.config.ts                # Vite bundler configuration & code splitting
├── tsconfig.json                 # Strict TypeScript configuration
├── tailwind.config.ts            # Research design system tokens
├── eslint.config.js              # ESLint 9 configuration
├── vitest.config.ts              # Unit test runner
├── playwright.config.ts          # E2E test runner
├── public/                       # Favicon and local assets
├── docs/                         # Design system, API contract, backend gaps
├── scripts/
│   ├── check-hardcoding.ts       # CI guard: fails build on hardcoded domain data
│   └── gen-api.ts                # OpenAPI type & schema synchronization
├── src/
│   ├── app/                      # App router, providers, layout, error boundary
│   ├── api/                      # Client, Zod schemas, endpoints, generated types
│   ├── components/
│   │   ├── ui/                   # Reusable atomic design primitives
│   │   ├── charts/               # Accessible chart wrappers with table fallback
│   │   ├── layout/               # Header, Sidebar, Navigation, Shell
│   │   └── feedback/             # ContractError, BackendUnavailable, EmptyState
│   ├── features/                 # 11 Modular research feature domains
│   │   ├── overview/             # High-level market & research executive summary
│   │   ├── data-explorer/        # ASPI time-series & technical indicator explorer
│   │   ├── events/               # Sri Lankan election & crisis catalog
│   │   ├── event-study/          # CAAR abnormal returns & placebo permutations
│   │   ├── methodology/          # Research protocol, leakage guards, walk-forward
│   │   ├── model-lab/            # Model leaderboard, ablations, prediction series
│   │   ├── news/                 # Live news feed polling & sentiment analytics
│   │   ├── scenario/             # Counterfactual event shock simulations
│   │   ├── research/             # Skeptical audit proofs & IEEE report assets
│   │   ├── favorites/            # Bookmarkable models, events, and views
│   │   └── feedback/             # Research study reviewer feedback portal
│   ├── hooks/                    # Reusable React hooks
│   ├── lib/                      # Validated env, query client, utilities
│   ├── stores/                   # Lightweight UI state
│   ├── styles/                   # Global CSS, font imports, Tailwind directives
│   ├── types/                    # Core application types
│   └── utils/                    # Formatting, date, and math utilities
└── tests/
    ├── unit/                     # Formatters, env validation, API adapter tests
    ├── integration/              # Contract error boundary tests
    └── e2e/                      # Playwright browser smoke tests
```

---

## 3. Development & Script Commands

```bash
# Install dependencies
npm install

# Start local development server (http://localhost:3000)
npm run dev

# Run hardcoding verification check (Rule FR1 & FR3)
npm run check:hardcoding

# Generate / synchronize OpenAPI types (Rule FR4)
npm run gen:api

# Run unit tests
npm test

# Run linter
npm run lint

# Production build
npm run build
```
