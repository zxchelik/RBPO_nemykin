# DFD — Data Flow Diagram

```mermaid
flowchart LR
    EXT[External User] -->|F1: HTTPS /login| GW[API Gateway]
    GW -->|F2: Auth request| AUTH[Auth Service]
    AUTH -->|F3: SQL (credentials check)| DB[(Users DB)]
    EXT -->|F4: HTTPS /tasks CRUD| GW
    GW -->|F5: Internal gRPC| TASK[Task Service]
    TASK -->|F6: SQL read/write| DB2[(Tasks DB)]

    subgraph Edge["Trust Boundary: Edge"]
        GW
    end

    subgraph Core["Trust Boundary: Core"]
        AUTH
        TASK
        DB
        DB2
    end

    style EXT stroke-width:2px,stroke:#333,fill:#f2f2f2
    style GW stroke-width:2px,stroke:#0066cc
    style AUTH stroke-width:2px,stroke:#009900
    style TASK stroke-width:2px,stroke:#009900
    style DB stroke-dasharray:3 3
    style DB2 stroke-dasharray:3 3
