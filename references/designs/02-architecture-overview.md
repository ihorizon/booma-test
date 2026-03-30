# Booma Ride Share Portal — Architecture Overview

## 1. Guiding Principles

| Principle | Rationale |
|---|---|
| **Web-first** | Passengers book via browser; no app install required |
| **Start modular, extract later** | Avoid premature microservice complexity |
| **Event-driven for real-time** | WebSocket + message queue decouple producers and consumers |
| **Regional isolation** | Trip data never crosses regions; reduces latency and meets data sovereignty requirements |
| **Security by default** | JWT in memory, refresh in HttpOnly cookie, server-side claim validation everywhere |
| **Replaceable components** | Each layer has a clean interface; swap implementations without rewriting callers |

---

## 2. High-Level System Context

The Booma platform serves three distinct user groups across two interfaces: a passenger web portal (the primary focus of this document) and a driver mobile app. A separate admin portal (as shown in the supplied design) manages user and driver accounts.

```mermaid
C4Context
    title Booma Platform — System Context

    Person(passenger, "Passenger", "Books rides via web browser")
    Person(driver, "Driver", "Accepts and completes rides via mobile app")
    Person(admin, "Admin", "Manages users, drivers, payouts via admin portal")

    System(booma, "Booma Platform", "Web booking portal, driver app, admin portal, and backend services")

    System_Ext(maps, "Google Maps / Mapbox", "Geocoding, routing, ETA")
    System_Ext(stripe, "Stripe", "Payment processing and payouts")
    System_Ext(sms, "Twilio / SNS", "SMS OTP and push notifications")
    System_Ext(email, "SendGrid", "Transactional email (receipts, alerts)")

    Rel(passenger, booma, "Books, tracks, and pays for rides", "HTTPS / WSS")
    Rel(driver, booma, "Receives and completes ride requests", "HTTPS / WSS")
    Rel(admin, booma, "Manages accounts and operations", "HTTPS")
    Rel(booma, maps, "Address search, routing, ETA")
    Rel(booma, stripe, "Charge cards, pay drivers")
    Rel(booma, sms, "OTP, ride alerts")
    Rel(booma, email, "Receipts, account emails")
```

---

## 3. Container Architecture

The platform is structured as a set of backend services behind a unified API Gateway, with three frontend clients.

```mermaid
C4Container
    title Booma Platform — Containers

    Person(passenger, "Passenger")
    Person(driver, "Driver")
    Person(admin, "Admin")

    Container_Boundary(frontend, "Frontend Layer") {
        Container(web_portal, "Passenger Web Portal", "React / Next.js", "Web booking UI — address search, map, ride tracking")
        Container(driver_app, "Driver App", "React Native", "Ride acceptance, navigation, status updates")
        Container(admin_portal, "Admin Portal", "React / Next.js", "User management, payout records, reports")
    }

    Container_Boundary(gateway, "API Layer") {
        Container(api_gw, "API Gateway", "Kong / AWS API GW", "Auth enforcement, rate limiting, routing, TLS termination")
        Container(ws_gw, "WebSocket Gateway", "Node.js / Socket.IO", "Persistent real-time connections for tracking")
    }

    Container_Boundary(services, "Backend Services") {
        Container(auth_svc, "Auth Service", "Node.js", "Registration, login, JWT issuance, token refresh, OAuth")
        Container(booking_svc, "Booking Service", "Node.js", "Ride requests, matching, status machine, scheduling")
        Container(location_svc, "Location Service", "Go", "Driver GPS ingestion, proximity search, live tracking fan-out")
        Container(payment_svc, "Payment Service", "Node.js", "Stripe integration, fare capture, refunds, driver payouts")
        Container(notification_svc, "Notification Service", "Node.js", "Push, SMS, email dispatch")
        Container(user_svc, "User Service", "Node.js", "Passenger profiles, saved addresses, ride history")
    }

    Container_Boundary(data, "Data Layer") {
        ContainerDb(pg, "PostgreSQL", "Database", "Users, rides, payments (ACID)")
        ContainerDb(redis, "Redis", "Cache / GEO", "Driver locations, sessions, locks")
        ContainerDb(kafka, "Kafka", "Message Broker", "GPS events, booking events, notifications")
    }

    Rel(passenger, web_portal, "Uses", "HTTPS")
    Rel(driver, driver_app, "Uses", "HTTPS / WSS")
    Rel(admin, admin_portal, "Uses", "HTTPS")

    Rel(web_portal, api_gw, "REST API calls", "HTTPS/JSON")
    Rel(web_portal, ws_gw, "Live tracking", "WSS")
    Rel(driver_app, api_gw, "REST API calls", "HTTPS/JSON")
    Rel(driver_app, ws_gw, "GPS stream + ride events", "WSS")
    Rel(admin_portal, api_gw, "REST API calls", "HTTPS/JSON")

    Rel(api_gw, auth_svc, "Routes /auth/*")
    Rel(api_gw, booking_svc, "Routes /bookings/*")
    Rel(api_gw, payment_svc, "Routes /payments/*")
    Rel(api_gw, user_svc, "Routes /users/*")

    Rel(location_svc, redis, "GEOADD / GEOSEARCH")
    Rel(location_svc, kafka, "Publishes GPS events")
    Rel(booking_svc, kafka, "Publishes booking events")
    Rel(booking_svc, pg, "Reads/writes ride records")
    Rel(notification_svc, kafka, "Subscribes to events")
    Rel(auth_svc, pg, "User credentials, refresh tokens")
    Rel(payment_svc, pg, "Payment records")
    Rel(ws_gw, location_svc, "Subscribes to driver locations")
```

