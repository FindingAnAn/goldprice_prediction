# 14-Infrastructure-Deployment / Quy ước Infrastructure và Deployment

## 1. Purpose / Mục đích

### EN
This document defines the conventions for infrastructure code, containerization, local development runtime, cloud provisioning, container orchestration, and CI/CD pipelines.
Its purpose is to ensure that infrastructure is treated as code, that environments are consistent and reproducible, that secrets are never embedded in infrastructure definitions, and that deployment is safe, auditable, and reversible.

### VI
Tài liệu này định nghĩa các quy ước cho infrastructure code, container hóa, local development runtime, cloud provisioning, container orchestration, và CI/CD pipeline.
Mục tiêu là đảm bảo infrastructure được đối xử như code, môi trường nhất quán và tái tạo được, secret không bao giờ được nhúng vào định nghĩa infrastructure, và deployment an toàn, có thể kiểm toán, và có thể đảo ngược.

> [!TIP]
> **Tùy chọn tham khảo code mẫu tại:** [Example/docker_compose_example.txt](Example/docker_compose_example.txt)

---

## 2. Scope / Phạm vi

### EN
This document applies to:

- Dockerfile and image build conventions
- docker-compose conventions for local development
- Infrastructure as Code conventions (Terraform and non-Terraform paths)
- Kubernetes and manifest conventions
- CI/CD pipeline conventions (GitHub Actions and GitLab CI)
- environment separation and promotion strategy
- secret injection into infrastructure
- health check and readiness requirements
- rollback and recovery expectations

### VI
Tài liệu này áp dụng cho:

- quy ước Dockerfile và image build
- quy ước docker-compose cho local development
- quy ước Infrastructure as Code (cả Terraform và không dùng Terraform)
- quy ước Kubernetes và manifest
- quy ước CI/CD pipeline (GitHub Actions và GitLab CI)
- chiến lược tách môi trường và promotion
- secret injection vào infrastructure
- yêu cầu về health check và readiness
- kỳ vọng về rollback và recovery

---

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Infrastructure is code / Infrastructure là code

#### EN
Every infrastructure definition must be treated as source code.
It must be version-controlled, reviewed, tested where possible, and subject to the same quality discipline as application code.
No infrastructure change may be applied manually to a shared environment without a corresponding code change that is reviewed and traceable.

#### VI
Mọi định nghĩa infrastructure phải được đối xử như source code.
Nó phải được version control, review, test khi có thể, và chịu cùng kỷ luật chất lượng như application code.
Không có thay đổi infrastructure nào được áp dụng thủ công lên môi trường dùng chung mà không có thay đổi code tương ứng được review và truy vết được.

---

### 3.2 Environments must be consistent and reproducible / Môi trường phải nhất quán và tái tạo được

#### EN
Local, staging, and production environments must share the same topology.
A developer must be able to run the full system stack locally.
The difference between environments must be limited to configuration values, not structural differences in how services are wired together.

#### VI
Môi trường local, staging, và production phải có cùng topology.
Developer phải có thể chạy full stack hệ thống trên máy local.
Sự khác biệt giữa các môi trường phải giới hạn ở giá trị cấu hình, không phải sự khác biệt về cấu trúc cách các service được kết nối.

---

### 3.3 Secrets must never live in infrastructure definitions / Secret không bao giờ được nằm trong định nghĩa infrastructure

#### EN
No secret, credential, token, or sensitive value may be hard-coded in any Dockerfile, docker-compose file, Terraform file, Kubernetes manifest, or CI/CD pipeline definition.
This rule has no exceptions.
All secrets must be injected at runtime from approved secret sources.

#### VI
Không có secret, credential, token, hoặc giá trị nhạy cảm nào được hard-code trong bất kỳ Dockerfile, docker-compose file, Terraform file, Kubernetes manifest, hoặc CI/CD pipeline definition.
Quy tắc này không có ngoại lệ.
Mọi secret phải được inject lúc runtime từ nguồn secret được phê duyệt.

---

### 3.4 Deployment must be safe, auditable, and reversible / Deployment phải an toàn, có thể kiểm toán, và đảo ngược được

#### EN
Every deployment must produce a traceable record of what changed, who triggered it, and when.
Every deployment must have a defined rollback path before it is executed.
Irreversible operations must require explicit confirmation and documentation.

#### VI
Mọi deployment phải tạo ra bản ghi truy vết được về thứ gì thay đổi, ai kích hoạt, và khi nào.
Mọi deployment phải có đường rollback được định nghĩa rõ trước khi thực thi.
Các thao tác không đảo ngược phải yêu cầu xác nhận tường minh và tài liệu hóa.

---

### 3.5 Agent and developer must declare context before applying conventions / Agent và developer phải khai báo context trước khi áp dụng quy ước

#### EN
This document covers multiple infrastructure paths.
Before generating, reviewing, or modifying infrastructure code, the agent must ask and the developer must declare:

- Is this project using docker-compose only for local runtime, or also for production deployment?
- Is this project using Terraform or another IaC tool, or managing infrastructure manually or through a platform?
- Is this project using Kubernetes for orchestration, or deploying directly to VMs, managed services, or a PaaS?
- Is CI/CD using GitHub Actions, GitLab CI, or another platform?

If context is not declared, the agent must not assume defaults and must ask explicitly.

#### VI
Tài liệu này bao phủ nhiều đường infrastructure khác nhau.
Trước khi generate, review, hoặc sửa infrastructure code, agent phải hỏi và developer phải khai báo:

- Dự án này dùng docker-compose chỉ cho local runtime, hay còn dùng cho production deployment?
- Dự án này dùng Terraform hoặc IaC tool khác, hay quản lý infrastructure thủ công hoặc qua platform?
- Dự án này dùng Kubernetes để orchestration, hay deploy thẳng lên VM, managed service, hoặc PaaS?
- CI/CD đang dùng GitHub Actions, GitLab CI, hay platform khác?

Nếu context chưa được khai báo, agent không được tự giả định mặc định và phải hỏi tường minh.

---

## 4. Infrastructure folder structure / Cấu trúc thư mục infrastructure

### 4.1 Standard layout / Layout chuẩn

#### EN
The `infrastructure/` directory must be organized by tool and concern, not by environment.
Environment differences belong in configuration values, not in separate folder trees.

