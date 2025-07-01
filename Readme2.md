# CMBCluster Backend: Architecture & End-to-End Flow

## 1. Overview

The CMBCluster backend is a Python FastAPI application that serves as the central control plane, or **Hub**, for a multi-tenant scientific computing platform. It is responsible for authenticating users, managing the entire lifecycle of their isolated Kubernetes environments, and providing a secure API for the frontend to interact with.

## 2. Architecture Diagram

```mermaid
graph TD
    subgraph "External"
        Users[👥 Users]
        CloudVolumes[☁️ Cloud Storage]
        ImageRegistry[📦 Container Registry]
    end

    Users -- HTTPS --> Proxy[🌐 Wildcard Ingress Controller]
    
    subgraph "Kubernetes Cluster (Namespace: cmbcluster)"
        subgraph "Control Plane"
            direction LR
            Hub[🎯 Hub (Backend API)]
            Frontend[🖥️ Frontend UI]
        end

        subgraph "User Environment"
            direction LR
            UserPod[Pod: user-jane-doe-...]
            UserService[Service: service-jane-doe]
            UserPVC[PVC: workspace-jane-doe]
        end

        Proxy -- "api.domain.com" --> Hub
        Proxy -- "domain.com" --> Frontend
        Proxy -- "*.domain.com" --> UserService

        Hub -- "Manages (K8s API)" --> UserPod & UserService & UserPVC
        Hub -- "Uses SA: cmbcluster-ksa (Privileged)"
        UserPod -- "Uses SA: cmbcluster-user-sa (Unprivileged)"
    end
    
    CloudVolumes -- "Provisions" --> UserPVC
    ImageRegistry -- "Provides Image" --> UserPod
    
    style Users fill:#f9f,stroke:#333,stroke-width:2px
    style Proxy fill:#9f9,stroke:#333,stroke-width:2px
    style Hub fill:#9f9,stroke:#333,stroke-width:2px
    style PV fill:#99f,stroke:#333,stroke-width:2px
    style CloudVolumes fill:#bbf,stroke:#333,stroke-width:2px
    style ImageRegistry fill:#bbf,stroke:#333,stroke-width:2px
    style Frontend fill:#9f9,stroke:#333,stroke-width:2px
    style UserPod fill:#99f,stroke:#333,stroke-width:2px
    style UserService fill:#99f,stroke:#333,stroke-width:2px
    style UserPVC fill:#99f,stroke:#333,stroke-width:2px
```

## 3. End-to-End User Flow

This section details the complete journey of a user, from logging in to accessing their persistent, isolated research environment.

### Step 1: Authentication (User -> Hub)

1.  **Login Request**: The user clicks "Login" on the frontend, which directs them to the backend's `/auth/login` endpoint.
2.  **OAuth Redirect**: The Hub redirects the user to Google for OAuth 2.0 authentication.
3.  **Callback & Token Generation**: After a successful Google login, the user is redirected back to the Hub's `/auth/callback` endpoint. The Hub:
    -   Receives the user's profile information from Google.
    -   Creates or updates the user's record in its internal store.
    -   Generates a secure **JSON Web Token (JWT)** containing the user's ID, email, and an expiration time.
4.  **Session Establishment**: The Hub redirects the user back to the frontend, passing the JWT in the URL. The frontend stores this token and includes it in the `Authorization` header for all future API requests, effectively establishing a stateless session.

### Step 2: Environment Request (Hub -> K8s API)

1.  **API Call**: The authenticated frontend sends a request to `POST /environments` to create a new research environment.
2.  **Authorization**: The Hub validates the user's JWT to confirm their identity.
3.  **Orchestration**: The `PodManager` class takes over, preparing to create the necessary Kubernetes resources. It first sanitizes the `user_id` (e.g., `jane.doe@google.com` -> `jane-doe-google-com`) to ensure it's a valid DNS name for use in resource naming.

### Step 3: Resource Provisioning (K8s API -> User Environment)

The `PodManager` makes a series of calls to the Kubernetes API to build the user's environment:

1.  **Persistence (PersistentVolumeClaim)**:
    -   A `PersistentVolumeClaim` (PVC) named `workspace-<safe-user-id>` is created.
    -   This requests a block of storage (e.g., 10Gi) from the underlying cloud provider.
    -   **Crucially, this PVC is NOT deleted when the user logs out**. It persists, safeguarding the user's data in their `/workspace` directory for future sessions.