---

## 4. Ride Booking Flow

This is the core user journey: a passenger requests a ride, a driver is matched and accepts, and the ride is completed with payment captured.

```mermaid
sequenceDiagram
    autonumber
    actor P as Passenger (Browser)
    participant WP as Web Portal
    participant GW as API Gateway
    participant BS as Booking Service
    participant LS as Location Service
    participant PS as Payment Service
    participant NS as Notification Service
    actor D as Driver App

    P->>WP: Enter pickup + destination
    WP->>GW: GET /bookings/estimate
    GW->>BS: Forward (JWT validated)
    BS->>LS: Find nearest drivers (GEOSEARCH)
    LS-->>BS: Driver list + ETAs
    BS-->>WP: Fare estimate, ETA, vehicle options

    P->>WP: Confirm booking
    WP->>GW: POST /bookings
    GW->>BS: Create ride record (status: SEARCHING)
    BS->>LS: Query nearby available drivers
    BS->>D: Push ride request via WebSocket
    D->>GW: POST /bookings/{id}/accept
    GW->>BS: Update status: ACCEPTED
    BS->>NS: Emit booking_accepted event
    NS-->>P: Browser notification + status update

    loop Every 4 seconds
        D->>GW: POST /drivers/location {lat, lng}
        GW->>LS: Update Redis GEO
        LS-->>WP: Fan-out via WebSocket (driver pin moves)
    end

    D->>GW: POST /bookings/{id}/arrived
    BS->>NS: Emit driver_arrived event
    NS-->>P: "Your driver has arrived"

    D->>GW: POST /bookings/{id}/start
    BS: Update status: IN_PROGRESS

    D->>GW: POST /bookings/{id}/complete
    BS->>PS: Capture payment (Stripe)
    PS-->>BS: Payment confirmed
    BS: Update status: COMPLETED
    BS->>NS: Emit ride_completed event
    NS-->>P: Receipt email + in-app confirmation
```

---

## 5. Ride State Machine

Every ride record moves through a well-defined set of states. Invalid transitions are rejected by the Booking Service.

```mermaid
stateDiagram-v2
    [*] --> ESTIMATING : passenger requests fare
    ESTIMATING --> SEARCHING : passenger confirms booking
    SEARCHING --> ACCEPTED : driver accepts
    SEARCHING --> CANCELLED : timeout / no drivers
    ACCEPTED --> DRIVER_ARRIVED : driver marks arrived
    ACCEPTED --> CANCELLED : driver cancels
    DRIVER_ARRIVED --> IN_PROGRESS : driver starts ride
    IN_PROGRESS --> COMPLETED : driver ends ride
    IN_PROGRESS --> CANCELLED : emergency cancellation
    COMPLETED --> [*]
    CANCELLED --> [*]

    note right of SEARCHING
        Max wait: 60 seconds
        Re-broadcasts every 15 seconds
        to expanding radius
    end note

    note right of COMPLETED
        Payment captured
        Receipt emitted
        Driver rated
    end note
```