```
infrastructure/
  docker/
    Dockerfile                  # primary application image
    Dockerfile.{service}        # per-service images when needed
    .dockerignore
  terraform/                    # present only if using Terraform
    main.tf
    variables.tf
    outputs.tf
    backend.tf
    modules/
      networking/
      compute/
      storage/
    environments/
      development.tfvars
      staging.tfvars
      production.tfvars
  kubernetes/                   # present only if using Kubernetes
    manifests/
      namespace.yaml
      deployment.yaml
      service.yaml
      configmap.yaml
      ingress.yaml
    helm/
      {chart-name}/
  scripts/
    setup/
    deployment/
    rollback/
docker-compose.yml              # base stack definition
docker-compose.override.yml     # local-only overrides
```

#### VI
Thư mục `infrastructure/` phải được tổ chức theo tool và concern, không phải theo môi trường.
Sự khác biệt giữa môi trường thuộc về giá trị cấu hình, không phải cây thư mục riêng biệt.

---

### 4.2 What belongs in infrastructure versus src / Phân biệt infrastructure và src

#### EN
`infrastructure/` contains definitions for how the system is packaged, deployed, and operated.
`src/` contains application code.

Forbidden in `infrastructure/`:
- business logic
- data processing code
- model training code
- application configuration that belongs in `config/`

Forbidden in `src/`:
- Dockerfile definitions
- deployment manifests
- cloud resource definitions
- CI/CD pipeline definitions

#### VI
`infrastructure/` chứa định nghĩa về cách hệ thống được đóng gói, deploy, và vận hành.
`src/` chứa application code.

Bị cấm trong `infrastructure/`:
- business logic
- code xử lý data
- code training model
- cấu hình application thuộc về `config/`

Bị cấm trong `src/`:
- định nghĩa Dockerfile
- deployment manifest
- định nghĩa cloud resource
- định nghĩa CI/CD pipeline

---

## 5. Dockerfile conventions / Quy ước Dockerfile

> **Cross-reference / Tham chiếu chéo**: Các quy ước Docker production-grade bổ sung (HEALTHCHECK trong Dockerfile, image tagging với semver+SHA, vulnerability scanning trong CI) được định nghĩa trong `18-Observability_orchestration_conventions` §4.

### 5.1 A Dockerfile has one job: package the runtime environment / Dockerfile có một việc: đóng gói runtime environment

#### EN
A Dockerfile must define the environment in which the application runs.
It must not contain:

- business logic execution at build time
- data downloads or model downloads at build time
- training runs at build time
- secrets or credentials of any kind
- hard-coded environment-specific values

Build-time operations must be limited to installing dependencies, copying source code, and setting up the runtime entrypoint.

#### VI
Dockerfile phải định nghĩa môi trường mà application chạy trong đó.
Nó không được chứa:

- thực thi business logic lúc build
- tải data hoặc model lúc build
- chạy training lúc build
- secret hoặc credential dưới bất kỳ hình thức nào
- giá trị đặc thù môi trường được hard-code

Các thao tác lúc build phải giới hạn ở cài đặt dependencies, copy source code, và thiết lập runtime entrypoint.

---

### 5.2 Use multi-stage builds for production images / Dùng multi-stage build cho production image

#### EN
Production images must use multi-stage builds to separate the build environment from the runtime environment.
The final image stage must contain only what is needed to run the application, not build tools, test dependencies, or intermediate artifacts.

```dockerfile
# Stage 1: build dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
COPY config/ ./config/
ENV PATH=/root/.local/bin:$PATH
ENTRYPOINT ["python", "-m", "src.main"]
```

#### VI
Production image phải dùng multi-stage build để tách môi trường build khỏi môi trường runtime.
Stage cuối cùng của image chỉ được chứa những gì cần thiết để chạy application, không phải build tool, test dependency, hoặc artifact trung gian.

---

### 5.3 Base image must be explicit and pinned / Base image phải tường minh và được ghim version

#### EN
Never use `latest` as a base image tag.
Always pin to a specific version that has been reviewed and tested.

Preferred:
- `python:3.11.9-slim`
- `python:3.11-slim-bookworm`

Avoid:
- `python:latest`
- `python:3`
- `python:3.11` without a patch version when stability is critical

Update base images intentionally through a reviewed change, not automatically.

#### VI
Không bao giờ dùng `latest` làm tag cho base image.
Luôn ghim vào một version cụ thể đã được review và test.

Ưu tiên:
- `python:3.11.9-slim`
- `python:3.11-slim-bookworm`

Tránh:
- `python:latest`
- `python:3`
- `python:3.11` không có patch version khi tính ổn định quan trọng

Cập nhật base image có chủ đích thông qua thay đổi được review, không tự động.

---

### 5.4 Images must run as non-root by default / Image phải chạy dưới non-root theo mặc định

#### EN
Production images must not run as root.
Create a dedicated non-root user and switch to it before the final entrypoint.

```dockerfile
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --no-create-home appuser
USER appuser
```

#### VI
Production image không được chạy dưới quyền root.
Tạo user non-root riêng và chuyển sang user đó trước entrypoint cuối cùng.

---

### 5.5 .dockerignore is mandatory / .dockerignore là bắt buộc

#### EN
Every Dockerfile must have a corresponding `.dockerignore` file.
It must exclude at minimum:

- `.git/`
- `.env` and `*.env`
- `__pycache__/` and `*.pyc`
- `tests/`
- `notebooks/`
- `artifacts/`
- `data/`
- `models/`
- local development overrides

#### VI
Mọi Dockerfile phải có file `.dockerignore` tương ứng.
File này phải loại trừ tối thiểu:

- `.git/`
- `.env` và `*.env`
- `__pycache__/` và `*.pyc`
- `tests/`
- `notebooks/`
- `artifacts/`
- `data/`
- `models/`
- local development override

---

### 5.6 One Dockerfile per service role / Một Dockerfile cho mỗi service role

#### EN
When a project has multiple service roles such as an API server, a training job, and a scheduler, each role should have its own Dockerfile.
Name Dockerfiles clearly by role: `Dockerfile.api`, `Dockerfile.training`, `Dockerfile.scheduler`.
Avoid a single giant Dockerfile that tries to serve all roles through environment variable switching.

