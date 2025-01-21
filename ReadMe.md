### README: Kubernetes Cluster for FastAPI Hero Application with PostgreSQL and Prometheus

#### Overview
This project demonstrates setting up a Kubernetes-based environment for running a highly available FastAPI application, backed by a PostgreSQL database and monitored using Prometheus. The solution is based on the requirements provided and uses tools like Kind for local Kubernetes clusters, Docker for containerization, and CloudNativePG for PostgreSQL management.

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
   - Configuration for the Kind cluster is defined in `kubernetes/kind-config.yaml`.

#### 2. **PostgreSQL Setup**
1. Deploy the CloudNativePG operator:
   ```bash
   kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.0.yaml
   ```
2. Verify the deployment of the operator:
   ```bash
   kubectl get deployment -n cnpg-system cnpg-controller-manager
   ```
3. Apply the PostgreSQL cluster manifest:
   ```bash
   kubectl apply -f kubernetes/postgres-cluster.yaml
   ```
   - The manifest includes the creation of a PostgreSQL database named `mydb` and a user `myuser` secured by credentials stored in a Kubernetes secret.

#### 3. **Monitoring Setup**
1. Add Prometheus Helm repository:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   ```
2. Install the Prometheus stack:
   ```bash
   helm upgrade --install -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/samples/monitoring/kube-stack-config.yaml prometheus-community prometheus-community/kube-prometheus-stack
   ```
3. Configure Prometheus rules:
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
4. Deploy secrets for the database connection:
   ```bash
   kubectl apply -f kubernetes/mydb-secret.yaml -n fastapi-hero-ns
   ```
5. Deploy the FastAPI application:
   ```bash
   kubectl apply -f kubernetes/hero-app.deployment.yml -n fastapi-hero-ns
   ```
6. Expose the application via a NodePort service:
   ```bash
   kubectl apply -f kubernetes/hero-app-service.yml -n fastapi-hero-ns
   ```

#### 5. **Testing the Deployment**
1. Access the application locally using the service's NodePort (default: 30002):
   ```
   http://localhost:30002/docs
   ```
   - This endpoint provides the Swagger UI for the FastAPI application.
2. Verify PostgreSQL integration by creating and retrieving heroes using the exposed API.

---

### Files in the Repository
- `Dockerfile`: Used to containerize the FastAPI application.
- `kubernetes/kind-config.yaml`: Configuration for creating a Kind cluster with exposed ports.
- `kubernetes/mydb-secret.yaml`: Kubernetes Secret for PostgreSQL credentials.
- `kubernetes/postgres-cluster.yaml`: Configuration for a highly available PostgreSQL cluster with monitoring enabled.
- `kubernetes/hero-app.deployment.yml`: Deployment manifest for the FastAPI application.
- `kubernetes/hero-app-service.yml`: Service manifest for exposing the FastAPI application.

---

### Additional Notes
- **NodePort Exposures**: Ports are mapped in the `kind-config.yaml` to expose the application and database locally.
- **Prometheus Metrics**: Metrics with the prefix `cnpg_` can be monitored via Prometheus.
- **Environment Variables**: The FastAPI application dynamically uses environment variables for database connection setup.

### Conclusion
This setup provides a scalable and monitored environment for a FastAPI application with PostgreSQL backend, all deployable on a local Kubernetes cluster for testing and development purposes.