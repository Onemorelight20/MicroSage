# MicroSage Query Flow Diagram

## Complete Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant QueryForm as QueryForm<br/>(React Component)
    participant API as API Service<br/>(api.ts)
    participant Backend as FastAPI Backend<br/>(main.py)
    participant QueryService as Query Service<br/>(query_service.py)
    participant WebSocket as WebSocket Manager<br/>(websocket.py)
    participant NanoSage as NanoSage Core<br/>(SearchSession)
    participant ProgressTracker as Progress Tracker<br/>(React Component)
    participant ResultsDisplay as Results Display<br/>(React Component)

    %% Submission Phase
    Note over User,QueryForm: 1. SUBMISSION PHASE
    User->>QueryForm: Enter query text and parameters
    QueryForm->>QueryForm: Validate input (1-500 chars)
    QueryForm->>API: submitQuery(queryText, parameters)
    API->>Backend: POST /api/query/submit
    Backend->>QueryService: submit_query(params)
    QueryService->>QueryService: Generate UUID
    QueryService->>QueryService: Validate with Pydantic
    QueryService-->>Backend: Return query_id
    Backend-->>API: Response {query_id}
    API-->>QueryForm: query_id received

    %% WebSocket Connection
    Note over QueryForm,WebSocket: 2. WEBSOCKET CONNECTION
    QueryForm->>API: connectWebSocket(query_id)
    API->>WebSocket: Establish WS connection /ws/{query_id}
    WebSocket-->>API: Connection established
    API-->>ProgressTracker: WebSocket ready

    %% Processing Phase
    Note over QueryService,NanoSage: 3. PROCESSING PHASE
    QueryService->>QueryService: Start background task
    QueryService->>NanoSage: Initialize SearchSession(params)

    activate NanoSage
    NanoSage->>NanoSage: Query analysis
    NanoSage->>WebSocket: Progress: "Analyzing query..." (10%)
    WebSocket->>ProgressTracker: Broadcast progress update
    ProgressTracker->>User: Display progress bar 10%

    NanoSage->>NanoSage: Web search (if enabled)
    NanoSage->>WebSocket: Progress: "Searching web..." (30%)
    WebSocket->>ProgressTracker: Broadcast progress update
    ProgressTracker->>User: Display progress bar 30%

    NanoSage->>NanoSage: Local corpus search
    NanoSage->>WebSocket: Progress: "Searching corpus..." (50%)
    WebSocket->>ProgressTracker: Broadcast progress update
    ProgressTracker->>User: Display progress bar 50%

    NanoSage->>NanoSage: Build search tree
    NanoSage->>WebSocket: Progress: "Building tree..." (70%)
    WebSocket->>ProgressTracker: Broadcast progress update
    ProgressTracker->>User: Display progress bar 70%

    NanoSage->>NanoSage: Generate final answer (LLM)
    NanoSage->>WebSocket: Progress: "Generating answer..." (90%)
    WebSocket->>ProgressTracker: Broadcast progress update
    ProgressTracker->>User: Display progress bar 90%

    NanoSage->>QueryService: Return results
    deactivate NanoSage

    %% Completion Phase
    Note over QueryService,ResultsDisplay: 4. COMPLETION PHASE
    QueryService->>QueryService: Save results to disk<br/>(results/{query_id}/)
    QueryService->>QueryService: Update status: completed
    QueryService->>WebSocket: Progress: "Completed" (100%)
    WebSocket->>ProgressTracker: Broadcast completion
    ProgressTracker->>User: Display progress bar 100%

    ProgressTracker->>API: getQuery(query_id)
    API->>Backend: GET /api/query/{query_id}
    Backend->>QueryService: get_query(query_id)
    QueryService-->>Backend: Return full results
    Backend-->>API: Response with results
    API-->>ResultsDisplay: Display results

    ResultsDisplay->>User: Show Final Answer tab
    ResultsDisplay->>User: Show Sources tab
    ResultsDisplay->>User: Show Search Tree tab

    %% Export Phase (Optional)
    Note over User,Backend: 5. EXPORT PHASE (Optional)
    User->>ResultsDisplay: Click Export button
    ResultsDisplay->>API: exportQuery(query_id, format)
    API->>Backend: POST /api/query/export
    Backend->>Backend: Generate file (MD/TXT/PDF)
    Backend->>Backend: Save to exports/ directory
    Backend-->>API: Return file download URL
    API-->>ResultsDisplay: Trigger download
    ResultsDisplay->>User: Download file