#### VI
Khi dự án có nhiều service role như API server, training job, và scheduler, mỗi role nên có Dockerfile riêng.
Đặt tên Dockerfile rõ theo role: `Dockerfile.api`, `Dockerfile.training`, `Dockerfile.scheduler`.
Tránh một Dockerfile khổng lồ cố phục vụ mọi role thông qua environment variable switching.

---

## 6. docker-compose conventions / Quy ước docker-compose

### 6.1 Context declaration required / Bắt buộc khai báo context

#### EN
Before writing or reviewing docker-compose files, declare:

- Is docker-compose used for local development only, or also for production deployment?

If **local development only**: apply all rules in this section without exception.
If **production deployment via docker-compose**: also apply section 6.8 (production constraints).

#### VI
Trước khi viết hoặc review docker-compose file, phải khai báo:

- docker-compose được dùng chỉ cho local development, hay còn cho production deployment?

Nếu **chỉ local development**: áp dụng mọi quy tắc trong section này không có ngoại lệ.
Nếu **production deployment qua docker-compose**: cũng áp dụng section 6.8 (production constraints).

---

### 6.2 Base and override file separation / Tách file base và override

#### EN
The project must use the standard docker-compose override pattern:

- `docker-compose.yml` — base service definitions shared across all contexts
- `docker-compose.override.yml` — local development overrides, automatically applied by docker-compose

The base file must not contain:
- volume mounts pointing to local source code
- debug-mode flags
- development-only services
- port mappings that would conflict in production

The override file contains what is needed to make local development convenient: source mounts, debug flags, relaxed resource limits.

#### VI
Dự án phải dùng pattern override chuẩn của docker-compose:

- `docker-compose.yml` — định nghĩa service base dùng chung cho mọi context
- `docker-compose.override.yml` — override cho local development, được docker-compose tự động áp dụng

File base không được chứa:
- volume mount trỏ vào source code local
- debug-mode flag
- service chỉ dùng cho development
- port mapping sẽ xung đột trong production

File override chứa những thứ giúp local development tiện lợi: source mount, debug flag, resource limit nới lỏng.

---

### 6.3 Local stack must mirror production topology / Stack local phải phản ánh topology production

#### EN
The local docker-compose stack must include all services that exist in production.
A developer must be able to run the full system locally without connecting to any external shared environment.

If production has: API + Postgres + Redis + Airflow + MLflow + Prometheus + Grafana,
then local must have the same services, even if scaled down.

Running locally and seeing "works here" must be meaningful, not accidental.

#### VI
Stack docker-compose local phải bao gồm tất cả service tồn tại trong production.
Developer phải có thể chạy full hệ thống local mà không cần kết nối đến môi trường dùng chung bên ngoài nào.

Nếu production có: API + Postgres + Redis + Airflow + MLflow + Prometheus + Grafana,
thì local cũng phải có cùng các service đó, dù ở scale nhỏ hơn.

"Chạy được local" phải có ý nghĩa thực sự, không phải ngẫu nhiên.

---

### 6.4 Every service must have a health check / Mọi service phải có health check

#### EN
Every service in docker-compose must define a `healthcheck` block.
Services that depend on other services must use `condition: service_healthy`, not just the service name.

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

Health checks must test actual service readiness, not just process liveness.

#### VI
Mọi service trong docker-compose phải định nghĩa block `healthcheck`.
Service phụ thuộc vào service khác phải dùng `condition: service_healthy`, không chỉ tên service.

Health check phải kiểm tra readiness thực sự của service, không chỉ là process còn sống.

---

### 6.5 Secrets must come from environment variables or .env file / Secret phải đến từ environment variable hoặc .env file

#### EN
Secrets must never be hard-coded in docker-compose files.
Use `${VARIABLE_NAME}` syntax to reference environment variables.
Provide an `.env.example` file with placeholder values, never with real secrets.
The real `.env` file must be in `.gitignore`.

```yaml
# Correct
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

# Forbidden
environment:
  POSTGRES_PASSWORD: mysecretpassword
```

#### VI
Secret không bao giờ được hard-code trong docker-compose file.
Dùng cú pháp `${VARIABLE_NAME}` để tham chiếu environment variable.
Cung cấp file `.env.example` với placeholder value, không bao giờ với secret thật.
File `.env` thật phải nằm trong `.gitignore`.

---

### 6.6 Use named volumes, not anonymous volumes / Dùng named volume, không dùng anonymous volume

#### EN
Always declare volumes explicitly with names in the top-level `volumes:` block.
Anonymous volumes are hard to inspect, back up, and clean up intentionally.

```yaml
# Correct
volumes:
  postgres_data:

services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data

# Avoid
services:
  postgres:
    volumes:
      - /var/lib/postgresql/data
```

#### VI
Luôn khai báo volume tường minh với tên trong block `volumes:` cấp cao nhất.
Anonymous volume khó inspect, backup, và dọn sạch có chủ đích.

---

### 6.7 Use a shared network with a meaningful name / Dùng network dùng chung với tên có ý nghĩa

#### EN
Define a single named network for the project and attach all services to it.
Network name should reflect the project name for clarity when running multiple projects locally.

```yaml
networks:
  project-name-network:
    driver: bridge
```

#### VI
Định nghĩa một named network duy nhất cho dự án và gắn mọi service vào đó.
Tên network phải phản ánh tên dự án để rõ ràng khi chạy nhiều dự án local cùng lúc.

---

### 6.8 Production deployment via docker-compose: additional constraints / Deploy production qua docker-compose: ràng buộc bổ sung

#### EN
If docker-compose is used for production deployment, the following additional rules apply:

- resource limits (`deploy.resources.limits`) must be defined for every service
- restart policy must be `unless-stopped` or `always`, never `no`
- log driver and log rotation must be configured explicitly
- no source code volume mounts may exist in the production compose file
- image tags must be pinned to a specific version, never `latest`
- a separate `docker-compose.prod.yml` must be maintained and explicitly referenced in deployment commands

#### VI
Nếu docker-compose được dùng cho production deployment, các quy tắc bổ sung sau áp dụng:

- resource limit (`deploy.resources.limits`) phải được định nghĩa cho mọi service
- restart policy phải là `unless-stopped` hoặc `always`, không bao giờ là `no`
- log driver và log rotation phải được cấu hình tường minh
- không có source code volume mount nào trong production compose file
- image tag phải được ghim vào version cụ thể, không bao giờ là `latest`
- một file `docker-compose.prod.yml` riêng phải được duy trì và tham chiếu tường minh trong deployment command

