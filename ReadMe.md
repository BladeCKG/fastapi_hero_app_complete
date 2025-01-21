### README: Kubernetes Cluster for FastAPI Hero Application

#### Overview
This project sets up a Kubernetes-based environment for deploying a FastAPI application with a PostgreSQL backend and Prometheus monitoring. The setup is highly available, monitored, and runs on a local Kind cluster.

---

### Prerequisites
1. Docker installed locally.
2. Kind (Kubernetes in Docker) installed.
3. `kubectl` CLI installed.
4. Helm installed for managing Kubernetes charts.

---

### Steps to Reproduce

#### 1. **Cluster Setup**
1. Create a Kubernetes cluster using Kind:
   ```bash
   kind create cluster --config kubernetes/kind-config.yaml --name kind-hero-and-pg
   ```
   - The cluster configuration is defined in `kubernetes/kind-config.yaml`.

#### 2. **PostgreSQL Setup**
1. Deploy the CloudNativePG operator:
   ```bash
   kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.0.yaml
   ```
2. Confirm the deployment:
   ```bash
   kubectl get deployment -n cnpg-system cnpg-controller-manager
   ```
3. Apply the PostgreSQL cluster manifest:
   ```bash
   kubectl apply -f kubernetes/postgres-cluster.yaml
   ```
   - Configures a PostgreSQL cluster with monitoring enabled and credentials stored in `kubernetes/mydb-secret.yaml`.

#### 3. **Monitoring Setup**
1. Add Prometheus Helm repository:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   ```
2. Install Prometheus stack:
   ```bash
   helm upgrade --install -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/samples/monitoring/kube-stack-config.yaml prometheus-community prometheus-community/kube-prometheus-stack
   ```
3. Apply Prometheus rules:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/samples/monitoring/prometheusrule.yaml
   ```

#### 4. **Hero Application Deployment**
1. Build the FastAPI application Docker image:
   ```bash
   docker build -t fastapi-hero:latest .
   ```
2. Load the Docker image into the Kind cluster:
   ```bash
   kind load docker-image fastapi-hero:latest --name kind-hero-and-pg
   ```
3. Create a namespace for the application:
   ```bash
   kubectl create ns fastapi-hero-ns
   ```
4. Deploy the PostgreSQL credentials:
   ```bash
   kubectl apply -f kubernetes/mydb-secret.yaml -n fastapi-hero-ns
   ```
5. Deploy the FastAPI application:
   ```bash
   kubectl apply -f kubernetes/hero-app.deployment.yaml -n fastapi-hero-ns
   ```
6. Expose the application:
   ```bash
   kubectl apply -f kubernetes/hero-app.service.yaml -n fastapi-hero-ns
   ```

#### 5. **Testing the Deployment**
1. Access the FastAPI application via:
   ```
   http://localhost:30002/docs
   ```
   - Provides Swagger UI for API interaction.
2. Verify database integration by using the API to create and retrieve heroes.

---

### Files in the Repository
1. **`Dockerfile`**: Containerizes the FastAPI application.
2. **`kubernetes/kind-config.yaml`**: Configures a Kind cluster.
3. **`kubernetes/mydb-secret.yaml`**: Secret for PostgreSQL credentials.
4. **`kubernetes/postgres-cluster.yaml`**: Configures PostgreSQL cluster with monitoring.
5. **`kubernetes/hero-app.deployment.yaml`**: Deploys the FastAPI application.
6. **`kubernetes/hero-app.service.yaml`**: Exposes the FastAPI application via NodePort.

---

### Additional Notes
- **Prometheus Metrics**: Monitor metrics with the `cnpg_` prefix.
- **Port Mapping**: Ports exposed for local access via `kind-config.yaml`.

### Conclusion
This setup demonstrates deploying and managing a monitored FastAPI application and PostgreSQL backend in a local Kubernetes cluster for testing and development purposes.