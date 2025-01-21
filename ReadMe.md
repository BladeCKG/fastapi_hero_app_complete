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
   **File: `kubernetes/kind-config.yaml`**
   ```yaml
   apiVersion: kind.x-k8s.io/v1alpha4
   kind: Cluster
   nodes:
      - role: control-plane
         extraPortMappings:
            - containerPort: 80
               hostPort: 30001
               listenAddress: "127.0.0.1"
               protocol: TCP # Exposes port 80 of the cluster for future applications.
            - containerPort: 30002
               hostPort: 30002
               protocol: TCP # Maps the FastAPI application service port.
      - role: worker # Worker node for application workloads.
      - role: worker # Additional worker for scalability.
      - role: worker # Another worker for potential distributed load.

   ```
   **Explanation**:
   - The control plane and workers are configured for a simple local cluster.
   - Extra port mappings expose specific ports for local testing.

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
   **File: `kubernetes/postgres-cluster.yaml`**
   ```yaml
   apiVersion: postgresql.cnpg.io/v1
   kind: Cluster
   metadata:
      name: cluster-with-metrics # Name of the PostgreSQL cluster for identification.
   spec:
      instances: 3 # Configures 3 instances for high availability.
      storage:
         size: 1Gi # Specifies storage size for each instance (adjustable for testing).
      monitoring:
         enablePodMonitor: true # Enables Prometheus monitoring of this cluster.
      bootstrap:
         initdb:
            database: mydb # Prepares a database named `mydb` on initialization.
            owner: myuser # Creates a database user `myuser` with ownership.
            secret:
            name: mydb-secret # Uses a Kubernetes secret for credentials.
      postgresql:
         pg_hba:
            - host all all 0.0.0.0/0 scram-sha-256 # Configures access control using scram-sha-256 authentication.
   ```
   **Explanation**:
   - The `Cluster` resource sets up a high-availability PostgreSQL instance.
   - Predefined credentials ensure easy integration with the application.

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
   **File: `kubernetes/mydb-secret.yaml`**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
      name: mydb-secret # Name of the secret for application reference.
   type: kubernetes.io/basic-auth # Standard secret type for database credentials.
   data:
      username: bXl1c2Vy # Base64-encoded value for "myuser".
      password: bXlwYXNzd29yZA== # Base64-encoded value for "mypassword".
   ```
   **Explanation**:
   - Secrets store credentials securely in Kubernetes.
5. Deploy the FastAPI application:
   ```bash
   kubectl apply -f kubernetes/hero-app.deployment.yaml -n fastapi-hero-ns
   ```
   **File: `kubernetes/hero-app.deployment.yaml`**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
      name: fastapi-hero # Name of the deployment.
      namespace: fastapi-hero-ns # Isolates the application in a dedicated namespace.
   spec:
      replicas: 1 # Single replica for simplicity in local testing (can scale as needed).
      selector:
         matchLabels:
            app: fastapi-hero # Matches pods labeled with `app: fastapi-hero`.
      template:
         metadata:
            labels:
            app: fastapi-hero # Labels for selectors and identification.
         spec:
            containers:
               - name: fastapi-hero
                  image: fastapi-hero:latest # Uses the locally built image for the application.
                  imagePullPolicy: Never # Ensures the image is not pulled from a remote registry.
                  ports:
                     - containerPort: 8000 # Container port exposed for FastAPI.
                  env:
                     - name: POSTGRES_HOST
                        value: cluster-with-metrics-rw.default.svc.cluster.local # Service DNS name for PostgreSQL.
                     - name: POSTGRES_PORT
                        value: "5432" # PostgreSQL default port.
                     - name: POSTGRES_DB
                        value: mydb # Database name.
                     - name: POSTGRES_USER
                        valueFrom:
                           secretKeyRef:
                              name: mydb-secret # References the secret for username.
                              key: username
                     - name: POSTGRES_PASSWORD
                        valueFrom:
                           secretKeyRef:
                              name: mydb-secret # References the secret for password.
                              key: password
   ```
   **Explanation**:
   - Configures a single replica deployment with clear database connection details.
   - Uses Kubernetes secrets to inject sensitive data securely.
6. Expose the application:
   ```bash
   kubectl apply -f kubernetes/hero-app.service.yaml -n fastapi-hero-ns
   ```
   **File: `kubernetes/hero-app.service.yaml`**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
      name: fastapi-hero # Service name for DNS and references.
   spec:
      type: NodePort # Exposes the service to the host via a specific port.
      selector:
         app: fastapi-hero # Matches pods labeled `app: fastapi-hero`.
      ports:
         - protocol: TCP
            port: 80 # External port for accessing the application.
            targetPort: 8000 # Internal container port.
            nodePort: 30002 # NodePort mapped to the host for local testing.
   ```
   **Explanation**:
   - A `NodePort` service exposes the application locally for ease of access.
   - Port mappings make the FastAPI app accessible via `http://localhost:30002`.

---

### Testing the Deployment

#### 1. **Accessing the Application**
The application is accessible locally via NodePort:
   ```
   http://localhost:30002/docs
   ```
   - This URL provides the Swagger UI to interact with the FastAPI application.

#### 2. **Testing API Functionality**
- Use the `/heroes/` endpoints available in the Swagger UI to create and retrieve heroes.

#### 3. **Testing Database Connection**
To verify the connection to the PostgreSQL database:

1. **Port-forward the PostgreSQL service**:
   ```bash
   kubectl port-forward svc/cluster-with-metrics-rw 5432:5432 -n default
   ```
   - This command forwards port `5432` from the PostgreSQL service to your local machine.

2. **Connect using `psql` or a database client**:
   - Install `psql` or use a GUI database client like DBeaver or pgAdmin.
   - Use the following connection details:
     ```
     Host: localhost
     Port: 5432
     Database: mydb
     User: myuser
     Password: mypassword
     ```
   - Alternatively, connect using the `psql` CLI:
     ```bash
     psql -h localhost -U myuser -d mydb
     ```
     - When prompted for a password, use `mypassword`.

3. **Run SQL queries**:
   - After successfully connecting, verify the database structure and contents:
     ```sql
     \dt
     SELECT * FROM hero;
     ```
   - The `\dt` command lists all tables, and the `SELECT` command checks if any data exists in the `hero` table.

#### 4. **Verifying Prometheus**
To confirm Prometheus is running and collecting metrics:

1. **Port-forward the Prometheus server**:
   ```bash
   kubectl port-forward svc/prometheus-community-kube-prometheus 9090
   ```
   - This command forwards port `9090` from the Prometheus service to your local machine.

2. **Access the Prometheus dashboard**:
   - Open your browser and navigate to:
     ```
     http://localhost:9090
     ```

3. **Explore metrics**:
   - Use the search bar to query metrics such as:
     ```
     cnpg_
     ```
     - Metrics with the `cnpg_` prefix provide insights into the PostgreSQL cluster's performance and health.
   - Verify that Prometheus is actively collecting metrics from the PostgreSQL cluster and other monitored components.

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
- **Prometheus Metrics**: Metrics with the `cnpg_` prefix provide insights into PostgreSQL cluster health.
- **Port Mapping**: Ports exposed for local access are defined in `kubernetes/kind-config.yaml`.

### Conclusion
This guide details the deployment of a FastAPI application backed by PostgreSQL with Prometheus monitoring in a Kubernetes cluster. The setup is optimized for local development and testing using Kind.