---

## 7. Infrastructure as Code conventions / Quy ước Infrastructure as Code

> **Cross-reference / Tham chiếu chéo**: Các quy ước Terraform nâng cao (module structure chi tiết, naming conventions cho resource, provider/module version pinning) được định nghĩa trong `18-Observability_orchestration_conventions` §5.

### 7.1 Context declaration required / Bắt buộc khai báo context

#### EN
Before writing or reviewing infrastructure provisioning code, declare:

- Is this project using Terraform, Pulumi, or another IaC tool?
- Or is infrastructure managed manually, through a cloud console, or through a PaaS platform?

If **using Terraform**: apply section 7.2 through 7.8.
If **not using IaC**: apply section 7.9 (manual and PaaS path).

#### VI
Trước khi viết hoặc review infrastructure provisioning code, phải khai báo:

- Dự án này dùng Terraform, Pulumi, hoặc IaC tool khác?
- Hay infrastructure được quản lý thủ công, qua cloud console, hoặc qua PaaS platform?

Nếu **dùng Terraform**: áp dụng section 7.2 đến 7.8.
Nếu **không dùng IaC**: áp dụng section 7.9 (đường manual và PaaS).

---

### 7.2 Terraform state must be stored remotely / Terraform state phải được lưu remote

#### EN
`terraform.tfstate` must never be committed to version control.
State must be stored in a remote backend with encryption and locking enabled.

Recommended backends:
- S3 with DynamoDB locking and server-side encryption
- Terraform Cloud
- GCS with locking

Add `*.tfstate` and `*.tfstate.backup` to `.gitignore` at project initialization.

**Critical warning**: Terraform state files may contain secrets in plaintext, including database passwords, API keys, and private keys generated by Terraform. A committed state file is a secret leak.

#### VI
`terraform.tfstate` không bao giờ được commit vào version control.
State phải được lưu trong remote backend với encryption và locking được bật.

Backend khuyến nghị:
- S3 với DynamoDB locking và server-side encryption
- Terraform Cloud
- GCS với locking

Thêm `*.tfstate` và `*.tfstate.backup` vào `.gitignore` khi khởi tạo dự án.

**Cảnh báo quan trọng**: File Terraform state có thể chứa secret dưới dạng plaintext, bao gồm database password, API key, và private key được Terraform generate. File state bị commit là một lần rò rỉ secret.

---

### 7.3 Backend configuration must be explicit / Cấu hình backend phải tường minh

#### EN
Define the remote backend in a dedicated `backend.tf` file.

```hcl
terraform {
  backend "s3" {
    bucket         = "my-project-tfstate"
    key            = "production/terraform.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    dynamodb_table = "my-project-tfstate-lock"
  }
}
```

Never use the default local backend for any environment that is shared or production-bound.

#### VI
Định nghĩa remote backend trong file `backend.tf` riêng.

Không bao giờ dùng local backend mặc định cho bất kỳ môi trường nào dùng chung hoặc hướng production.

---

### 7.4 Variables must be separated from logic / Variable phải tách khỏi logic

#### EN
Terraform files must follow this separation:

- `main.tf` — resource definitions
- `variables.tf` — variable declarations with types and descriptions
- `outputs.tf` — output declarations
- `backend.tf` — backend configuration
- `environments/{env}.tfvars` — environment-specific values

No hard-coded values may appear in `main.tf` that should vary between environments.

#### VI
Terraform file phải theo sự tách biệt sau:

- `main.tf` — định nghĩa resource
- `variables.tf` — khai báo variable với type và description
- `outputs.tf` — khai báo output
- `backend.tf` — cấu hình backend
- `environments/{env}.tfvars` — giá trị đặc thù theo môi trường

Không được có giá trị hard-coded trong `main.tf` mà đáng ra phải thay đổi giữa các môi trường.

---

### 7.5 Every variable must have a description / Mọi variable phải có description

#### EN
Every input variable in `variables.tf` must have:
- a `type` declaration
- a `description` that explains what the variable controls

```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the training job runner. Use t3.medium for dev, c5.2xlarge for production."
}
```

Variables without descriptions make infrastructure reviews impossible to do meaningfully.

#### VI
Mọi input variable trong `variables.tf` phải có:
- khai báo `type`
- `description` giải thích variable đó kiểm soát cái gì

Variable không có description làm cho việc review infrastructure trở nên không thể thực hiện có ý nghĩa.

---

### 7.6 Modules must have clear boundaries / Module phải có ranh giới rõ ràng

#### EN
Group related resources into modules with a single clear responsibility.

Preferred module boundaries:
- `networking/` — VPC, subnets, security groups, DNS
- `compute/` — EC2, ECS, GKE node pools, container instances
- `storage/` — S3, GCS, RDS, databases, object stores

Do not create modules that span unrelated concerns.
Do not create a single flat `main.tf` with all resources when the infrastructure has more than a few components.

#### VI
Nhóm các resource liên quan vào module với một trách nhiệm rõ ràng.

Ranh giới module ưu tiên:
- `networking/` — VPC, subnet, security group, DNS
- `compute/` — EC2, ECS, GKE node pool, container instance
- `storage/` — S3, GCS, RDS, database, object store

Không tạo module trải dài qua các concern không liên quan.
Không tạo một `main.tf` phẳng khổng lồ với mọi resource khi infrastructure có nhiều hơn vài thành phần.

---

### 7.7 Sensitive outputs must be marked / Output nhạy cảm phải được đánh dấu

#### EN
Any Terraform output that contains a sensitive value such as a database endpoint, connection string, or generated password must be marked `sensitive = true`.

```hcl
output "database_password" {
  value     = random_password.db.result
  sensitive = true
}
```

This prevents the value from being printed in plan and apply output.

#### VI
Mọi Terraform output chứa giá trị nhạy cảm như database endpoint, connection string, hoặc password được generate phải được đánh dấu `sensitive = true`.

Điều này ngăn giá trị bị in ra trong plan và apply output.

---

### 7.8 Always run plan before apply / Luôn chạy plan trước apply

#### EN
No `terraform apply` may be executed without a prior `terraform plan` that has been reviewed.
For production environments, the plan output must be reviewed and approved before apply is triggered.
In CI/CD pipelines, plan and apply must be separate jobs with explicit approval between them for production.

