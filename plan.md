# Implementation Plan & Task Status

## Architecture Overview

Enterprise asynchronous microservices architecture orchestrated via an **API Gateway** with **gRPC inter-service communication** and **Database-per-Service persistence**:

```
                         [ External Client / Frontend (Web & Mobile) ]
                                               │
                                               │ HTTP / REST (:8080)
                                               ▼
                              ┌──────────────────────────────────┐
                              │  API Gateway & Orchestrator      │
                              │  - Unified OpenAPI / Swagger UI  │
                              │  - Composite Checkout Workflow   │
                              │  - Request Aggregation           │
                              └────────────────┬─────────────────┘
                                               │
            ┌──────────────────────────────────┼──────────────────────────────────┐
            │ gRPC (:50050)                    │ gRPC (:50051)                    │ HTTP / gRPC (:8002)
            ▼                                  ▼                                  ▼
┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│  User Service            │      │  Product Service         │      │  Order Service           │
│  - FastAPI REST (:8000)  │      │  - FastAPI REST (:8001)  │      │  - FastAPI REST (:8002)  │
│  - gRPC Server (:50050)  │      │  - gRPC Server (:50051)  │      │  - gRPC Auth Client      │
│  - JWT Auth (Login/Reg)  │      │  - Catalog & Inventory   │      │  - gRPC Stock Client     │
└────────────┬─────────────┘      └────────────┬─────────────┘      └────────────┬─────────────┘
             │                                 │                                 │
             ▼                                 ▼                                 ▼
      [ PostgreSQL /                    [ PostgreSQL /                    [ PostgreSQL /
         SQLite DB ]                       SQLite DB ]                       SQLite DB ]
      (users, auth, roles)              (products, stock)                 (orders, order_items)
```

---

## Task Status Matrix