---

## 6. Data Model (Conceptual ERD)

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email
        string phone
        string full_name
        string password_hash
        string role
        timestamp created_at
        timestamp updated_at
    }

    SAVED_ADDRESSES {
        uuid id PK
        uuid user_id FK
        string label
        string formatted_address
        float lat
        float lng
    }

    DRIVERS {
        uuid id PK
        uuid user_id FK
        string vehicle_make
        string vehicle_model
        string vehicle_plate
        string status
        float current_lat
        float current_lng
        float rating
    }

    RIDES {
        uuid id PK
        uuid passenger_id FK
        uuid driver_id FK
        string status
        string pickup_address
        float pickup_lat
        float pickup_lng
        string destination_address
        float destination_lat
        float destination_lng
        decimal fare_estimate
        decimal fare_final
        timestamp requested_at
        timestamp completed_at
    }

    PAYMENTS {
        uuid id PK
        uuid ride_id FK
        string stripe_payment_intent_id
        decimal amount
        string currency
        string status
        timestamp captured_at
    }

    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        boolean revoked
    }

    USERS ||--o{ SAVED_ADDRESSES : "has"
    USERS ||--o| DRIVERS : "can be"
    USERS ||--o{ RIDES : "books as passenger"
    DRIVERS ||--o{ RIDES : "completes"
    RIDES ||--o| PAYMENTS : "has"
    USERS ||--o{ REFRESH_TOKENS : "holds"
```

---

## 7. Frontend Architecture (Passenger Web Portal)

```mermaid
graph TD
    subgraph Browser
        A[Next.js App Router]
        B[React Server Components]
        C[Client Components]
        D[Zustand — Global State]
        E[React Query — Server State]
        F[MapboxGL — Interactive Map]
        G[WebSocket Client]
    end

    subgraph Pages
        P1[/ — Landing / Login]
        P2[/book — Booking Flow]
        P3[/ride/:id — Live Tracking]
        P4[/history — Past Rides]
        P5[/account — Profile / Payments]
    end

    A --> B
    A --> C
    C --> D
    C --> E
    P2 --> F
    P3 --> F
    P3 --> G
    E -->|REST calls| API[API Gateway]
    G -->|WSS| WSG[WebSocket Gateway]
```

### 7.1 Key Frontend Libraries

| Library | Purpose |
|---|---|
| Next.js 14 (App Router) | SSR, routing, image optimisation |
| React 18 | UI component tree |
| Zustand | Lightweight global state (auth, active ride) |
| React Query (TanStack) | Data fetching, caching, background refresh |
| MapboxGL JS | Interactive map, driver pins, route polyline |
| Socket.IO Client | WebSocket with auto-reconnect |
| React Hook Form + Zod | Form validation |
| Tailwind CSS | Utility-first styling |

---

## 8. Backend Service Design

### 8.1 Auth Service

Responsibilities: registration, login, JWT issuance, token refresh, OAuth callback, password reset.

```mermaid
sequenceDiagram
    participant C as Client
    participant AS as Auth Service
    participant DB as PostgreSQL
    participant Cache as Redis

    C->>AS: POST /auth/login {email, password}
    AS->>DB: Fetch user by email
    AS->>AS: bcrypt.verify(password, hash)
    AS->>AS: Sign access_token (15 min JWT)
    AS->>AS: Sign refresh_token (30 days, opaque)
    AS->>DB: Store refresh_token hash
    AS-->>C: { access_token } + Set-Cookie: refresh_token (HttpOnly, Secure, SameSite=Strict)

    Note over C,AS: Subsequent requests
    C->>AS: POST /auth/refresh (Cookie: refresh_token)
    AS->>DB: Validate token hash, check expiry
    AS->>DB: Rotate — invalidate old, issue new
    AS-->>C: { access_token } + Set-Cookie: new refresh_token
```

### 8.2 Booking Service State Transitions

The Booking Service owns the canonical ride state and enforces all valid transitions. It publishes events to Kafka on every state change so downstream services (notifications, payments, analytics) react without tight coupling.

```mermaid
graph LR
    A[POST /bookings] -->|Creates record| B[(PostgreSQL\nstatus: SEARCHING)]
    B -->|Driver accepts| C[status: ACCEPTED]
    B -->|Timeout / no drivers| D[status: CANCELLED]
    C -->|Driver arrives| E[status: DRIVER_ARRIVED]
    C -->|Driver cancels| D
    E -->|Ride starts| F[status: IN_PROGRESS]
    F -->|Ride ends| G[status: COMPLETED]
    G -->|Event published| H[Kafka: ride_completed]
    H --> I[Payment Service\ncapture fare]
    H --> J[Notification Service\nsend receipt]
    H --> K[Analytics\nrecord trip]
```

### 8.3 Location Service

The Location Service is the most write-intensive component. Every active driver posts a GPS coordinate every 4 seconds.

```mermaid
graph TD
    D[Driver App] -->|POST /drivers/location| GW[API Gateway]
    GW -->|Validated JWT| LS[Location Service - Go]
    LS -->|GEOADD driver_id lat lng| R[(Redis GEO)]
    LS -->|Publish gps_update| K[Kafka]

    subgraph Fan-out
        K -->|Consumed by| WS[WebSocket Gateway]
        WS -->|Push to subscribed passengers| P[Passenger Browsers]
    end

    subgraph Proximity Search
        BS[Booking Service] -->|GEOSEARCH radius 5km| R
        R -->|Nearest driver IDs| BS
    end
```

---

## 9. Infrastructure and Deployment

```mermaid
graph TD
    subgraph CDN [CloudFront / Cloudflare CDN]
        STA[Static Assets\nJS, CSS, Images]
    end

    subgraph AWS ap-southeast-2 [AWS Region — Sydney]
        subgraph VPC
            subgraph Public Subnet
                ALB[Application Load Balancer\nHTTPS + WSS]
                NATGW[NAT Gateway]
            end

            subgraph Private Subnet — Services
                GW[API Gateway\nKong]
                WSGATE[WebSocket Gateway\nNode.js]
                AUTH[Auth Service]
                BOOK[Booking Service]
                LOC[Location Service\nGo]
                PAY[Payment Service]
                NOTIF[Notification Service]
            end

            subgraph Private Subnet — Data
                PG[(RDS PostgreSQL\nMulti-AZ)]
                REDIS[(ElastiCache Redis\nCluster)]
                MSK[(MSK Kafka\nManaged)]
            end
        end
    end

    subgraph External
        STRIPE[Stripe API]
        MAPS[Mapbox / Google Maps]
        TWILIO[Twilio SMS]
        SENDGRID[SendGrid]
    end

    Internet -->|HTTPS| CDN
    Internet -->|HTTPS / WSS| ALB
    ALB --> GW
    ALB --> WSGATE
    GW --> AUTH & BOOK & PAY & NOTIF
    WSGATE --> LOC
    LOC --> REDIS & MSK
    BOOK --> PG & MSK
    AUTH --> PG
    PAY --> STRIPE
    NOTIF --> TWILIO & SENDGRID
    LOC --> MAPS
```

### 9.1 Kubernetes Workload Summary

| Service | Replicas (normal) | Replicas (peak) | Scaling Trigger |
|---|---|---|---|
| API Gateway (Kong) | 2 | 4 | CPU > 70% |
| Auth Service | 2 | 4 | RPS > 500 |
| Booking Service | 2 | 6 | RPS > 200 |
| Location Service | 3 | 10 | Message lag > 1s |
| WebSocket Gateway | 3 | 8 | Connections > 5,000 |
| Payment Service | 2 | 4 | RPS > 100 |
| Notification Service | 2 | 4 | Queue depth |

---

## 10. Non-Functional Requirements Summary

| Requirement | Target | Approach |
|---|---|---|
| API response time (p99) | < 500 ms | Redis caching, DB read replicas |
| WebSocket latency | < 1 second | Go location service, Redis pub/sub |
| Availability | 99.9% | Multi-AZ RDS, Redis cluster, K8s restarts |
| Throughput | 100 bookings/sec peak | Horizontal pod autoscaling |
| Payment reliability | Zero double-charges | Stripe idempotency keys |
| Data residency | Australia | All services in `ap-southeast-2` |

---

*Previous: [01-market-research.md](./01-market-research.md) | Next: [03-security-architecture.md](./03-security-architecture.md)*