#### VI
Không có `terraform apply` nào được thực thi mà không có `terraform plan` trước đó đã được review.
Với môi trường production, output của plan phải được review và phê duyệt trước khi apply được kích hoạt.
Trong CI/CD pipeline, plan và apply phải là job riêng biệt với approval tường minh ở giữa cho production.

---

### 7.9 Non-IaC path: manual and PaaS infrastructure rules / Đường không dùng IaC: quy tắc infrastructure thủ công và PaaS

#### EN
If the project does not use an IaC tool, the following rules apply:

- every infrastructure component must be documented in `docs/architecture/` with its configuration, purpose, and access requirements
- changes to shared infrastructure must go through a reviewed change request, not silent manual edits
- credentials and connection strings for all environments must be stored in an approved secret manager, never in documents or spreadsheets
- the production environment configuration must be reproducible from documentation alone: if the environment had to be rebuilt from scratch, the documentation must be sufficient to do so

#### VI
Nếu dự án không dùng IaC tool, các quy tắc sau áp dụng:

- mọi thành phần infrastructure phải được tài liệu hóa trong `docs/architecture/` với cấu hình, mục đích, và yêu cầu truy cập
- thay đổi infrastructure dùng chung phải đi qua change request được review, không được sửa thủ công âm thầm
- credential và connection string cho mọi môi trường phải được lưu trong secret manager được phê duyệt, không bao giờ trong document hoặc spreadsheet
- cấu hình production phải có thể tái tạo chỉ từ tài liệu: nếu môi trường phải xây lại từ đầu, tài liệu phải đủ để làm điều đó

---

## 8. Kubernetes conventions / Quy ước Kubernetes

> **Cross-reference / Tham chiếu chéo**: Các quy ước Kubernetes nâng cao (RBAC, PodDisruptionBudget, namespace topology cho monitoring stack, ConfigMap versioning) được định nghĩa trong `18-Observability_orchestration_conventions` §6.

### 8.1 Context declaration required / Bắt buộc khai báo context

#### EN
Before writing or reviewing Kubernetes manifests, declare:

- Is this project deploying to Kubernetes or a managed Kubernetes service (EKS, GKE, AKS)?
- Or is it deploying to VMs, a managed container service (ECS, Cloud Run), or a PaaS?

If **not using Kubernetes**: skip this section entirely.
If **using Kubernetes**: apply all rules in this section.

#### VI
Trước khi viết hoặc review Kubernetes manifest, phải khai báo:

- Dự án này deploy lên Kubernetes hoặc managed Kubernetes service (EKS, GKE, AKS)?
- Hay deploy lên VM, managed container service (ECS, Cloud Run), hoặc PaaS?

Nếu **không dùng Kubernetes**: bỏ qua section này hoàn toàn.
Nếu **dùng Kubernetes**: áp dụng mọi quy tắc trong section này.

---

### 8.2 Every manifest must declare resource limits / Mọi manifest phải khai báo resource limit