2.  **Compute (Pod)**:
    -   A Kubernetes `Pod` is created with a unique name (e.g., `user-jane-doe-google-com-1678886400`).
    -   The user's PVC is mounted into the pod at the `/workspace` path.
    -   The pod is assigned the **unprivileged** `cmbcluster-user-sa` service account, which has no permissions to interact with the Kubernetes API, effectively sandboxing the user's code.
    -   The pod is labeled with `user-id: <safe-user-id>`, which is essential for networking.

3.  **Internal Networking (Service)**:
    -   A `ClusterIP` Service named `service-<safe-user-id>` is created.
    -   This service is given a stable internal DNS name and IP address within the cluster.
    -   It uses a `selector` to automatically target and route internal traffic to any pod with the label `user-id: <safe-user-id>`.

### Step 4: Accessing the Environment (User -> Proxy -> Pod)

1.  **URL Generation**: The Hub returns the unique, public-facing URL for the new environment to the frontend (e.g., `https://jane-doe-google-com.cmbcluster.local`).
2.  **Wildcard Ingress Routing**: The user's browser navigates to this URL. The request hits the cluster's main NGINX Ingress Controller (the "Proxy").
3.  **Dynamic Forwarding**: The Ingress resource for `*.<base_domain>` is configured with a special `server-snippet` that:
    -   Extracts the subdomain from the hostname (`jane-doe-google-com`).
    -   Dynamically constructs the full internal service name (`service-jane-doe-google-com.cmbcluster.svc.cluster.local`).
    -   Forwards the user's request directly to the correct internal `Service`.
4.  **Final Hop**: The `Service` receives the traffic and routes it to the user's running `Pod` on port 8501, establishing a connection to their Streamlit application.

### Step 5: Session Teardown & Cleanup (Hub -> K8s API)

To conserve resources, environments are automatically culled when not in use.

1.  **Inactivity Monitoring**: A background task in the Hub (`monitor_environment`) periodically checks the `last_activity` timestamp of each environment. This timestamp is updated via the `/environments/heartbeat` endpoint.
2.  **Automated Deletion**: If an environment is inactive for longer than `max_inactive_hours`, the `PodManager` is triggered to delete it.
3.  **Resource Deletion**: The `PodManager` deletes the user's **Pod** and **Service**. This immediately frees up CPU, memory, and internal networking resources.
4.  **Data Persistence**: The user's **PVC is not deleted**, ensuring their `/workspace` data is safe and will be available the next time they log in and create an environment.

## 4. Security Model: Principle of Least Privilege

The platform's security relies on strict separation of privileges between the control plane and user environments.

-   **`cmbcluster-ksa` (Backend Service Account)**:
    -   **Privileged**: This account is used by the main backend `Deployment`.
    -   **Permissions**: It is bound to a `ClusterRole` that grants it the minimum necessary permissions: `get`, `list`, `create`, `delete` on `pods`, `services`, and `persistentvolumeclaims`.
    -   **Scope**: It can manage resources but cannot access cluster-wide secrets or modify other critical components.

-   **`cmbcluster-user-sa` (User Pod Service Account)**:
    -   **Unprivileged**: This account is assigned to every user-created pod.
    -   **Permissions**: It has **no roles bound to it**. It cannot read, create, or delete any resources in the Kubernetes API.
    -   **Purpose**: This creates a strong security sandbox. Even if a user's code is compromised, it cannot affect other users' environments or the cluster itself.

## 5. Deployment

The entire application stack is defined and managed as a single unit using **Helm**.

-   **`helm/`**: The Helm chart contains templates for all Kubernetes resources: Deployments, Services, Ingresses, and RBAC rules.
-   **`values.yaml`**: This file provides a centralized location for all configuration, such as domain names, image repositories, and resource limits.
-   **`scripts/deploy.sh`**: This script automates the entire deployment process. It:
    1.  Loads configuration from a `.env` file.
    2.  Builds and pushes container images.
    3.  Sets up Workload Identity bindings with Google Cloud.
    4.  Creates Kubernetes secrets.
    5.  Runs `helm upgrade --install`, passing in the correct configuration values to deploy or update the application on the cluster.