```

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend (React + TypeScript)"
        A[User] --> B[QueryForm Component]
        B --> C[API Service - api.ts]
        C --> D[ProgressTracker Component]
        C --> E[ResultsDisplay Component]
        C --> F[SearchTree Component]
        C --> G[ExportPanel Component]
    end

    subgraph "Backend (FastAPI + Python)"
        H[main.py - FastAPI App]
        I[models.py - Pydantic Models]
        J[query_service.py]
        K[export_service.py]
        L[websocket.py]
        M[validators.py]
        N[file_upload_service.py]
        O[history_service.py]
    end

    subgraph "NanoSage Core Engine"
        P[SearchSession]
        Q[Knowledge Base]
        R[LLM Interface]
        S[Web Crawler]
    end

    subgraph "External Services"
        T[Tavily API - Web Search]
        U[Ollama - Local LLM]
    end

    subgraph "Storage"
        V[(results/ - Query Results)]
        W[(exports/ - Export Files)]
        X[(uploads/ - User Files)]
    end

    C -->|HTTP POST/GET| H
    C -->|WebSocket| L
    H --> I
    H --> J
    H --> K
    H --> L
    H --> M
    H --> N
    H --> O

    J --> P
    K --> W
    N --> X
    O --> V

    P --> Q
    P --> R
    P --> S
    P --> T
    R --> U

    J --> V
    L -->|Broadcast| D
    E --> F

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#fff4e1
    style H fill:#e1ffe1
    style P fill:#ffe1f5
    style V fill:#f0f0f0
    style W fill:#f0f0f0
    style X fill:#f0f0f0
```

## Data Flow Overview

```mermaid
flowchart LR
    A[User Input] --> B{Validation}
    B -->|Valid| C[Generate UUID]
    B -->|Invalid| A
    C --> D[WebSocket Connect]
    D --> E[Background Processing]

    E --> F[Query Analysis]
    F --> G{Web Search?}
    G -->|Yes| H[Fetch Web Results]
    G -->|No| I[Local Search]
    H --> I

    I --> J[Build Search Tree]
    J --> K[Generate Final Answer<br/>via LLM]
    K --> L[Save Results]
    L --> M[Notify Frontend]

    M --> N[Display Results]
    N --> O{User Action}
    O -->|Export| P[Generate File]
    O -->|New Query| A
    O -->|View History| Q[Load Historical Query]

    P --> R[Download File]
    Q --> N

    style A fill:#e1f5ff
    style E fill:#ffe1e1
    style K fill:#ffe1f5
    style N fill:#e1ffe1
    style R fill:#f0f0f0
```

## WebSocket Communication Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant WebSocket
    participant Backend
    participant SearchSession

    Frontend->>WebSocket: Connect /ws/{query_id}
    WebSocket-->>Frontend: Connection Established

    loop Query Processing
        SearchSession->>Backend: Emit progress log
        Backend->>WebSocket: Broadcast message
        WebSocket->>Frontend: {status, message, progress}
        Frontend->>Frontend: Update UI
    end

    alt Connection Lost
        Frontend->>Frontend: Detect disconnect
        Frontend->>Frontend: Start polling fallback
        Frontend->>Backend: GET /api/query/{id}
        Backend-->>Frontend: Current status
    else Connection Active
        SearchSession->>Backend: Processing complete
        Backend->>WebSocket: Final status (100%)
        WebSocket->>Frontend: Completion message
        Frontend->>Frontend: Fetch full results
    end

    Frontend->>WebSocket: Disconnect
```

## Technology Stack Integration

```mermaid
graph LR
    subgraph "Frontend Stack"
        A1[React 18]
        A2[TypeScript 4.9]
        A3[Axios]
        A4[react-markdown]
    end

    subgraph "Backend Stack"
        B1[FastAPI]
        B2[Python 3.8+]
        B3[Pydantic v2]
        B4[Uvicorn]
        B5[WebSocket]
    end

    subgraph "Core ML Stack"
        C1[PyTorch]
        C2[Transformers]
        C3[Sentence-Transformers]
        C4[Ollama]
    end

    subgraph "Search & Export"
        D1[Tavily API]
        D2[BeautifulSoup4]
        D3[ReportLab]
    end

    A1 --> B1
    A3 --> B1
    B1 --> B5
    B1 --> B3
    B1 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    B1 --> D1
    B1 --> D2
    B1 --> D3

    style A1 fill:#61dafb
    style B1 fill:#009688
    style C1 fill:#ee4c2c
    style D1 fill:#ffd700
```

---

## Diagram Legend

- **Blue boxes**: User-facing components
- **Green boxes**: Backend services
- **Pink boxes**: Core processing engine
- **Gray boxes**: Storage/persistence layer
- **Yellow boxes**: External services

## Notes

1. All HTTP requests use Axios with base URL configuration
2. WebSocket provides real-time progress updates with polling fallback
3. Query processing is asynchronous using FastAPI background tasks
4. Results are persisted to disk in `results/{query_id}/` directory
5. Export files are generated on-demand and saved to `exports/` directory