#### EN
Every container spec must define both `requests` and `limits` for CPU and memory.
Missing resource limits cause unstable scheduling and can starve other workloads.

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "2Gi"
```

#### VI
Mọi container spec phải định nghĩa cả `requests` và `limits` cho CPU và memory.
Thiếu resource limit gây lập lịch không ổn định và có thể làm chết đói các workload khác.

---

### 8.3 Secrets must use Kubernetes Secrets or an external secret operator / Secret phải dùng Kubernetes Secrets hoặc external secret operator

#### EN
Sensitive values must never appear in ConfigMaps or manifest files.
Use Kubernetes Secrets, or preferably an external secret operator that syncs from a secret manager such as AWS Secrets Manager or HashiCorp Vault.

Never store Kubernetes Secret manifests with real values in version control.
If Secret manifests must be committed, they must contain only placeholder values or be encrypted with a tool like Sealed Secrets or SOPS.

#### VI
Giá trị nhạy cảm không bao giờ được xuất hiện trong ConfigMap hoặc manifest file.
Dùng Kubernetes Secrets, hoặc tốt hơn là external secret operator sync từ secret manager như AWS Secrets Manager hoặc HashiCorp Vault.

Không bao giờ lưu Kubernetes Secret manifest với giá trị thật vào version control.
Nếu Secret manifest phải được commit, chúng chỉ được chứa placeholder value hoặc phải được mã hóa bằng tool như Sealed Secrets hoặc SOPS.

---

### 8.4 Liveness and readiness probes are mandatory / Liveness và readiness probe là bắt buộc

#### EN
Every Deployment must define both a liveness probe and a readiness probe.

- liveness probe: determines if the container process is alive and should be restarted if not
- readiness probe: determines if the container is ready to receive traffic

They must test different conditions and must not be identical copies of each other.

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

#### VI
Mọi Deployment phải định nghĩa cả liveness probe và readiness probe.

- liveness probe: xác định process container còn sống và có nên restart không
- readiness probe: xác định container đã sẵn sàng nhận traffic chưa

Chúng phải kiểm tra điều kiện khác nhau và không được là bản copy giống hệt nhau.

---

### 8.5 Namespaces must separate environments and concerns / Namespace phải tách môi trường và concern

#### EN
Use namespaces to separate:
- environments: `development`, `staging`, `production`
- system concerns from application concerns: `monitoring`, `logging`, `ingress`

Do not deploy everything into the `default` namespace.

#### VI
Dùng namespace để tách:
- môi trường: `development`, `staging`, `production`
- system concern khỏi application concern: `monitoring`, `logging`, `ingress`

Không deploy mọi thứ vào namespace `default`.

---

### 8.6 Use Helm for parameterized deployments / Dùng Helm cho parameterized deployment

#### EN
When a service must be deployed across multiple environments with different configurations, use a Helm chart to parameterize the manifests.
Raw manifests are acceptable for simple, single-environment deployments or infrastructure components that do not change between environments.

Helm chart values files must follow the same environment separation pattern as Terraform: one values file per environment.

#### VI
Khi một service phải được deploy trên nhiều môi trường với cấu hình khác nhau, dùng Helm chart để parameterize manifest.
Raw manifest chấp nhận được cho deployment đơn giản, một môi trường, hoặc infrastructure component không thay đổi giữa các môi trường.

File values của Helm chart phải tuân theo cùng pattern tách môi trường như Terraform: một values file cho mỗi môi trường.

---

## 9. Environment separation conventions / Quy ước tách môi trường

### 9.1 Three environments are the minimum standard / Ba môi trường là tiêu chuẩn tối thiểu

#### EN
Every project that is production-bound must have at minimum:

- `development` or `local`: developer-controlled, no shared state, safe to break
- `staging`: mirrors production topology and data shape, used for integration validation
- `production`: serves real traffic, protected, requires formal change process

The structural difference between staging and production must be limited to scale and resource size, never to missing services or different connection topology.

#### VI
Mọi dự án hướng production phải có tối thiểu:

- `development` hoặc `local`: developer kiểm soát, không có shared state, an toàn để phá
- `staging`: phản ánh topology production và data shape, dùng để validate integration
- `production`: phục vụ traffic thật, được bảo vệ, yêu cầu quy trình thay đổi chính thức

Sự khác biệt về cấu trúc giữa staging và production phải giới hạn ở scale và resource size, không bao giờ là thiếu service hoặc topology kết nối khác nhau.

---

### 9.2 Environment promotion must be explicit / Promotion giữa môi trường phải tường minh

#### EN
A change must pass through environments in sequence: development → staging → production.
Skipping staging for non-emergency changes is forbidden.
Each promotion step must be triggered explicitly, not automatically, for production.

#### VI
Một thay đổi phải đi qua các môi trường theo thứ tự: development → staging → production.
Bỏ qua staging cho các thay đổi không khẩn cấp là bị cấm.
Mỗi bước promotion phải được kích hoạt tường minh, không tự động, cho production.

---

### 9.3 Environment-specific configuration must not change code behavior structurally / Cấu hình theo môi trường không được thay đổi hành vi code về mặt cấu trúc

#### EN
The same container image must be deployable to any environment.
Environment differences must be expressed only through configuration values injected at runtime.
It is forbidden to build different images for different environments.

#### VI
Cùng một container image phải deploy được lên bất kỳ môi trường nào.
Sự khác biệt môi trường chỉ được biểu đạt qua giá trị cấu hình được inject lúc runtime.
Bị cấm build image khác nhau cho môi trường khác nhau.

---

## 10. CI/CD pipeline conventions / Quy ước CI/CD pipeline

### 10.1 Context declaration required / Bắt buộc khai báo context

#### EN
Before writing or reviewing CI/CD pipeline definitions, declare:

- Is this project using GitHub Actions, GitLab CI, or another CI/CD platform?

The structural conventions in this section apply to all platforms.
Platform-specific syntax examples are provided for GitHub Actions and GitLab CI.
For other platforms, apply the structural intent and adapt the syntax.

#### VI
Trước khi viết hoặc review CI/CD pipeline definition, phải khai báo:

- Dự án này dùng GitHub Actions, GitLab CI, hay CI/CD platform khác?

Các quy ước về cấu trúc trong section này áp dụng cho mọi platform.
Ví dụ cú pháp đặc thù platform được cung cấp cho GitHub Actions và GitLab CI.
Với platform khác, áp dụng ý đồ cấu trúc và điều chỉnh cú pháp cho phù hợp.

---

### 10.2 Pipeline structure: CI and CD are separate concerns / Cấu trúc pipeline: CI và CD là concern tách biệt

#### EN
CI (Continuous Integration) and CD (Continuous Delivery/Deployment) must be separate pipeline definitions or clearly separated stages.

CI pipeline responsibilities:
- run on every push and pull request
- lint, format check, type check
- run unit tests
- run integration tests if applicable
- build and validate the container image
- must complete in a reasonable time (target under 10 minutes for unit tests)

CD pipeline responsibilities:
- triggered on merge to main or on explicit release tag
- deploy to staging automatically after CI passes
- deploy to production only after explicit approval
- produce a deployment record with version, timestamp, and approver

#### VI
CI (Continuous Integration) và CD (Continuous Delivery/Deployment) phải là pipeline definition riêng biệt hoặc stage được tách rõ.

Trách nhiệm của CI pipeline:
- chạy mỗi lần push và pull request
- lint, format check, type check
- chạy unit test
- chạy integration test nếu có
- build và validate container image
- phải hoàn thành trong thời gian hợp lý (mục tiêu dưới 10 phút cho unit test)

Trách nhiệm của CD pipeline:
- được kích hoạt khi merge vào main hoặc trên release tag tường minh
- deploy lên staging tự động sau khi CI pass
- chỉ deploy lên production sau khi có approval tường minh
- tạo deployment record với version, timestamp, và người phê duyệt

---

### 10.3 Secrets in CI/CD must use platform secret stores / Secret trong CI/CD phải dùng platform secret store

#### EN
All secrets used in pipeline jobs must be stored in the CI/CD platform's secret or variable store.
They must be referenced by name in the pipeline definition, never hard-coded.

**GitHub Actions:**
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}
```

**GitLab CI:**
```yaml
variables:
  DATABASE_URL: $DATABASE_URL   # set in GitLab CI/CD Variables
  API_KEY: $API_KEY
```

Secret values must never appear in pipeline logs.
If a secret is accidentally printed, it must be treated as a rotation event immediately.

#### VI
Mọi secret được dùng trong pipeline job phải được lưu trong secret store hoặc variable store của CI/CD platform.
Chúng phải được tham chiếu bằng tên trong pipeline definition, không bao giờ hard-code.

Giá trị secret không bao giờ được xuất hiện trong pipeline log.
Nếu secret vô tình bị in ra, nó phải được xem là sự kiện rotation ngay lập tức.

---

### 10.4 Pipeline jobs must be scoped and named clearly / Pipeline job phải có phạm vi rõ và tên rõ

#### EN
Each job in a pipeline must:
- have a name that describes its purpose
- have a clearly defined scope: one job, one responsibility
- produce clear pass/fail output
- not combine unrelated checks in a single job

Avoid a single `test` job that runs linting, unit tests, integration tests, and security scans all together.
Split them into separately named jobs so failures are immediately identifiable.

#### VI
Mỗi job trong pipeline phải:
- có tên mô tả mục đích
- có phạm vi được định nghĩa rõ: một job, một trách nhiệm
- tạo ra output pass/fail rõ ràng
- không gộp các check không liên quan vào một job duy nhất

