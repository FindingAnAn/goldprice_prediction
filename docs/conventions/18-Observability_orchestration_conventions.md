# 18-Observability-Orchestration / Quy ước Observability và Triển khai Orchestration

## 1. Purpose / Mục đích

### EN
This document defines the conventions for deploying and operating the core infrastructure stack: Docker (containerization), Kubernetes (orchestration), Terraform (infrastructure as code), Prometheus + Grafana (observability), and Apache Airflow (workflow orchestration).  
Its purpose is to ensure that these tools are deployed consistently, securely, and in a way that an agent can reliably reproduce any environment from the code alone.

### VI
Tài liệu này định nghĩa các quy ước để triển khai và vận hành bộ infrastructure cốt lõi: Docker (container hóa), Kubernetes (orchestration), Terraform (IaC), Prometheus + Grafana (observability), và Apache Airflow (orchestration workflow).  
Mục tiêu là đảm bảo các công cụ này được triển khai nhất quán, bảo mật, và theo cách mà agent có thể tái tạo bất kỳ môi trường nào chỉ từ code.

---

## 2. Scope / Phạm vi

### EN
This document applies to:
- Docker image build and Dockerfile conventions (production-grade)
- Kubernetes deployment patterns (manifests, Helm, Operators)
- Terraform module conventions (structure, naming, state management)
- Prometheus and Grafana observability stack deployment
- Apache Airflow deployment on Kubernetes
- Integration patterns for the combined stack (how these tools wire together)

### VI
Tài liệu này áp dụng cho:
- Quy ước build Docker image và Dockerfile (cấp production)
- Các pattern triển khai Kubernetes (manifest, Helm, Operator)
- Quy ước module Terraform (cấu trúc, đặt tên, quản lý state)
- Triển khai Prometheus và Grafana observability stack
- Triển khai Apache Airflow trên Kubernetes
- Các pattern tích hợp cho bộ công cụ kết hợp (cách các công cụ kết nối với nhau)

---

## 3. Context declaration required / Bắt buộc khai báo context

### EN
Before generating or reviewing any configuration in this document, the agent must ask and the developer must declare:

- Is Docker used only for local development, or also for production image delivery?
- Is Kubernetes self-managed (kubeadm, k3s) or a managed service (EKS, GKE, AKS)?
- Is Terraform the IaC tool in use, or is another tool (Pulumi, Ansible) being used?
- Is Airflow deployed standalone (docker-compose) or on Kubernetes (KubernetesExecutor)?
- Is Prometheus deployed via Helm (kube-prometheus-stack), Operator, or standalone?

If any of these are not declared, the agent must not assume defaults. It must ask explicitly before generating configurations.

### VI
Trước khi generate hoặc review bất kỳ cấu hình nào trong tài liệu này, agent phải hỏi và developer phải khai báo:

- Docker được dùng chỉ cho local development, hay còn dùng cho production image delivery?
- Kubernetes là self-managed (kubeadm, k3s) hay managed service (EKS, GKE, AKS)?
- Terraform có phải là IaC tool đang sử dụng, hay đang dùng tool khác (Pulumi, Ansible)?
- Airflow được triển khai standalone (docker-compose) hay trên Kubernetes (KubernetesExecutor)?
- Prometheus được triển khai qua Helm (kube-prometheus-stack), Operator, hay standalone?

Nếu bất kỳ điều nào chưa được khai báo, agent không được tự giả định mặc định. Phải hỏi tường minh trước khi generate cấu hình.

---

## 4. Docker conventions (production-grade extensions) / Quy ước Docker (mở rộng cấp production)

> **Cross-reference / Tham chiếu chéo**: Các quy ước Docker cơ bản (multi-stage build, non-root user, `.dockerignore`, base image pinning, one Dockerfile per role, docker-compose) đã được định nghĩa đầy đủ trong `14-Infrastructure_deployment` §5-6. Section này **chỉ bổ sung** các quy ước production-grade chưa có ở file 14.

### 4.1 HEALTHCHECK must be defined in production Dockerfiles / HEALTHCHECK phải được định nghĩa trong Dockerfile production

#### EN
Every production Dockerfile must define a `HEALTHCHECK` instruction so that Docker and Kubernetes know the container's health state.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1
```

#### VI
Mọi Dockerfile production phải định nghĩa lệnh `HEALTHCHECK` để Docker và Kubernetes biết trạng thái health của container.

---

### 4.2 Image tagging must be deterministic / Tag image phải xác định được

#### EN
Images must be tagged with both a semantic version and a Git commit SHA.  
Never deploy an image tagged only as `latest` to staging or production.

```bash
# Correct: version + commit SHA
docker build -t myapp:1.4.2 -t myapp:1.4.2-abc1234 .

# Forbidden in production:
docker build -t myapp:latest .
```

#### VI
Image phải được tag với cả semantic version lẫn Git commit SHA.  
Không bao giờ deploy image chỉ được tag là `latest` lên staging hoặc production.

---

### 4.3 Image vulnerability scanning must run in CI / Scan lỗ hổng image phải chạy trong CI

#### EN
Every Docker image build in CI must be scanned for vulnerabilities before being pushed to the registry.  
Use `trivy` as the default scanner.

```yaml
# GitHub Actions example
- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:${{ github.sha }}
    format: table
    exit-code: 1              # fail CI on HIGH or CRITICAL vulnerabilities
    severity: HIGH,CRITICAL
```

#### VI
Mọi Docker image build trong CI phải được scan lỗ hổng trước khi push vào registry.  
Dùng `trivy` làm scanner mặc định.

---

## 5. Terraform conventions (advanced) / Quy ước Terraform (nâng cao)

> **Cross-reference / Tham chiếu chéo**: Các quy ước Terraform cơ bản (remote state, backend config, variables with description/type, sensitive outputs, plan before apply, module boundaries) đã được định nghĩa đầy đủ trong `14-Infrastructure_deployment` §7. Section này **chỉ bổ sung** các quy ước nâng cao chưa có ở file 14.

### 5.1 Module structure is standardized / Cấu trúc module được chuẩn hóa

#### EN
Every Terraform module — whether a root module or a reusable module — must follow this layout:

```
modules/
  <module-name>/
    main.tf           # primary resource definitions
    variables.tf      # all input variable declarations
    outputs.tf        # all output declarations
    versions.tf       # required_providers and terraform version constraints
    README.md         # usage examples, inputs, outputs (auto-generated by terraform-docs)
```

Root configuration (per environment):
```
infrastructure/terraform/
  environments/
    development.tfvars
    staging.tfvars
    production.tfvars
  main.tf             # calls modules
  variables.tf
  outputs.tf
  versions.tf
  backend.tf          # remote state backend configuration
```

#### VI
Mọi Terraform module — dù là root module hay reusable module — phải tuân theo layout sau:

```
modules/
  <module-name>/
    main.tf           # định nghĩa resource chính
    variables.tf      # khai báo tất cả input variable
    outputs.tf        # khai báo tất cả output
    versions.tf       # required_providers và ràng buộc phiên bản terraform
    README.md         # ví dụ sử dụng, inputs, outputs (auto-generate bởi terraform-docs)