| Task ID | Component / Area | Description | Status | Deliverables |
| :--- | :--- | :--- | :---: | :--- |
| **1.1** | Schema Contract | Shared `.proto` contract with `ProductService`, `ProductRequest`, `ProductResponse`, `ProductValidationRequest` | **COMPLETED** | `proto/product.proto` |
| **1.2** | Code Generation Script | Python script to compile `.proto` to `product_pb2.py` and `product_pb2_grpc.py` with relative import fixes | **COMPLETED** | `scripts/generate_proto.py` |
| **1.3** | Compiled Stubs | Generated protobuf and gRPC Python modules for Product Service | **COMPLETED** | `product_service/generated/product_pb2.py`<br>`product_service/generated/product_pb2_grpc.py` |
| **2.1** | Product Service Config | Environment-aware host/port settings for HTTP (8001) and gRPC (50051) | **COMPLETED** | `product_service/config.py` |
| **2.2** | Product Store | In-memory catalog repository with stock validation logic | **COMPLETED** | `product_service/store.py` |
| **2.3** | Product REST Models | Pydantic schema for external REST responses | **COMPLETED** | `product_service/models.py` |
| **2.4** | Product gRPC Servicer | `ProductServicer` handling `GetProduct`, `ListProducts`, and `ValidateProduct` | **COMPLETED** | `product_service/grpc_server.py` |
| **2.5** | Product Service Main | FastAPI app co-hosting async `grpc.aio.server` in application lifespan | **COMPLETED** | `product_service/main.py` |
| **3.1** | Order Service Config | Environment-aware settings for HTTP (8002) and Product gRPC host/port | **COMPLETED** | `order_service/config.py` |
| **3.2** | Order gRPC Client | Long-lived async `ProductGRPCClient` stub pool | **COMPLETED** | `order_service/grpc_client.py` |
| **3.3** | Order REST Models | Pydantic schemas for order creation request & response | **COMPLETED** | `order_service/models.py` |
| **3.4** | Order Store | In-memory order persistence repository | **COMPLETED** | `order_service/store.py` |
| **3.5** | Order Service Main | FastAPI app orchestrating gRPC stock checks before confirming orders | **COMPLETED** | `order_service/main.py` |
| **4.1** | Product Unit Tests | Product Service REST API test suite (6 tests) | **COMPLETED** | `tests/test_product_service.py` (6/6 passing) |
| **4.2** | Order Unit Tests | Order Service standalone health and auth enforcement tests | **COMPLETED** | `tests/test_order_service.py` (3/3 passing) |
| **4.3** | Core Docker Support | Dockerfiles for Product & Order Services + Docker Compose orchestration | **COMPLETED** | `product_service/Dockerfile`<br>`order_service/Dockerfile`<br>`docker-compose.yml`, `.dockerignore` |
| **4.4** | Project Requirements | Updated `requirements.txt` with categorized dependencies (FastAPI, gRPC, JWT, bcrypt) | **COMPLETED** | `requirements.txt` |
| **7.1** | User Proto Contract | Define `UserService` RPCs (`ValidateToken`, `GetUser`) in protobuf | **COMPLETED** | `proto/user.proto` |
| **7.2** | Proto Generator Update | Update `scripts/generate_proto.py` to compile all protos into `product_service` and `user_service` stubs | **COMPLETED** | `scripts/generate_proto.py`<br>`user_service/generated/` |
| **7.3** | User Service Security | Password hashing (`bcrypt`) and JWT creation/verification utilities | **COMPLETED** | `user_service/security.py` |
| **7.4** | User Service Config & Store | Configuration (JWT secret, ports) and in-memory user repository with seed accounts | **COMPLETED** | `user_service/config.py`<br>`user_service/store.py` |
| **7.5** | User REST Models | Pydantic schemas for `/auth/register`, `/auth/login`, and user profiles | **COMPLETED** | `user_service/models.py` |
| **7.6** | User gRPC Servicer | `UserServiceServicer` implementing `ValidateToken` and `GetUser` over gRPC | **COMPLETED** | `user_service/grpc_server.py` |
| **7.7** | User Service Main | FastAPI app co-hosting `grpc.aio.server` on port `50050` with auth REST routes | **COMPLETED** | `user_service/main.py` |
| **7.8** | Order Service Auth Client | Async gRPC client in Order Service to validate incoming Bearer tokens | **COMPLETED** | `order_service/grpc_auth_client.py` |
| **7.9** | Order Protected Routes | Integrate JWT validation dependency into Order creation and listing routes | **COMPLETED** | `order_service/main.py` |
| **7.10** | User Service Dockerfile | Dockerfile for `user_service` and Docker Compose integration | **COMPLETED** | `user_service/Dockerfile`<br>`docker-compose.yml` |
| **7.11** | User Service Tests | Unit and integration tests for JWT issuance and gRPC token validation | **COMPLETED** | `tests/test_user_service.py` (9/9 passing) |
| **9.1** | DB Dependencies | Add `SQLAlchemy 2.0` (async), `aiosqlite`, and `asyncpg` to `requirements.txt` | **COMPLETED** | `requirements.txt` |
| **9.2** | User Service Persistence | SQLAlchemy async database connection & `UserModel` with seed migration | **COMPLETED** | `user_service/database.py`<br>`user_service/models_db.py` |
| **9.3** | Product Service Persistence | SQLAlchemy async database connection & `ProductModel` with inventory checks | **COMPLETED** | `product_service/database.py`<br>`product_service/models_db.py` |
| **9.4** | Order Service Persistence | SQLAlchemy async database connection & `OrderModel` + `OrderItemModel` | **COMPLETED** | `order_service/database.py`<br>`order_service/models_db.py` |
| **10.1** | API Gateway Configuration | Port settings (`:8080`), gRPC client targets for User & Product services, Order URL | **COMPLETED** | `api_gateway/config.py` |
| **10.2** | Gateway gRPC Clients | High-performance async gRPC client stubs for `UserService` and `ProductService` | **COMPLETED** | `api_gateway/clients/` |
| **10.3** | Gateway Orchestrator | Composite checkout workflow (token auth $\rightarrow$ stock check $\rightarrow$ order placement) | **COMPLETED** | `api_gateway/orchestrator.py` |
| **10.4** | Gateway Reverse Proxy & API | Unified REST routes (`/api/v1/auth`, `/api/v1/catalog`, `/api/v1/orders`, `/api/v1/checkout`) | **COMPLETED** | `api_gateway/main.py` |
| **10.5** | Gateway Dockerfile & Compose | Dockerfile for `api_gateway` and multi-service Docker Compose with PostgreSQL | **COMPLETED** | `api_gateway/Dockerfile`<br>`docker-compose.yml` |
| **10.6** | Gateway Orchestration Tests | Integration test verifying unified checkout and service orchestration | **COMPLETED** | `tests/test_api_gateway.py` |
| **11.1** | OpenTelemetry Tracing | Distributed tracing across FastAPI HTTP and gRPC boundaries | **UNCOMPLETED** (P1; tracked in 12.7) | Tracing interceptors |