Tránh một job `test` duy nhất chạy linting, unit test, integration test, và security scan tất cả cùng nhau.
Tách thành job được đặt tên riêng để failure có thể nhận diện ngay lập tức.

---

### 10.5 Artifact caching must be intentional / Cache artifact phải có chủ đích

#### EN
Dependency caches must use cache keys that include the dependency file hash so the cache is invalidated when dependencies change.

**GitHub Actions:**
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**GitLab CI:**
```yaml
cache:
  key:
    files:
      - requirements.txt
  paths:
    - .pip-cache/
```

Never use a static cache key that does not reflect dependency content.

#### VI
Cache dependency phải dùng cache key bao gồm hash của file dependency để cache bị invalidate khi dependency thay đổi.

Không bao giờ dùng static cache key không phản ánh nội dung dependency.

---

### 10.6 Production deployment requires explicit approval / Deployment production yêu cầu approval tường minh

#### EN
No automated process may deploy to production without a human approval step.

**GitHub Actions:** use environment protection rules with required reviewers.
**GitLab CI:** use `when: manual` for the production deploy job.

The approval step must be logged with the identity of the approver and the timestamp.

#### VI
Không có quy trình tự động nào được deploy lên production mà không có bước human approval.

**GitHub Actions:** dùng environment protection rule với required reviewer.
**GitLab CI:** dùng `when: manual` cho production deploy job.

Bước approval phải được log với danh tính của người phê duyệt và timestamp.

---

### 10.7 Every deployment must produce a traceable record / Mỗi deployment phải tạo ra bản ghi truy vết được

#### EN
After a successful deployment, the pipeline must record:
- image tag or artifact version deployed
- target environment
- deployment timestamp
- pipeline run ID or commit SHA
- approver identity (for production)

This record must be stored durably, not just in ephemeral pipeline logs.

#### VI
Sau deployment thành công, pipeline phải ghi lại:
- image tag hoặc artifact version được deploy
- môi trường đích
- timestamp deployment
- pipeline run ID hoặc commit SHA
- danh tính người phê duyệt (cho production)

Bản ghi này phải được lưu trữ bền vững, không chỉ trong ephemeral pipeline log.

---

### 10.8 Pipeline definitions must be reviewed like code / Định nghĩa pipeline phải được review như code

#### EN
Changes to `.github/workflows/`, `.gitlab-ci.yml`, or equivalent pipeline definitions must go through the same pull request and review process as application code.
Pipeline changes must not be merged without review.
This is especially important because pipeline files have access to secrets and deployment permissions.

#### VI
Thay đổi với `.github/workflows/`, `.gitlab-ci.yml`, hoặc pipeline definition tương đương phải đi qua cùng quy trình pull request và review như application code.
Thay đổi pipeline không được merge mà không có review.
Điều này đặc biệt quan trọng vì file pipeline có quyền truy cập secret và quyền deployment.

---

## 11. Health check and readiness conventions / Quy ước health check và readiness

### 11.1 Every deployable service must expose health endpoints / Mọi service có thể deploy phải expose health endpoint

#### EN
Every service must expose at minimum:
- `/health/live` or `/healthz` — liveness: the process is running
- `/health/ready` or `/readyz` — readiness: the service is ready to accept traffic

These endpoints must respond without requiring authentication.
They must not trigger side effects such as logging a request or updating a database.
They must be lightweight and respond within a few hundred milliseconds.

#### VI
Mọi service phải expose tối thiểu:
- `/health/live` hoặc `/healthz` — liveness: process đang chạy
- `/health/ready` hoặc `/readyz` — readiness: service sẵn sàng nhận traffic

Các endpoint này phải phản hồi mà không yêu cầu authentication.
Chúng không được trigger side effect như log request hoặc update database.
Chúng phải nhẹ và phản hồi trong vài trăm millisecond.

---

### 11.2 Readiness must reflect real dependency health / Readiness phải phản ánh sức khỏe dependency thực sự

#### EN
The readiness endpoint must reflect whether the service can actually serve requests, including the health of its critical dependencies.
If the service cannot reach the database or a critical external dependency, it must return not-ready.

Readiness must not simply return 200 because the process started.

#### VI
Endpoint readiness phải phản ánh liệu service có thực sự có thể phục vụ request không, bao gồm sức khỏe của các dependency quan trọng.
Nếu service không đến được database hoặc dependency ngoài quan trọng, nó phải trả về not-ready.

Readiness không được đơn giản trả về 200 chỉ vì process đã start.

---

## 12. Rollback conventions / Quy ước rollback

### 12.1 Every deployment must have a rollback plan / Mọi deployment phải có kế hoạch rollback

#### EN
Before executing a deployment, the following must be defined:
- what is the rollback target (previous image tag, previous Terraform state, previous manifest version)?
- who has the authority to trigger a rollback?
- what is the expected rollback execution time?

A deployment must not be approved if the rollback path is undefined.

#### VI
Trước khi thực thi một deployment, những điều sau phải được định nghĩa:
- rollback target là gì (image tag trước, Terraform state trước, manifest version trước)?
- ai có quyền kích hoạt rollback?
- thời gian thực thi rollback dự kiến là bao lâu?

Deployment không được phê duyệt nếu đường rollback chưa được định nghĩa.

---

### 12.2 Rollback scripts must be tested / Script rollback phải được test

#### EN
Rollback scripts in `infrastructure/scripts/rollback/` must be tested in staging before they are needed in production.
An untested rollback script is as dangerous as no rollback script.

#### VI
Script rollback trong `infrastructure/scripts/rollback/` phải được test trên staging trước khi cần dùng trong production.
Script rollback chưa được test nguy hiểm như không có script rollback.

---

### 12.3 Database migrations require special rollback consideration / Database migration yêu cầu cân nhắc rollback đặc biệt

#### EN
Schema changes and data migrations may not be reversible without data loss.
For any migration that is destructive or irreversible:
- a backup must be taken before applying
- the migration must be staged: add column before removing old column, not remove and add in one step
- the deployment plan must account for the case where rollback requires the old column to still exist

#### VI
Schema change và data migration có thể không đảo ngược được mà không mất data.
Với migration nào mang tính phá hủy hoặc không đảo ngược:
- phải backup trước khi áp dụng
- migration phải được chia nhỏ: thêm cột trước khi xóa cột cũ, không xóa và thêm trong một bước
- kế hoạch deployment phải tính đến trường hợp rollback yêu cầu cột cũ vẫn phải còn