```

---

### 5.2 Naming conventions for Terraform resources / Quy ước đặt tên resource Terraform

#### EN
All Terraform identifiers (resource names, variable names, output names, local names) must use `snake_case`.  
Do not repeat the resource type in the resource name.

```hcl
# Correct
resource "aws_s3_bucket" "model_artifacts" { ... }
variable "db_instance_class" { ... }
output "vpc_id" { ... }

# Forbidden — repeats resource type
resource "aws_s3_bucket" "aws_s3_bucket_model_artifacts" { ... }

# Forbidden — uses kebab-case or camelCase
variable "dbInstanceClass" { ... }
resource "aws_s3_bucket" "model-artifacts" { ... }
```

Output names must follow the pattern `{name}_{type}_{attribute}`:
```hcl
output "db_instance_endpoint" { ... }
output "vpc_main_id" { ... }
output "iam_role_arn" { ... }
```

#### VI
Mọi identifier Terraform (tên resource, biến, output, local) phải dùng `snake_case`.  
Không lặp lại loại resource trong tên resource.

---

### 5.3 Provider and module versions must be pinned / Phiên bản provider và module phải được pin

#### EN
All provider versions must be pinned with `~>` or exact constraints.  
The `.terraform.lock.hcl` file must be committed to version control.  
Terraform version must be pinned in `versions.tf`.

```hcl
# versions.tf
terraform {
  required_version = "~> 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}
```

#### VI
Mọi phiên bản provider phải được pin bằng `~>` hoặc ràng buộc chính xác.  
File `.terraform.lock.hcl` phải được commit vào version control.  
Phiên bản Terraform phải được pin trong `versions.tf`.

---

## 6. Kubernetes conventions (advanced) / Quy ước Kubernetes (nâng cao)

> **Note**: Basic Kubernetes conventions (resource limits, probes, secrets, namespaces, Helm) are defined in **document 14-Infrastructure-Deployment, Section 8**. This section covers advanced patterns specific to the Prometheus + Airflow + monitoring stack.

### 6.1 Namespace topology for the full stack / Topology namespace cho full stack

#### EN
The monitoring and orchestration stack must be deployed in dedicated namespaces, isolated from application workloads.

```
Namespace layout (minimum):
  production          → application workloads (API, workers, etc.)
  airflow             → Airflow webserver, scheduler, triggerer, workers
  monitoring          → Prometheus, Grafana, Alertmanager, exporters
  logging             → log aggregation stack (Loki, Fluentd, etc.)
  ingress             → ingress controllers
```

Namespaces must never be shared between environment tiers. Do not run `staging` airflow in the same namespace as `production` airflow.

#### VI
Monitoring và orchestration stack phải được deploy trong dedicated namespace, tách biệt khỏi application workload.

```
Layout namespace (tối thiểu):
  production          → application workload (API, worker, v.v.)
  airflow             → Airflow webserver, scheduler, triggerer, worker
  monitoring          → Prometheus, Grafana, Alertmanager, exporter
  logging             → log aggregation stack (Loki, Fluentd, v.v.)
  ingress             → ingress controller
```

Namespace không bao giờ được chia sẻ giữa các tier môi trường. Không chạy airflow `staging` trong cùng namespace với airflow `production`.

---

### 6.2 RBAC must be explicitly defined for all service accounts / RBAC phải được định nghĩa tường minh cho mọi service account

#### EN
Every pod that needs to call the Kubernetes API (Prometheus, Airflow KubernetesExecutor, etc.) must have an explicit `ServiceAccount`, `ClusterRole` or `Role`, and a `RoleBinding` or `ClusterRoleBinding`.  
Never use the `default` service account for workloads that need API access.

```yaml
# prometheus-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources: [nodes, nodes/proxy, services, endpoints, pods]
    verbs: [get, list, watch]
  - nonResourceURLs: ["/metrics"]
    verbs: [get]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
```

#### VI
Mọi pod cần gọi Kubernetes API (Prometheus, Airflow KubernetesExecutor, v.v.) phải có `ServiceAccount`, `ClusterRole` hoặc `Role`, và `RoleBinding` hoặc `ClusterRoleBinding` tường minh.  
Không bao giờ dùng service account `default` cho workload cần API access.

---

### 6.3 PodDisruptionBudget is required for critical workloads / PodDisruptionBudget bắt buộc cho workload quan trọng

#### EN
Stateful or always-available components (Prometheus, Airflow scheduler, database proxies) must have a `PodDisruptionBudget` to prevent all replicas from being evicted simultaneously during node maintenance.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: prometheus-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: prometheus
```

#### VI
Các thành phần stateful hoặc luôn cần available (Prometheus, Airflow scheduler, database proxy) phải có `PodDisruptionBudget` để tránh toàn bộ replica bị evict đồng thời khi bảo trì node.

---

### 6.4 ConfigMaps for tool configurations must be versioned / ConfigMap cho cấu hình tool phải được version hóa

#### EN
For tools like Prometheus (scrape configs, alert rules) and Airflow, configurations stored in ConfigMaps must be treated as versioned code.  
Use a label annotation with the config version or checksum so that pod restarts are triggered on change.

```yaml
metadata:
  name: prometheus-config
  namespace: monitoring
  annotations:
    # Checksum forces pod restart when config changes
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

#### VI
Với các công cụ như Prometheus (scrape config, alert rule) và Airflow, cấu hình lưu trong ConfigMap phải được đối xử như code được version hóa.  
Dùng label annotation với version hoặc checksum để trigger pod restart khi config thay đổi.

---

## 7. Prometheus conventions / Quy ước Prometheus

### 7.1 Deployment method selection / Chọn phương pháp triển khai

#### EN
Use the appropriate deployment method based on environment:

| Environment       | Recommended method                                      |
|-------------------|---------------------------------------------------------|
| Local development | `docker-compose` with `prom/prometheus` image           |
| Kubernetes (any)  | `kube-prometheus-stack` Helm chart (default)            |
| Kubernetes (custom control) | Prometheus Operator with manual CRDs         |
| Standalone VM     | Prometheus binary + systemd                             |

The `kube-prometheus-stack` Helm chart is the default because it bundles Prometheus, Alertmanager, Grafana, Node Exporter, kube-state-metrics, and sensible default rules in a single release.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi
```

#### VI
Dùng phương pháp triển khai phù hợp dựa trên môi trường:

| Môi trường         | Phương pháp đề xuất                                      |
|--------------------|----------------------------------------------------------|
| Local development  | `docker-compose` với image `prom/prometheus`             |
| Kubernetes (bất kỳ)| Helm chart `kube-prometheus-stack` (mặc định)            |
| Kubernetes (kiểm soát tùy chỉnh) | Prometheus Operator với CRD thủ công    |
| Standalone VM      | Prometheus binary + systemd                              |

Helm chart `kube-prometheus-stack` là mặc định vì nó bundle Prometheus, Alertmanager, Grafana, Node Exporter, kube-state-metrics, và các rule mặc định hợp lý trong một release.

---

### 7.2 ServiceMonitor is the required discovery pattern in Kubernetes / ServiceMonitor là pattern discovery bắt buộc trong Kubernetes

#### EN
When using the Prometheus Operator (via kube-prometheus-stack), never manually edit `prometheus.yml`.  
Instead, define `ServiceMonitor` resources to declare what services Prometheus should scrape.  
This keeps Prometheus configuration GitOps-compatible and declarative.

```yaml
# servicemonitor-api.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-service-monitor
  namespace: monitoring
  labels:
    release: prometheus    # must match Prometheus Operator's serviceMonitorSelector
spec:
  selector:
    matchLabels:
      app: api             # selects the target Service
  namespaceSelector:
    matchNames:
      - production
  endpoints:
    - port: http           # port name in the Service spec
      path: /metrics
      interval: 15s
```

#### VI
Khi dùng Prometheus Operator (qua kube-prometheus-stack), không bao giờ sửa thủ công `prometheus.yml`.  
Thay vào đó, định nghĩa `ServiceMonitor` resource để khai báo service nào Prometheus cần scrape.  
Điều này giữ cho cấu hình Prometheus tương thích với GitOps và declarative.

---

### 7.3 Metric naming conventions / Quy ước đặt tên metric

#### EN
Metrics exposed by application services must follow the Prometheus naming standard:

```
<namespace>_<subsystem>_<name>_<unit>
```

Rules:
- use lowercase with underscores, no hyphens
- include unit as suffix: `_seconds`, `_bytes`, `_total`, `_ratio`
- use `_total` suffix for counters (monotonically increasing values)
- avoid dynamic label values (user IDs, session IDs, request IDs) — these cause label cardinality explosion
- consistent label naming: always `environment`, `service`, `namespace`, not mixed with `env`, `svc`, `ns`

```python
# Correct metric names
http_request_duration_seconds     # histogram
http_requests_total               # counter
db_connections_active             # gauge
model_inference_latency_seconds   # histogram

# Forbidden
httpRequestDurationSecs           # camelCase
request-count                     # hyphens
http_requests_count_total_2       # redundant, unclear
```

#### VI
Metric được expose bởi application service phải tuân theo chuẩn đặt tên của Prometheus:

```
<namespace>_<subsystem>_<name>_<unit>
```

Quy tắc:
- dùng chữ thường với underscore, không dùng gạch nối
- thêm unit làm hậu tố: `_seconds`, `_bytes`, `_total`, `_ratio`
- dùng hậu tố `_total` cho counter (giá trị tăng đơn điệu)
- tránh giá trị label động (user ID, session ID, request ID) — gây label cardinality explosion
- đặt tên label nhất quán: luôn dùng `environment`, `service`, `namespace`, không trộn với `env`, `svc`, `ns`

---

### 7.4 Scrape interval must match signal volatility / Scrape interval phải phù hợp với mức độ thay đổi của tín hiệu

#### EN
Do not use a single scrape interval for all targets. Match the interval to how frequently the metric changes.

| Signal type                         | Recommended interval |
|-------------------------------------|----------------------|
| High-frequency (latency, error rate)| `15s`                |
| Standard application metrics        | `30s`                |
| Infrastructure (node, disk)         | `60s`                |
| Slow-changing (config, quota)       | `300s`               |

The global default should be `30s`. Override per-job only when necessary.

```yaml
# prometheus.yml or ServiceMonitor
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'api-high-frequency'
    scrape_interval: 15s    # override for latency-sensitive metrics
```

#### VI
Không dùng một scrape interval duy nhất cho mọi target. Điều chỉnh interval theo tần suất metric thay đổi.

---

### 7.5 Recording rules must pre-aggregate expensive queries / Recording rule phải pre-aggregate query tốn kém

#### EN
Any PromQL expression that is used repeatedly in dashboards or alerts, or that aggregates data across many time series, must be defined as a recording rule.  
This reduces query latency at read time and reduces Prometheus CPU load.

```yaml
# PrometheusRule CRD for recording rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-recording-rules
  namespace: monitoring
spec:
  groups:
    - name: api.rules
      interval: 30s
      rules:
        - record: job:http_request_duration_seconds:p99
          expr: histogram_quantile(0.99, sum by(job, le) (rate(http_request_duration_seconds_bucket[5m])))

        - record: job:http_requests_total:rate5m
          expr: sum by(job, status_code) (rate(http_requests_total[5m]))
```

#### VI
Bất kỳ biểu thức PromQL nào được dùng lặp lại trong dashboard hoặc alert, hoặc aggregate data qua nhiều time series, phải được định nghĩa là recording rule.  
Điều này giảm độ trễ query lúc đọc và giảm tải CPU của Prometheus.

---

### 7.6 Alerting rules must define severity and runbook / Alert rule phải định nghĩa severity và runbook

#### EN
Every alert rule must declare:
- `severity`: one of `critical`, `warning`, `info`
- `summary`: a one-line human-readable description
- `description`: a detailed message including affected service, metric value, and impact
- `runbook_url`: a link to the operational runbook for this alert

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alert-rules
  namespace: monitoring
spec:
  groups:
    - name: api.alerts
      rules:
        - alert: ApiHighErrorRate
          expr: job:http_requests_total:rate5m{status_code=~"5.."} / job:http_requests_total:rate5m > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "API error rate above 5% for {{ $labels.job }}"
            description: "Service {{ $labels.job }} has error rate of {{ $value | humanizePercentage }} for the last 5 minutes. This affects user-facing traffic."
            runbook_url: "https://wiki.internal/runbooks/api-high-error-rate"
```

#### VI
Mọi alert rule phải khai báo:
- `severity`: một trong `critical`, `warning`, `info`
- `summary`: mô tả ngắn gọn một dòng cho người đọc
- `description`: thông điệp chi tiết bao gồm service bị ảnh hưởng, giá trị metric, và tác động
- `runbook_url`: link tới runbook vận hành cho alert này

---

### 7.7 Prometheus must have persistent storage / Prometheus phải có persistent storage

#### EN
Prometheus local storage (TSDB) must be backed by a `PersistentVolumeClaim`.  
Never run Prometheus with ephemeral storage in production — all data is lost on pod restart.

Minimum recommended retention and storage:

| Environment    | Retention | PVC size |
|----------------|-----------|----------|
| Development    | 7d        | 10Gi     |
| Staging        | 15d       | 30Gi     |
| Production     | 30d       | 100Gi+   |

For long-term retention (>30d), use a remote write backend such as **Thanos**, **Cortex**, or **Grafana Mimir**.

```yaml
# Helm values for kube-prometheus-stack
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 100Gi
```

#### VI
Local storage (TSDB) của Prometheus phải được hỗ trợ bởi `PersistentVolumeClaim`.  
Không bao giờ chạy Prometheus với ephemeral storage trong production — toàn bộ data bị mất khi pod restart.

Với retention dài hạn (>30d), dùng remote write backend như **Thanos**, **Cortex**, hoặc **Grafana Mimir**.

---

### 7.8 High availability configuration / Cấu hình High Availability

#### EN
Production Prometheus must run with at least 2 replicas for high availability.  
Alertmanager must also run with at least 2 replicas and enable cluster peering.

```yaml
# Prometheus HA via kube-prometheus-stack Helm values
prometheus:
  prometheusSpec:
    replicas: 2
    # Each replica scrapes independently; Thanos or Alertmanager deduplicates

alertmanager:
  alertmanagerSpec:
    replicas: 2
```

When running 2+ Prometheus replicas scraping the same targets, use **Thanos Sidecar** or **Grafana Mimir** for deduplication and unified querying.

#### VI
Prometheus production phải chạy với ít nhất 2 replica cho high availability.  
Alertmanager cũng phải chạy với ít nhất 2 replica và bật cluster peering.

Khi chạy 2+ replica Prometheus scrape cùng target, dùng **Thanos Sidecar** hoặc **Grafana Mimir** để deduplicate và query thống nhất.

---

## 8. Apache Airflow on Kubernetes conventions / Quy ước Apache Airflow trên Kubernetes

### 8.1 Executor selection / Chọn Executor

#### EN
Use the official Apache Airflow Helm chart as the only supported installation method for Kubernetes.  
Executor must be chosen explicitly based on workload characteristics:

| Executor                  | When to use                                                       |
|---------------------------|-------------------------------------------------------------------|
| `KubernetesExecutor`      | Production default. Each task runs in an isolated pod. Best for tasks with variable resource needs, long-running tasks, and strict isolation. |
| `CeleryExecutor`          | Use when task latency is critical and startup overhead of pod creation is unacceptable. Requires Redis. |
| `CeleryKubernetesExecutor`| Hybrid: short tasks use Celery workers, heavy tasks use K8s pods. Use only when both conditions apply. |
| `LocalExecutor`           | Development and testing only. Never use in production.           |

#### VI
Dùng Helm chart chính thức của Apache Airflow là phương pháp cài đặt duy nhất được hỗ trợ trên Kubernetes.  
Executor phải được chọn tường minh dựa trên đặc điểm workload.

---

### 8.2 Installation via official Helm chart / Cài đặt qua Helm chart chính thức

#### EN

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Install with custom values
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow \
  --create-namespace \
  --values infrastructure/helm/airflow/values.yaml \
  --values infrastructure/helm/airflow/values-production.yaml
```

Airflow Helm chart values must be split into a base file and an environment-specific override file:
```
infrastructure/helm/airflow/
  values.yaml                # shared across all environments
  values-development.yaml    # development overrides
  values-staging.yaml        # staging overrides
  values-production.yaml     # production overrides
```

#### VI

Values của Airflow Helm chart phải được tách thành file base và file override theo môi trường.

---

### 8.3 DAGs must be synced via git-sync sidecar / DAG phải được sync qua git-sync sidecar

#### EN
Never use persistent volume mounts to manage DAG files in Kubernetes.  
Use the `git-sync` sidecar pattern so that DAGs are pulled from a Git repository.  
This enables full version control of DAGs, rollback capability, and eliminates manual file transfers.

```yaml
# airflow Helm values
dags:
  gitSync:
    enabled: true
    repo: git@github.com:my-org/my-dags-repo.git
    branch: main
    rev: HEAD
    depth: 1
    maxFailures: 3
    subPath: dags/                # folder inside the repo containing DAGs
    sshKeySecret: airflow-git-ssh-key
```

DAG changes are promoted through the same Git branching strategy as application code (PR review → merge → automatic sync).

#### VI
Không bao giờ dùng persistent volume mount để quản lý file DAG trong Kubernetes.  
Dùng pattern `git-sync` sidecar để DAG được pull từ Git repository.  
Điều này cho phép version control đầy đủ cho DAG, khả năng rollback, và loại bỏ việc chuyển file thủ công.

Thay đổi DAG được promote qua cùng Git branching strategy như application code (PR review → merge → tự động sync).

---

### 8.4 Airflow scheduler must run with 2 replicas / Airflow scheduler phải chạy với 2 replica

#### EN
Run 2 Airflow scheduler replicas to avoid a single point of failure.  
Airflow supports HA scheduling via leader election since version 2.x.  
If the active scheduler crashes, the standby takes over within seconds.

```yaml
# Helm values
scheduler:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2
      memory: 4Gi
```

#### VI
Chạy 2 replica Airflow scheduler để tránh single point of failure.  
Airflow hỗ trợ HA scheduling qua leader election từ phiên bản 2.x.  
Nếu scheduler đang hoạt động crash, scheduler dự phòng tiếp quản trong vài giây.

---

### 8.5 Airflow connections and variables must use Secrets Backend / Connections và variables Airflow phải dùng Secrets Backend

#### EN
Never store Airflow connections, variables, or passwords inside the Airflow metadata database or as Helm chart values in plaintext.  
Use a Secrets Backend (HashiCorp Vault, AWS Secrets Manager, or GCP Secret Manager) to inject sensitive Airflow configuration at runtime.

```yaml
# Helm values — use Vault as Secrets Backend
env:
  - name: AIRFLOW__SECRETS__BACKEND
    value: "airflow.providers.hashicorp.secrets.vault.VaultBackend"
  - name: AIRFLOW__SECRETS__BACKEND_KWARGS
    value: '{"connections_path": "airflow/connections", "variables_path": "airflow/variables", "url": "https://vault.internal:8200"}'
```

#### VI
Không bao giờ lưu Airflow connection, variable, hoặc password bên trong Airflow metadata database hoặc dưới dạng Helm chart values plaintext.  
Dùng Secrets Backend (HashiCorp Vault, AWS Secrets Manager, hoặc GCP Secret Manager) để inject cấu hình Airflow nhạy cảm lúc runtime.

---

### 8.6 KubernetesExecutor pod template must define resources / Pod template của KubernetesExecutor phải định nghĩa resources

#### EN
When using KubernetesExecutor, worker pods are ephemeral. Define a pod template file to standardize worker pod specifications.  
Every worker pod must have explicit `resources` with `requests` and `limits`.

```yaml
# worker pod template (pod_template_file.yaml)
apiVersion: v1
kind: Pod
metadata:
  name: airflow-worker
spec:
  serviceAccountName: airflow
  containers:
    - name: base          # must be named 'base' — required by Airflow
      image: apache/airflow:2.10.0
      resources:
        requests:
          cpu: 500m
          memory: 512Mi
        limits:
          cpu: 2
          memory: 4Gi
      env:
        - name: AIRFLOW__CORE__EXECUTOR
          value: KubernetesExecutor
```

Individual DAG tasks can override resources via `executor_config`:
```python
# In DAG definition — override worker pod resources per task
task = PythonOperator(
    task_id="heavy_transform",
    python_callable=run_transform,
    executor_config={
        "pod_override": k8s.V1Pod(
            spec=k8s.V1PodSpec(
                containers=[k8s.V1Container(
                    name="base",
                    resources=k8s.V1ResourceRequirements(
                        requests={"cpu": "2", "memory": "8Gi"},
                        limits={"cpu": "4", "memory": "16Gi"},
                    )
                )]
            )
        )
    }
)
```

#### VI
Khi dùng KubernetesExecutor, worker pod là ephemeral. Định nghĩa pod template file để chuẩn hóa thông số worker pod.  
Mọi worker pod phải có `resources` tường minh với `requests` và `limits`.

---

### 8.7 Airflow metrics must be exported to Prometheus / Metrics Airflow phải được export sang Prometheus

#### EN
Enable StatsD metric export in Airflow and use `statsd-exporter` as a bridge to Prometheus.

```yaml
# Helm values
env:
  - name: AIRFLOW__METRICS__STATSD_ON
    value: "True"
  - name: AIRFLOW__METRICS__STATSD_HOST
    value: "prometheus-statsd-exporter.monitoring.svc.cluster.local"
  - name: AIRFLOW__METRICS__STATSD_PORT
    value: "9125"
  - name: AIRFLOW__METRICS__STATSD_PREFIX
    value: "airflow"

# Deploy statsd-exporter in the monitoring namespace
# Then configure a ServiceMonitor to scrape it
```

Key Airflow metrics to alert on:
- `airflow_scheduler_heartbeat` — scheduler liveness
- `airflow_dag_processing_total_parse_time` — DAG parsing performance
- `airflow_task_instance_created_*` — task creation rate
- `airflow_executor_open_slots` — executor capacity headroom

#### VI
Bật StatsD metric export trong Airflow và dùng `statsd-exporter` làm cầu nối sang Prometheus.

Các metric Airflow quan trọng cần alert:
- `airflow_scheduler_heartbeat` — liveness của scheduler
- `airflow_dag_processing_total_parse_time` — hiệu năng parse DAG
- `airflow_task_instance_created_*` — tỷ lệ tạo task
- `airflow_executor_open_slots` — dung lượng còn lại của executor

---

## 9. Integration patterns: full stack wiring / Pattern tích hợp: kết nối full stack

### 9.1 Service topology / Topology service

#### EN
The following is the canonical service topology for a production deployment combining Docker, Kubernetes, Terraform, Prometheus, and Airflow:

```
┌──────────────────────────────────────────────────────────────────┐
│  Terraform (IaC layer)                                           │
│  Provisions: VPC, node groups, databases, storage, IAM           │
└───────────────────────────────┬──────────────────────────────────┘
                                │ creates
┌───────────────────────────────▼──────────────────────────────────┐
│  Kubernetes Cluster (orchestration layer)                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ ns: production  │  │   ns: airflow    │  │ ns: monitoring  │ │
│  │ API, workers    │  │ scheduler x2     │  │ Prometheus x2   │ │
│  │ (Docker images) │  │ webserver x2     │  │ Grafana         │ │
│  │                 │  │ triggerer x1     │  │ Alertmanager x2 │ │
│  │                 │  │ KubeExecutor     │  │ node-exporter   │ │
│  └────────┬────────┘  └───────┬──────────┘  └────────┬────────┘ │
│           │ /metrics          │ StatsD+exporter       │ scrapes  │
│           └───────────────────┴───────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

#### VI
Sau đây là topology service chuẩn cho triển khai production kết hợp Docker, Kubernetes, Terraform, Prometheus, và Airflow.

---

### 9.2 Deployment order / Thứ tự triển khai

#### EN
When deploying the full stack from scratch, follow this sequence to avoid dependency failures:

1. **Terraform**: provision cloud infrastructure (VPC, databases, node pools, storage buckets, IAM roles)
2. **Kubernetes base**: apply namespaces, RBAC, storage classes, and cluster-wide configurations
3. **Monitoring stack**: deploy `kube-prometheus-stack` (Prometheus must be up before applications that push/pull metrics)
4. **Airflow**: deploy via Helm chart, including metadata database migration
5. **Application workloads**: deploy API services and workers, with ServiceMonitors referencing Prometheus

Rolling updates follow this reverse order: application workloads → Airflow → monitoring → Kubernetes base → Terraform.

#### VI
Khi triển khai full stack từ đầu, theo thứ tự sau để tránh lỗi dependency:

1. **Terraform**: provision cloud infrastructure (VPC, database, node pool, storage bucket, IAM role)
2. **Kubernetes base**: apply namespace, RBAC, storage class, và cấu hình cluster-wide
3. **Monitoring stack**: deploy `kube-prometheus-stack` (Prometheus phải chạy trước các application expose metric)
4. **Airflow**: deploy qua Helm chart, bao gồm migration metadata database
5. **Application workload**: deploy API service và worker, với ServiceMonitor tham chiếu Prometheus

Rolling update theo thứ tự ngược: application workload → Airflow → monitoring → Kubernetes base → Terraform.

---

### 9.3 Secrets flow across the stack / Luồng secret trong toàn bộ stack

#### EN
Secrets must flow from a single source of truth into each layer:

```
Secret Manager (Vault / AWS Secrets Manager / GCP Secret Manager)
  │
  ├──► Terraform: reads secrets via data sources, never hard-codes
  │      terraform data "vault_generic_secret" "db_creds" { ... }
  │
  ├──► Kubernetes: External Secrets Operator syncs secrets from Vault into K8s Secrets
  │      ExternalSecret CR → creates K8s Secret → mounted into pods
  │
  ├──► Airflow: Secrets Backend reads directly from Vault at runtime
  │      AIRFLOW__SECRETS__BACKEND = VaultBackend
  │
  └──► Prometheus: credentials for scrape targets use K8s Secrets via SecretKeyRef
```

No secret may appear in:
- Terraform `.tf` files or `.tfvars` files in version control
- Kubernetes YAML manifests in version control
- Airflow Helm values files
- Prometheus configuration ConfigMaps

#### VI
Secret phải chảy từ một nguồn sự thật duy nhất vào từng layer.

Không có secret nào được xuất hiện trong:
- File `.tf` hoặc `.tfvars` Terraform trong version control
- Kubernetes YAML manifest trong version control
- File values Airflow Helm
- ConfigMap cấu hình Prometheus

---

### 9.4 Observability coverage requirements / Yêu cầu độ phủ observability

#### EN
Every service and component in the stack must expose metrics and be scraped by Prometheus. The following table defines minimum required coverage:

| Component                  | Metrics source             | Must have alert      |
|----------------------------|----------------------------|----------------------|
| API services               | `/metrics` endpoint        | error rate, latency  |
| Kubernetes nodes           | Node Exporter              | CPU, memory, disk    |
| Kubernetes pods            | cAdvisor / kube-state-metrics | OOMKill, restarts |
| PostgreSQL (Airflow DB)    | postgres-exporter          | connections, queries |
| Airflow scheduler          | statsd-exporter            | heartbeat, task fail |
| Prometheus itself          | self-scrape `/metrics`     | TSDB head bytes      |
| Alertmanager               | self-scrape `/metrics`     | alert routing errors |

A Grafana dashboard must exist for each row in the above table before a service is considered production-ready.

#### VI
Mọi service và component trong stack phải expose metric và được Prometheus scrape. Bảng dưới định nghĩa độ phủ tối thiểu bắt buộc.

Phải có Grafana dashboard cho mỗi dòng trong bảng trên trước khi một service được coi là sẵn sàng production.

---

## 10. Local development stack / Stack local development

### 10.1 docker-compose stack for local simulation / docker-compose stack để mô phỏng local

#### EN
For local development, all stack components must be runnable via `docker-compose`.  
The local stack must mirror production topology at reduced scale.  
Do not configure local development to depend on cloud resources that are not reproducible offline.

```yaml
# docker-compose.yml (abridged)
services:
  api:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile
      target: runtime
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: ${DATABASE_URL}
    depends_on: [postgres, prometheus]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # from .env, never hardcoded
    volumes: [postgres_data:/var/lib/postgresql/data]

  prometheus:
    image: prom/prometheus:v2.51.0   # pin version
    volumes:
      - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:10.4.0    # pin version
    ports: ["3000:3000"]
    volumes:
      - ./infrastructure/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro

  airflow-scheduler:
    image: apache/airflow:2.10.0
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor  # local uses LocalExecutor
    depends_on: [postgres]
    volumes: [./dags:/opt/airflow/dags]

volumes:
  postgres_data:
```

#### VI
Với local development, mọi component stack phải có thể chạy qua `docker-compose`.  
Stack local phải phản ánh topology production ở quy mô thu nhỏ.  
Không cấu hình local development phụ thuộc vào cloud resource không thể tái tạo offline.

---

### 10.2 Local prometheus.yml for static scrape config / prometheus.yml local cho static scrape config

#### EN
In local development (docker-compose), use a static `prometheus.yml` instead of ServiceMonitors (which require the Prometheus Operator).

```yaml
# infrastructure/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### VI
Trong local development (docker-compose), dùng `prometheus.yml` tĩnh thay vì ServiceMonitor (yêu cầu Prometheus Operator).

---

## 11. Grafana conventions / Quy ước Grafana

### 11.1 Dashboards must be provisioned as code / Dashboard phải được provision dưới dạng code

#### EN
Grafana dashboards must be defined as JSON files and provisioned via Grafana's provisioning mechanism or the Grafana Operator.  
Never create production dashboards manually through the Grafana UI — they will be lost on pod restart.

Dashboard files must be stored in version control under `infrastructure/grafana/dashboards/`.

```
infrastructure/grafana/
  dashboards/
    api-overview.json
    airflow-performance.json
    kubernetes-cluster.json
    data-pipeline-health.json
  provisioning/
    dashboards.yaml          # provisioning config
    datasources.yaml         # datasource config
```

#### VI
Grafana dashboard phải được định nghĩa dưới dạng file JSON và được provision qua cơ chế provisioning của Grafana hoặc Grafana Operator.  
Không bao giờ tạo production dashboard thủ công qua Grafana UI — chúng sẽ bị mất khi pod restart.

File dashboard phải được lưu trong version control dưới `infrastructure/grafana/dashboards/`.

---

### 11.2 Dashboard organization / Tổ chức dashboard

#### EN
Dashboards must be organized into folders that reflect system components:

| Folder         | Contents                                                |
|----------------|---------------------------------------------------------|
| `Application`  | API latency, error rates, throughput, business metrics  |
| `Kubernetes`   | Cluster health, node resources, pod status              |
| `Airflow`      | DAG runs, task durations, scheduler health              |
| `Data Pipeline`| Pipeline execution, data freshness, quality metrics     |
| `Infrastructure`| Database connections, storage, network                 |

Dashboard naming must follow the pattern: `<component>-<aspect>` (e.g., `api-latency`, `airflow-dag-performance`, `k8s-node-health`).

#### VI
Dashboard phải được tổ chức vào các folder phản ánh component hệ thống.

Đặt tên dashboard theo pattern: `<component>-<aspect>` (ví dụ: `api-latency`, `airflow-dag-performance`, `k8s-node-health`).

---

### 11.3 Datasource provisioning / Provision datasource

#### EN
Grafana datasources must be provisioned via YAML configuration, not manually created through the UI.

```yaml
# infrastructure/grafana/provisioning/datasources.yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-kube-prometheus-stack-prometheus.monitoring.svc:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki.logging.svc:3100
    editable: false
```

#### VI
Grafana datasource phải được provision qua cấu hình YAML, không tạo thủ công qua UI.

---

### 11.4 Dashboard variables must be consistent / Biến dashboard phải nhất quán

#### EN
All dashboards must use standardized template variables for filtering:

- `$namespace` — Kubernetes namespace
- `$environment` — deployment environment
- `$service` — service name
- `$interval` — scrape interval (auto or explicit)

Labels used in dashboard queries must match exactly the label names defined in `§7.3 Metric naming conventions`.

#### VI
Mọi dashboard phải dùng template variable chuẩn hóa để lọc.

Label dùng trong dashboard query phải khớp chính xác với tên label được định nghĩa trong `§7.3 Quy ước đặt tên metric`.

---

### 11.5 Grafana access and authentication / Truy cập và xác thực Grafana

#### EN
Grafana must not be publicly accessible without authentication.  
In Kubernetes, expose Grafana through an Ingress with one of the following authentication methods:

- OAuth2 Proxy (recommended) with SSO (Google, GitHub, OIDC)
- Basic auth behind TLS (minimum for staging)
- Grafana built-in LDAP/SAML integration

Never expose Grafana on a public endpoint with only the default `admin/admin` credentials.

#### VI
Grafana không được truy cập công khai mà không có xác thực.  
Trong Kubernetes, expose Grafana qua Ingress với một trong các phương thức xác thực được liệt kê.

Không bao giờ expose Grafana trên endpoint công khai chỉ với credential mặc định `admin/admin`.

---

## 12. Log aggregation conventions / Quy ước thu thập log tập trung

> **Cross-reference / Tham chiếu chéo**: Các quy ước log ở application level (format, level, structured logging, sensitive data) được định nghĩa trong `06-Logging_observability_convention` §4-5. Section này quy ước việc **thu thập, lưu trữ, và truy vấn** log ở infrastructure level.

### 12.1 Centralized log collection is required for production / Thu thập log tập trung là bắt buộc cho production

#### EN
Production systems must not rely on `kubectl logs` or `docker logs` as the primary log access method.  
A centralized log aggregation stack must be deployed to collect, store, and query logs from all services and components.

Recommended stacks:

| Stack          | Components                           | When to use                        |
|----------------|--------------------------------------|------------------------------------|
| Loki stack     | Promtail + Loki + Grafana           | Default for K8s; lightweight, integrates with Grafana |
| ELK/EFK stack  | Fluentd + Elasticsearch + Kibana    | When full-text search is critical  |

#### VI
Hệ thống production không được dựa vào `kubectl logs` hoặc `docker logs` làm phương thức truy cập log chính.  
Phải deploy stack thu thập log tập trung để thu thập, lưu trữ, và truy vấn log từ mọi service và component.

---

### 12.2 Log collection must use DaemonSet pattern in Kubernetes / Thu thập log phải dùng pattern DaemonSet trong Kubernetes

#### EN
Deploy the log collector (Promtail, Fluentd, or Fluent Bit) as a `DaemonSet` so that every node has a log forwarder.  
The collector must:
- read from `/var/log/pods/` or `/var/log/containers/`
- enrich logs with Kubernetes metadata (pod name, namespace, container name, labels)
- forward to the centralized log store

```yaml
# Helm install Promtail (for Loki stack)
helm install promtail grafana/promtail \
  --namespace logging \
  --create-namespace \
  --set config.lokiAddress=http://loki.logging.svc:3100/loki/api/v1/push
```

#### VI
Deploy log collector (Promtail, Fluentd, hoặc Fluent Bit) dưới dạng `DaemonSet` để mỗi node đều có log forwarder.  
Collector phải enrich log với Kubernetes metadata (pod name, namespace, container name, label).

---

### 12.3 Log retention must be defined and enforced / Retention log phải được định nghĩa và bắt buộc

#### EN

| Environment    | Retention | Storage    |
|----------------|-----------|------------|
| Development    | 3d        | 5Gi        |
| Staging        | 7d        | 20Gi       |
| Production     | 30d       | 100Gi+     |

For compliance or audit requirements exceeding 30 days, archive logs to object storage (S3/GCS) with lifecycle policies.

#### VI

| Môi trường     | Retention | Storage    |
|----------------|-----------|------------|
| Development    | 3d        | 5Gi        |
| Staging        | 7d        | 20Gi       |
| Production     | 30d       | 100Gi+     |

Với yêu cầu compliance hoặc audit vượt quá 30 ngày, lưu trữ log vào object storage (S3/GCS) với lifecycle policy.

---

### 12.4 Sensitive data must not appear in aggregated logs / Dữ liệu nhạy cảm không được xuất hiện trong log tập trung

#### EN
The log collection pipeline must not capture or forward sensitive data.  
Follow `06-Logging_observability` §4.6 and `08-Security_secrets_conventions` §7 for data redaction rules.

If the log collector supports field-level filtering (Fluentd plugins, Promtail pipeline stages), sensitive fields must be dropped or redacted before forwarding to the store.

#### VI
Pipeline thu thập log không được capture hoặc forward dữ liệu nhạy cảm.  
Tuân theo `06-Logging_observability` §4.6 và `08-Security_secrets_conventions` §7 cho quy tắc redaction dữ liệu.

---

## 13. Checklist: agent must verify before applying configurations / Checklist: agent phải xác minh trước khi áp dụng cấu hình

### EN
Before generating or applying any configuration in this document, the agent must verify all applicable checklists below.  
Items marked with **(→14)** reference rules owned by `14-Infrastructure_deployment`. Items marked with **(→06)** reference `06-Logging_observability`. Items marked with **(→08)** reference `08-Security_secrets_conventions`.

**Docker checklist**
- [ ] Dockerfile uses multi-stage build **(→14 §5.2)**
- [ ] Final stage derives from slim/distroless base image **(→14 §5.3)**
- [ ] No `latest` tag used for any base image **(→14 §5.3)**
- [ ] `USER` is set to non-root before `CMD`/`ENTRYPOINT` **(→14 §5.4)**
- [ ] `.dockerignore` exists and excludes `.env`, `.git`, `tests/` **(→14 §5.5)**
- [ ] `HEALTHCHECK` is defined **(§4.1)**
- [ ] Image tag includes semantic version and Git SHA **(§4.2)**
- [ ] Image scanned for vulnerabilities in CI **(§4.3)**

**Terraform checklist**
- [ ] `backend.tf` configures remote state with locking **(→14 §7.2)**
- [ ] `.terraform.lock.hcl` is committed **(§5.3)**
- [ ] All variables have `description` and `type` **(→14 §7.5)**
- [ ] Sensitive outputs use `sensitive = true` **(→14 §7.7)**
- [ ] No credentials appear in `.tf` or `.tfvars` files **(→14 §7.7, →08)**
- [ ] Module names use `snake_case` **(§5.2)**
- [ ] Provider versions are pinned with `~>` **(§5.3)**
- [ ] `terraform plan` reviewed before any `apply` **(→14 §7.8)**

**Kubernetes checklist**
- [ ] All containers have `resources.requests` and `resources.limits` **(→14 §8.2)**
- [ ] Liveness and readiness probes are defined **(→14 §8.4)**
- [ ] No secrets appear in ConfigMaps **(→14 §8.3)**
- [ ] Components are in dedicated namespaces (not `default`) **(§6.1, →14 §8.5)**
- [ ] Explicit RBAC is defined for service accounts that call the API **(§6.2)**
- [ ] PodDisruptionBudget is defined for critical components **(§6.3)**
- [ ] ConfigMaps use checksum annotations for config-driven restarts **(§6.4)**

**Prometheus checklist**
- [ ] Prometheus runs with `PersistentVolumeClaim` backing **(§7.7)**
- [ ] Prometheus runs with ≥2 replicas in production **(§7.8)**
- [ ] Discovery uses `ServiceMonitor` (not manual `prometheus.yml` in K8s) **(§7.2)**
- [ ] All alert rules have `severity`, `summary`, `description`, `runbook_url` **(§7.6)**
- [ ] Recording rules defined for any repeated complex PromQL **(§7.5)**
- [ ] Metric names use correct naming convention with units **(§7.3)**
- [ ] Scrape intervals match signal volatility **(§7.4)**

**Grafana checklist**
- [ ] Dashboards are provisioned as code (JSON), not created manually **(§11.1)**
- [ ] Dashboards organized into folders by component **(§11.2)**
- [ ] Datasources provisioned via YAML **(§11.3)**
- [ ] Template variables are standardized (`$namespace`, `$environment`, `$service`) **(§11.4)**
- [ ] Grafana is not publicly accessible without authentication **(§11.5)**

**Log aggregation checklist**
- [ ] Centralized log collection is deployed (Loki or ELK) **(§12.1)**
- [ ] Log collector runs as DaemonSet in K8s **(§12.2)**
- [ ] Log retention policies are defined per environment **(§12.3)**
- [ ] Sensitive data is not forwarded to log store **(§12.4, →06 §4.6)**

**Airflow checklist**
- [ ] Installed via official Apache Airflow Helm chart **(§8.2)**
- [ ] Executor is explicitly declared (not defaulted) **(§8.1)**
- [ ] DAGs sync via `git-sync` sidecar (not volume mount) **(§8.3)**
- [ ] Scheduler runs with ≥2 replicas in production **(§8.4)**
- [ ] Secrets use Secrets Backend, not Helm values **(§8.5)**
- [ ] Worker pod template defines explicit resource requests/limits **(§8.6)**
- [ ] StatsD metrics exported to Prometheus via statsd-exporter **(§8.7)**

**Secrets flow checklist**
- [ ] Secrets originate from a single source (Vault / AWS SM / GCP SM) **(§9.3, →08)**
- [ ] No secret appears in `.tf`, `.tfvars`, Helm values, ConfigMaps, or YAML manifests **(§9.3)**
- [ ] External Secrets Operator or equivalent syncs secrets into K8s **(§9.3)**

### VI
Trước khi generate hoặc apply bất kỳ cấu hình nào trong tài liệu này, agent phải xác minh tất cả checklist áp dụng ở trên.  
Các mục đánh dấu **(→14)** tham chiếu tới `14-Infrastructure_deployment`. Các mục **(→06)** tham chiếu `06-Logging_observability`. Các mục **(→08)** tham chiếu `08-Security_secrets_conventions`.

---

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- manually editing `prometheus.yml` in Kubernetes instead of using ServiceMonitor CRDs
- running Prometheus without persistent storage in production
- running single-replica Prometheus, Alertmanager, or Airflow scheduler in production
- storing Airflow connections or variables in the metadata database in plaintext
- managing DAGs via persistent volume mounts in Kubernetes instead of `git-sync`
- using `latest` tag for any image in the monitoring/orchestration stack
- not defining `PodDisruptionBudget` for stateful or always-available components
- hardcoding scrape targets instead of using service discovery (ServiceMonitor)
- using dynamic, unbounded label values (user IDs, request IDs) in Prometheus metrics — causes cardinality explosion
- not exporting Airflow metrics to Prometheus
- creating Grafana dashboards manually through the UI for production environments
- exposing Grafana or Prometheus publicly without authentication
- relying on `kubectl logs` or `docker logs` as the only log access method in production
- ignoring log retention policies, leading to unbounded storage growth
- mixing monitoring and application workloads in the same Kubernetes namespace
- deploying Terraform changes without reviewing `terraform plan` output
- not defining alert severity levels or missing runbook URLs in alert rules

### VI
Tránh:

- sửa thủ công `prometheus.yml` trong Kubernetes thay vì dùng ServiceMonitor CRD
- chạy Prometheus mà không có persistent storage trong production
- chạy single-replica Prometheus, Alertmanager, hoặc Airflow scheduler trong production
- lưu Airflow connection hoặc variable trong metadata database dạng plaintext
- quản lý DAG qua persistent volume mount trong Kubernetes thay vì `git-sync`
- dùng tag `latest` cho bất kỳ image nào trong monitoring/orchestration stack
- không định nghĩa `PodDisruptionBudget` cho component stateful hoặc luôn phải available
- hardcode scrape target thay vì dùng service discovery (ServiceMonitor)
- dùng giá trị label động, không giới hạn (user ID, request ID) trong Prometheus metric — gây cardinality explosion
- không export Airflow metric sang Prometheus
- tạo Grafana dashboard thủ công qua UI cho production
- expose Grafana hoặc Prometheus ra public mà không có xác thực
- chỉ dựa vào `kubectl logs` hoặc `docker logs` làm phương thức truy cập log duy nhất trong production
- bỏ qua log retention policy, dẫn đến storage tăng không giới hạn
- trộn monitoring và application workload trong cùng Kubernetes namespace
- deploy thay đổi Terraform mà không review `terraform plan` output
- không định nghĩa alert severity hoặc thiếu runbook URL trong alert rule

---

## 15. References / Tham khảo

### EN
These conventions are derived from and consistent with:

- [Prometheus Best Practices — cloudraft.io](https://www.cloudraft.io/blog/prometheus-best-practices)
- [Prometheus Kubernetes Guide — plural.sh](https://www.plural.sh/blog/prometheus-kubernetes-monitoring-guide/)
- [kube-prometheus-stack Helm Chart — prometheus-community](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Terraform Naming Conventions — terraform-best-practices.com](https://www.terraform-best-practices.com/naming)
- [Terraform Standard Module Structure — HashiCorp](https://developer.hashicorp.com/terraform/language/modules/develop/structure)
- [AWS Terraform Provider Best Practices — AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/structure.html)
- [Airflow Helm Chart — airflow.apache.org](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [Airflow KubernetesExecutor — airflow.apache.org](https://airflow.apache.org/docs/apache-airflow/stable/executor/kubernetes.html)
- [Production-Ready Airflow on Kubernetes (Airflow 3.0) — medium.com/@valerykretinin](https://medium.com/@valerykretinin/a-production-ready-apache-airflow-v3-0-on-kubernetes-61d0e4924de7)
- [Docker Build Best Practices — docs.docker.com](https://docs.docker.com/build/building/best-practices/)
- [Dockerfile Security Best Practices — sysdig.com](https://www.sysdig.com/learn-cloud-native/dockerfile-best-practices)
- [High Availability in Prometheus — last9.io](https://last9.io/blog/high-availability-in-prometheus/)
- [Grafana Provisioning — grafana.com](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Loki Architecture — grafana.com](https://grafana.com/docs/loki/latest/get-started/overview/)

### VI
Các quy ước này được derived từ và nhất quán với các tài liệu tham khảo được liệt kê ở trên.

---

## 16. Versioning / Phiên bản

| Phiên bản | Ngày | Thay đổi |
|-----------|------|----------|
| v1.0 | 2026-03-30 | Tạo file ban đầu: Docker production-grade, Terraform advanced, K8s advanced, Prometheus, Airflow on K8s, integration patterns, local dev stack |
| v1.1 | 2026-03-30 | Rút gọn Docker/Terraform trùng lặp → cross-reference tới file 14. Bổ sung §11 Grafana conventions, §12 Log aggregation. Cải thiện §13 Checklist với cross-ref annotations. Thêm §14 Anti-patterns, §16 Versioning, §17 DoD |

---

## 17. Definition of Done / Điều kiện hoàn thành

### EN
An observability or orchestration infrastructure change is considered done only if:

- context has been declared (§3): Docker usage, K8s type, IaC tool, Airflow deployment, Prometheus deployment
- all applicable checklists in §13 have been verified and passed
- Docker conventions from both `14-Infrastructure_deployment` §5-6 and this document §4 are satisfied
- Terraform conventions from both `14-Infrastructure_deployment` §7 and this document §5 are satisfied
- Kubernetes basic rules (→14 §8) and advanced rules (this document §6) are satisfied
- Prometheus is deployed with persistent storage, HA replicas, and ServiceMonitor discovery
- Grafana dashboards are provisioned as code with proper authentication
- Log aggregation is deployed with defined retention policies
- Airflow is deployed via official Helm chart with git-sync, Secrets Backend, and HA scheduler
- all secrets flow from a single source of truth (§9.3) and do not appear in any tracked file
- the change satisfies the general definition of done in `11-Definition_of_done`

### VI
Một thay đổi infrastructure liên quan đến observability hoặc orchestration chỉ được coi là done khi:

- context đã được khai báo (§3): cách dùng Docker, loại K8s, IaC tool, cách deploy Airflow, cách deploy Prometheus
- tất cả checklist áp dụng trong §13 đã được xác minh và pass
- quy ước Docker từ cả `14-Infrastructure_deployment` §5-6 và file này §4 được thỏa mãn
- quy ước Terraform từ cả `14-Infrastructure_deployment` §7 và file này §5 được thỏa mãn
- quy tắc Kubernetes cơ bản (→14 §8) và nâng cao (file này §6) được thỏa mãn
- Prometheus được deploy với persistent storage, HA replica, và ServiceMonitor discovery
- Grafana dashboard được provision dưới dạng code với xác thực phù hợp
- Log aggregation được deploy với retention policy đã định nghĩa
- Airflow được deploy qua Helm chart chính thức với git-sync, Secrets Backend, và HA scheduler
- mọi secret chảy từ một nguồn sự thật duy nhất (§9.3) và không xuất hiện trong file tracked nào
- thay đổi thỏa mãn definition of done chung trong `11-Definition_of_done`