---

## Prioritized Reliability & Security Backlog

Ranked by importance. **P0** blocks safe production use; **P1** is needed before production; **P2** improves API and deployment quality. Task 11.1 is included in rank 5 under task 12.7. Completed items below were verified against the current implementation. The end-to-end run exercised the four live services and their isolated databases.

| Rank | Task ID | Priority | Work | Status | Acceptance criteria / deliverables |
| :--- | :---: | :--- | :---: | :--- |
| **12.1** | P0 | Fix user serialization defect | **COMPLETED** | `UserModel.to_dict()` returns `self.hashed_password`; registration, lookup, and the full existing suite work. |
| **12.2** | P0 | Protect user and order data | **COMPLETED** | `GET /users` requires an administrator; orders persist `user_id`; customers can list and fetch only their own orders, while administrators can view all. Existing orders receive a nullable ownership column through a compatibility upgrade. |
| **1** | **12.3** | P0 | Make inventory reservation atomic | **UNCOMPLETED** | Reserve/decrement stock atomically so concurrent checkouts cannot oversell; release reservations when order creation fails, with explicit reservation/compensation behavior. |
| **2** | **12.4** | P0 | Require production secrets and protect service traffic | **UNCOMPLETED** | Remove the known JWT secret fallback in production; fail startup when required secrets are absent; secure gRPC with TLS or authenticated service-to-service credentials and document local development settings. |
| **3** | **12.5** | P1 | Make order creation retry-safe and resilient | **UNCOMPLETED** | Accept idempotency keys; set explicit gRPC deadlines; standardize downstream error responses; define recovery/compensation for partial failure between inventory reservation and order persistence. |
| **4** | **12.6** | P1 | Harden data types and database operations | **UNCOMPLETED** | Use fixed-precision decimal currency; add versioned database migrations instead of relying on `create_all()`; document/configure backups, connection limits, and restore procedures. |
| **5** | **12.7** | P1 | Add operational visibility and dependency readiness | **UNCOMPLETED** | Add structured logs with request/trace IDs, latency/error metrics, distributed HTTP/gRPC tracing, and readiness checks that report required dependency health. Includes task 11.1. |
| **6** | **12.8** | P1 | Tighten API and deployment contracts | **UNCOMPLETED** | Update README for all four services, routes, methods, and ports; validate email and stronger passwords; set request-size and rate limits; expose only the Gateway publicly where appropriate. |

---

## Service Endpoints & Port Map

| Service | Port | Protocols | Primary Responsibilities |
| :--- | :---: | :---: | :--- |
| **API Gateway** | `8080` | HTTP / REST | Public entrypoint, request aggregation, composite checkout orchestration |
| **User Service** | `8000` / `50050` | HTTP / gRPC | User accounts, password hashing, JWT generation, gRPC token validation |
| **Product Service** | `8001` / `50051` | HTTP / gRPC | Product catalog, pricing, inventory stock validation RPC |
| **Order Service** | `8002` | HTTP | Order placement, validates token via User gRPC & stock via Product gRPC |

---

## How to Run (Current Implemented Services)

### Local PowerShell Runner:
```powershell
.\run_services.ps1
```

### Run Tests:
```powershell
.\venv\Scripts\pytest.exe -v
```
*(Run `.\venv\Scripts\pytest.exe -v` after installing dependencies.)*