---

## 13. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- hard-coding any secret, credential, or environment-specific value in Dockerfile, docker-compose, Terraform, Kubernetes manifests, or CI/CD pipeline files
- using `latest` as a Docker image tag in any environment
- committing `terraform.tfstate` or `.tfstate.backup` to version control
- running containers as root in production
- deploying to production without a prior staging validation
- deploying to production without explicit human approval
- merging pipeline definition changes without review
- building different images for different environments instead of using runtime configuration
- using the same credentials across development, staging, and production
- writing health checks that always return 200 without checking actual readiness
- defining a deployment without a defined rollback path
- skipping multi-stage builds for production images
- mixing local development overrides into the base docker-compose file
- using anonymous volumes instead of named volumes
- not declaring resource limits in Kubernetes or production docker-compose

### VI
Tránh:

- hard-code secret, credential, hoặc giá trị đặc thù môi trường trong Dockerfile, docker-compose, Terraform, Kubernetes manifest, hoặc CI/CD pipeline file
- dùng `latest` làm Docker image tag trong bất kỳ môi trường nào
- commit `terraform.tfstate` hoặc `.tfstate.backup` vào version control
- chạy container dưới quyền root trong production
- deploy lên production mà không có staging validation trước
- deploy lên production mà không có human approval tường minh
- merge thay đổi pipeline definition mà không review
- build image khác nhau cho môi trường khác nhau thay vì dùng runtime configuration
- dùng cùng credential cho development, staging, và production
- viết health check luôn trả về 200 mà không kiểm tra readiness thực sự
- định nghĩa deployment mà không có đường rollback được định nghĩa
- bỏ qua multi-stage build cho production image
- trộn local development override vào base docker-compose file
- dùng anonymous volume thay vì named volume
- không khai báo resource limit trong Kubernetes hoặc production docker-compose

---

## 14. Review checklist / Checklist review

### EN
When reviewing infrastructure code, first confirm the declared context:

- Is this docker-compose only for local, or also for production?
- Is Terraform in use or not?
- Is Kubernetes in use or not?
- Which CI/CD platform is in use?

Then check:

- Is any secret, credential, or token hard-coded anywhere?
- Are base image tags pinned to specific versions?
- Does every service have a health check?
- Are `depends_on` using `condition: service_healthy`?
- Does the Dockerfile use a multi-stage build for production?
- Does the Dockerfile run as non-root?
- Is a `.dockerignore` present and complete?
- Is Terraform state configured for remote storage with encryption?
- Does every Terraform variable have a type and description?
- Are Kubernetes resource limits defined for every container?
- Are liveness and readiness probes defined and distinct?
- Are CI/CD secrets stored in the platform secret store and not inline?
- Is production deployment gated behind explicit approval?
- Is the rollback path defined before the deployment is approved?
- Have pipeline definition changes been reviewed like code?
- Are environments structurally identical, differing only in configuration values?

### VI
Khi review infrastructure code, trước tiên xác nhận context đã khai báo:

- docker-compose này chỉ cho local hay còn cho production?
- Có dùng Terraform không?
- Có dùng Kubernetes không?
- Đang dùng CI/CD platform nào?

Sau đó kiểm tra:

- Có secret, credential, hoặc token nào bị hard-code ở đâu không?
- Base image tag có được ghim vào version cụ thể không?
- Mọi service có health check không?
- `depends_on` có dùng `condition: service_healthy` không?
- Dockerfile có dùng multi-stage build cho production không?
- Dockerfile có chạy dưới non-root không?
- `.dockerignore` có tồn tại và đầy đủ không?
- Terraform state có được cấu hình remote storage với encryption không?
- Mọi Terraform variable có type và description không?
- Kubernetes resource limit có được định nghĩa cho mọi container không?
- Liveness và readiness probe có được định nghĩa và khác nhau không?
- CI/CD secret có được lưu trong platform secret store và không inline không?
- Production deployment có được chặn sau explicit approval không?
- Đường rollback có được định nghĩa trước khi deployment được phê duyệt không?
- Thay đổi pipeline definition có được review như code không?
- Môi trường có cùng cấu trúc, chỉ khác ở giá trị cấu hình không?

---

## 15. Definition of done / Điều kiện hoàn thành

### EN
An infrastructure change is considered done only if:

- context has been declared: docker-compose usage, IaC tool, orchestration platform, CI/CD platform
- no secret or credential is hard-coded in any infrastructure file
- base image tags are pinned to specific versions
- every service has a health check and depends_on uses service_healthy conditions
- Dockerfiles use multi-stage builds and run as non-root for production
- .dockerignore is present and excludes source, data, and test artifacts
- Terraform state is stored remotely with encryption if Terraform is in use
- every Terraform variable has a type and description if Terraform is in use
- Kubernetes resource limits and probes are defined if Kubernetes is in use
- CI/CD secrets are stored in the platform secret store
- production deployment requires explicit human approval
- a rollback path is defined and documented before the change is merged
- pipeline definition changes have been reviewed
- environments are structurally consistent, differing only in configuration values
- the change satisfies the definition of done in `11-Definition_of_done`

### VI
Một thay đổi infrastructure chỉ được coi là done khi:

- context đã được khai báo: cách dùng docker-compose, IaC tool, orchestration platform, CI/CD platform
- không có secret hoặc credential bị hard-code trong bất kỳ file infrastructure nào
- base image tag được ghim vào version cụ thể
- mọi service có health check và depends_on dùng điều kiện service_healthy
- Dockerfile dùng multi-stage build và chạy dưới non-root cho production
- .dockerignore tồn tại và loại trừ source, data, và test artifact
- Terraform state được lưu remote với encryption nếu dùng Terraform
- mọi Terraform variable có type và description nếu dùng Terraform
- Kubernetes resource limit và probe được định nghĩa nếu dùng Kubernetes
- CI/CD secret được lưu trong platform secret store
- production deployment yêu cầu human approval tường minh
- đường rollback được định nghĩa và tài liệu hóa trước khi thay đổi được merge
- thay đổi pipeline definition đã được review
- môi trường nhất quán về cấu trúc, chỉ khác nhau về giá trị cấu hình
- thay đổi thỏa mãn definition of done trong `11-Definition_of_done`
