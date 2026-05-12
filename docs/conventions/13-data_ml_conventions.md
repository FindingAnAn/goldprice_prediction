# 13-Data-ML-Conventions / Quy ước Data và Machine Learning

## 1. Purpose / Mục đích

### EN
This document defines the conventions for data pipelines, feature engineering, model development, experiment tracking, notebook usage, and ML-specific testing and observability.
Its purpose is to ensure that data and ML systems are reproducible, traceable, testable, and safe to operate in both development and production environments.
This document extends and specializes the general conventions already defined in the project. Where a general convention already applies, this document adds ML/data-specific detail rather than repeating the general rule.

### VI
Tài liệu này định nghĩa các quy ước cho data pipeline, feature engineering, phát triển model, experiment tracking, sử dụng notebook, và testing/observability đặc thù cho ML.
Mục tiêu là đảm bảo hệ thống data và ML có tính tái tạo được, truy vết được, kiểm thử được, và an toàn để vận hành trong cả môi trường phát triển lẫn production.
Tài liệu này mở rộng và chuyên biệt hóa các quy ước chung đã được định nghĩa trong dự án. Ở những chỗ quy ước chung đã áp dụng, tài liệu này bổ sung chi tiết đặc thù cho ML/data thay vì lặp lại quy tắc chung.

---

## 2. Scope / Phạm vi

### EN
This document applies to:

- data ingestion and raw data handling
- data validation and schema enforcement
- data preprocessing and transformation
- feature engineering
- model design, training, and serialization
- experiment tracking and reproducibility
- ML pipeline design
- notebook usage and lifecycle
- ML-specific unit testing
- ML-specific observability and monitoring

### VI
Tài liệu này áp dụng cho:

- ingestion dữ liệu và xử lý raw data
- validation dữ liệu và áp đặt schema
- tiền xử lý và biến đổi dữ liệu
- feature engineering
- thiết kế, training, và serialization model
- experiment tracking và reproducibility
- thiết kế ML pipeline
- sử dụng và vòng đời của notebook
- unit testing đặc thù cho ML
- observability và monitoring đặc thù cho ML

---

## 3. Core principles / Nguyên tắc cốt lõi

### 3.1 Reproducibility is non-negotiable / Reproducibility là không thể thương lượng

#### EN
Every pipeline, training run, and transformation must produce the same result given the same data, configuration, and random seed.
Reproducibility is a first-class requirement, not a nice-to-have.

#### VI
Mọi pipeline, training run, và phép biến đổi phải cho ra cùng kết quả khi có cùng data, cấu hình, và random seed.
Reproducibility là yêu cầu hạng nhất, không phải điều tùy chọn.

---

### 3.2 Data and model must be traceable / Data và model phải truy vết được

#### EN
At any point it must be possible to answer:

- which data version was used to train this model?
- which configuration produced this result?
- which code version was used in this run?

#### VI
Tại bất kỳ thời điểm nào cũng phải có khả năng trả lời:

- model này được train từ data version nào?
- cấu hình nào tạo ra kết quả này?
- code version nào được dùng trong run này?

---

### 3.3 Fail early on data quality / Fail sớm khi có vấn đề chất lượng dữ liệu

#### EN
Data quality problems must be caught as early as possible in the pipeline.
A schema violation, unexpected null rate, or distribution shift must stop the pipeline explicitly, not produce silently degraded output.

#### VI
Các vấn đề chất lượng data phải được phát hiện càng sớm càng tốt trong pipeline.
Schema violation, null rate bất thường, hoặc distribution shift phải dừng pipeline một cách tường minh, không được để ra output bị suy giảm âm thầm.

---

### 3.4 Notebooks are exploration tools, not production paths / Notebook là công cụ khám phá, không phải đường chạy production

#### EN
Notebooks are valid for exploratory analysis, prototyping, and communication.
They must not become the execution path for production pipelines, automated jobs, or shared business logic.

#### VI
Notebook hợp lệ để phân tích khám phá, prototype, và trình bày kết quả.
Chúng không được trở thành đường chạy của production pipeline, automated job, hoặc business logic dùng chung.

---

### 3.5 Training and inference must be clearly separated / Train và inference phải tách biệt rõ ràng

#### EN
Code and logic that belong only to training must not leak into the inference path.
The inference path must remain lightweight, deterministic, and free from training-time side effects.

#### VI
Code và logic chỉ thuộc về quá trình training không được rò sang inference path.
Inference path phải nhẹ, có tính xác định, và không bị ảnh hưởng bởi side effect của quá trình training.

---

### 3.6 All ML-specific tests must be unit tests / Mọi test đặc thù ML đều phải là unit test

#### EN
All testing requirements defined in this document must be implemented as unit tests following the structure and conventions defined in `07-Testing`.
No notebook cell, script runner, or manual validation is a substitute for a unit test.
Tests must run through pytest without external system dependencies.

#### VI
Mọi yêu cầu kiểm thử được định nghĩa trong tài liệu này phải được triển khai dưới dạng unit test theo cấu trúc và quy ước đã định nghĩa trong `07-Testing`.
Không có notebook cell, script runner, hoặc validation thủ công nào thay thế được unit test.
Test phải chạy được qua pytest mà không phụ thuộc vào hệ thống bên ngoài.

---

## 4. Project structure for data and ML / Cấu trúc dự án cho data và ML

### 4.1 Standard ML project layout / Cấu trúc dự án ML chuẩn

#### EN
A data or ML project must follow the baseline structure from `01-Structure` and extend it with the following:

```
src/
  data/
    ingestion/       # adapters for each data source
    validation/      # schema definitions and validators
    preprocessing/   # cleaning and transformation logic
  features/
    engineering/     # feature transformation functions
    selection/       # feature selection logic
  modeling/
    training/        # training orchestration
    evaluation/      # metrics and evaluation logic
    serving/         # inference interface and model loading
  monitoring/
    data_quality/    # data drift and quality checks
    model_quality/   # model performance monitoring
  pipelines/         # pipeline definitions and DAGs
notebooks/           # exploratory notebooks only
artifacts/           # excluded from version control
experiments/         # experiment tracking configs
```

#### VI
Dự án data hoặc ML phải tuân theo cấu trúc nền tảng từ `01-Structure` và mở rộng với phần sau:

```
src/
  data/
    ingestion/       # adapter cho từng nguồn dữ liệu
    validation/      # định nghĩa schema và validator
    preprocessing/   # logic làm sạch và biến đổi
  features/
    engineering/     # hàm biến đổi feature
    selection/       # logic chọn feature
  modeling/
    training/        # orchestration cho training
    evaluation/      # metrics và logic đánh giá
    serving/         # interface inference và load model
  monitoring/
    data_quality/    # kiểm tra drift và chất lượng data
    model_quality/   # monitoring hiệu suất model
  pipelines/         # định nghĩa pipeline và DAG
notebooks/           # chỉ dành cho notebook khám phá
artifacts/           # loại khỏi version control
experiments/         # config cho experiment tracking
```

---

### 4.2 Artifacts must be excluded from version control / Artifact phải được loại khỏi version control

#### EN
Model files, large datasets, and intermediate data artifacts must not be committed to the repository.
Use `.gitignore` to exclude common artifact formats: `.pkl`, `.joblib`, `.h5`, `.onnx`, `.parquet`, `.csv` for data files.

#### VI
File model, dataset lớn, và data artifact trung gian không được commit vào repository.
Dùng `.gitignore` để loại trừ các format artifact phổ biến: `.pkl`, `.joblib`, `.h5`, `.onnx`, `.parquet`, `.csv` cho file data.

---

## 5. Data layer conventions / Quy ước cho lớp data

### 5.1 Each data source must have its own adapter / Mỗi nguồn data phải có adapter riêng

#### EN
Data ingestion code must follow the infrastructure adapter pattern from `01-Structure` and `04-Dependencies`.
Each source such as a database, API, file system, or object store must have a dedicated adapter class in `src/data/ingestion/`.
Business logic must not import data-source-specific SDKs directly.

#### VI
Code ingestion data phải tuân theo pattern adapter của lớp infrastructure theo `01-Structure` và `04-Dependencies`.
Mỗi nguồn như database, API, file system, hoặc object store phải có class adapter riêng trong `src/data/ingestion/`.
Business logic không được import trực tiếp SDK đặc thù của nguồn dữ liệu.

---

### 5.2 Raw data must be preserved before transformation / Raw data phải được lưu trước khi biến đổi

#### EN
Raw ingested data must be stored as-is before any transformation is applied.
The raw layer is immutable. Transformations always produce a new artifact or layer.

#### VI
Data raw được ingested phải được lưu nguyên trạng trước khi áp dụng bất kỳ phép biến đổi nào.
Lớp raw là bất biến. Phép biến đổi luôn tạo ra artifact hoặc lớp mới.

---

### 5.3 Schema must be validated explicitly / Schema phải được validate tường minh

#### EN
Every dataset entering the pipeline must pass through an explicit schema validation step.
Schema definitions must be versioned alongside code.
Validation failures must raise a clear error and stop the pipeline.

Recommended tools:
- `pandera` for DataFrame schema validation
- `pydantic` for record-level schema validation
- `great_expectations` for complex data quality suites

#### VI
Mọi dataset đi vào pipeline phải qua bước validate schema tường minh.
Định nghĩa schema phải được version hóa cùng với code.
Khi validation thất bại phải raise lỗi rõ ràng và dừng pipeline.

Công cụ khuyến nghị:
- `pandera` để validate schema cho DataFrame
- `pydantic` để validate schema ở cấp record
- `great_expectations` cho các bộ kiểm tra chất lượng data phức tạp

---

### 5.4 Data types must be explicit / Kiểu dữ liệu phải tường minh

#### EN
Do not rely on automatic type inference from pandas or other libraries.
Specify `dtype` explicitly when reading data.
Use the most appropriate type for the domain:

- `int64` for counts and identifiers
- `float32` for model inputs where memory matters
- `float64` for financial or precision-sensitive values
- `bool` for binary flags, not integers
- `category` for low-cardinality string columns with known values
- `pd.Timestamp` with explicit timezone for datetime values

#### VI
Không được dựa vào suy kiểu tự động từ pandas hoặc thư viện khác.
Chỉ định `dtype` tường minh khi đọc data.
Dùng kiểu phù hợp nhất với ngữ nghĩa:

- `int64` cho count và identifier
- `float32` cho đầu vào model khi bộ nhớ quan trọng
- `float64` cho giá trị tài chính hoặc cần độ chính xác cao
- `bool` cho cờ nhị phân, không dùng integer
- `category` cho cột string có ít giá trị và tập giá trị đã biết
- `pd.Timestamp` với timezone tường minh cho datetime

---

### 5.5 Missing value policy must be explicit / Chính sách với giá trị thiếu phải tường minh

#### EN
Every column with potential missing values must have a documented handling strategy.
Choose explicitly from:

- impute with a specific strategy and document the reason
- drop rows or columns with justification
- flag as a separate boolean feature

Do not allow `NaN` to propagate silently through the pipeline.

#### VI
Mọi cột có khả năng có giá trị thiếu phải có chiến lược xử lý được tài liệu hóa.
Chọn tường minh một trong các cách:

- impute với một chiến lược cụ thể và ghi rõ lý do
- drop row hoặc cột kèm lý giải
- đánh dấu thành feature boolean riêng

Không được để `NaN` lan truyền âm thầm qua pipeline.

---

### 5.6 Data size must be handled intentionally / Kích thước data phải được xử lý có chủ đích

#### EN
Choose the right tool based on data scale:

- use `pandas` for data that fits comfortably in memory
- use `polars` when performance on medium-sized data matters
- use `pyspark` or `dask` for data that exceeds single-machine memory
- use chunked reading when streaming large files

Do not load entire datasets into memory when only a subset or stream is needed.

#### VI
Chọn công cụ phù hợp dựa trên quy mô dữ liệu:

- dùng `pandas` khi data vừa đủ trong bộ nhớ
- dùng `polars` khi hiệu suất với data cỡ vừa quan trọng
- dùng `pyspark` hoặc `dask` khi data vượt bộ nhớ một máy
- dùng đọc theo chunk khi stream file lớn

Không được load toàn bộ dataset vào bộ nhớ khi chỉ cần một phần hoặc có thể stream.

---

## 6. Feature engineering conventions / Quy ước feature engineering

### 6.1 Feature naming rules / Quy tắc đặt tên feature

#### EN
Feature names must be explicit, self-explanatory, and consistent.

Rules:
- use `snake_case` for all feature names
- prefix by source or domain: `user_`, `transaction_`, `product_`, `session_`
- boolean features must use `is_`, `has_`, or `did_` prefix
- ratio features must use `_ratio` or `_rate` suffix
- count features must use `_count` or `_n_` prefix
- do not use abbreviations unless universally understood in the domain

#### VI
Tên feature phải rõ ràng, tự giải thích, và nhất quán.

Quy tắc:
- dùng `snake_case` cho tất cả tên feature
- prefix theo nguồn hoặc domain: `user_`, `transaction_`, `product_`, `session_`
- feature boolean phải có prefix `is_`, `has_`, hoặc `did_`
- feature tỷ lệ phải có suffix `_ratio` hoặc `_rate`
- feature đếm phải có prefix `_count` hoặc `_n_`
- không viết tắt trừ khi phổ biến và rõ trong domain

---

### 6.2 Feature functions must be isolated / Hàm feature phải được cô lập

#### EN
Each feature or closely related group of features must be implemented as a dedicated function.
Feature functions must:

- accept a DataFrame or Series as input and return a transformed result
- have no side effects beyond the transformation
- be independently testable
- not depend on global state or external systems

#### VI
Mỗi feature hoặc nhóm feature liên quan chặt phải được triển khai trong một hàm riêng.
Hàm feature phải:

- nhận DataFrame hoặc Series làm đầu vào và trả về kết quả đã biến đổi
- không có side effect nào ngoài phép biến đổi
- có thể test độc lập được
- không phụ thuộc vào global state hoặc hệ thống ngoài

---

### 6.3 Data leakage must be prevented by convention / Rò rỉ data phải được ngăn bằng quy ước

#### EN
Data leakage must be treated as a correctness violation, not just a performance concern.

Mandatory rules:
- always split data into train and test before fitting any transformer or encoder
- fit all scalers, encoders, and imputers on the training set only
- never use the target variable or any variable derived from it as a feature
- never use information from future time periods in features for past predictions
- document the split strategy and enforce it through code structure, not just comments

#### VI
Data leakage phải được xem là vi phạm tính đúng đắn, không chỉ là vấn đề hiệu suất.

Quy tắc bắt buộc:
- luôn split data thành train và test trước khi fit bất kỳ transformer hoặc encoder nào
- chỉ fit scaler, encoder, và imputer trên training set
- không bao giờ dùng target variable hoặc biến dẫn xuất từ nó làm feature
- không dùng thông tin từ kỳ thời gian trong tương lai làm feature cho dự đoán quá khứ
- tài liệu hóa chiến lược split và thực thi nó qua cấu trúc code, không chỉ comment

---

### 6.4 Feature transformers must be stateless by default / Feature transformer phải stateless theo mặc định

#### EN
Feature transformation functions must not store internal state by default.
When a transformer requires fitting (such as a scaler or encoder), it must be:

- explicitly instantiated and fit as a separate step
- persisted as a named artifact alongside the model
- loaded explicitly during inference

Do not hide stateful transformers inside functions that appear stateless.

#### VI
Hàm biến đổi feature không được lưu trạng thái nội bộ theo mặc định.
Khi một transformer cần fit (như scaler hoặc encoder), nó phải được:

- khởi tạo và fit tường minh như một bước riêng
- lưu trữ như một artifact được đặt tên cùng với model
- load tường minh trong quá trình inference

Không được giấu stateful transformer bên trong hàm trông có vẻ stateless.

---

## 7. Model conventions / Quy ước về model

### 7.1 Model interface must be consistent / Interface của model phải nhất quán

#### EN
Every model implementation must expose a consistent interface with at minimum:

- `train(X, y, config)` or equivalent training entrypoint
- `predict(X)` returning predictions in a documented format
- `evaluate(X, y)` returning a standardized metrics dictionary

Model classes must not contain data loading or ingestion logic.

#### VI
Mỗi model implementation phải expose một interface nhất quán gồm tối thiểu:

- `train(X, y, config)` hoặc training entrypoint tương đương
- `predict(X)` trả về dự đoán theo format được tài liệu hóa
- `evaluate(X, y)` trả về dictionary metric được chuẩn hóa

Model class không được chứa logic load hoặc ingestion dữ liệu.

---

### 7.2 Hyperparameters must go through config / Hyperparameter phải đi qua config

#### EN
All hyperparameters must be defined in the configuration system described in `02-Config`.
No hyperparameter may be hard-coded inside a model class or training function.

Naming rules for hyperparameters:
- use `snake_case`
- prefix by component when ambiguous: `optimizer_lr`, `model_dropout_rate`
- use full words: `learning_rate`, not `lr`

#### VI
Mọi hyperparameter phải được định nghĩa trong hệ thống cấu hình mô tả trong `02-Config`.
Không được hard-code hyperparameter bên trong model class hoặc training function.

Quy tắc đặt tên hyperparameter:
- dùng `snake_case`
- prefix theo thành phần khi mơ hồ: `optimizer_lr`, `model_dropout_rate`
- dùng từ đầy đủ: `learning_rate`, không phải `lr`

---

### 7.3 Random state must be controlled centrally / Random state phải được kiểm soát tập trung

#### EN
All random seeds must be set in one centralized location, typically the training configuration.
Every library that uses randomness must receive the seed explicitly:

- `numpy.random.seed(seed)`
- `random.seed(seed)`
- `torch.manual_seed(seed)` if applicable
- `random_state=seed` for all scikit-learn estimators

Do not set seeds inside model methods or transformation functions.

#### VI
Mọi random seed phải được set ở một vị trí tập trung, thường là cấu hình training.
Mọi thư viện sử dụng tính ngẫu nhiên phải nhận seed tường minh:

- `numpy.random.seed(seed)`
- `random.seed(seed)`
- `torch.manual_seed(seed)` nếu áp dụng
- `random_state=seed` cho mọi estimator scikit-learn

Không được set seed bên trong model method hoặc transformation function.

---

### 7.4 Model artifacts must follow a consistent naming convention / Artifact model phải theo quy ước đặt tên nhất quán

#### EN
Model artifact file names must include:

- model name
- version or identifier
- date in `YYYYMMDD` format

Example: `churn_predictor_v2_20250317.joblib`

Model artifacts must be stored with a companion metadata file containing:
- feature list used
- training data version or hash
- training configuration
- performance metrics on evaluation set
- library versions

#### VI
Tên file artifact model phải bao gồm:

- tên model
- version hoặc identifier
- ngày theo định dạng `YYYYMMDD`

Ví dụ: `churn_predictor_v2_20250317.joblib`

Artifact model phải được lưu kèm file metadata chứa:
- danh sách feature được dùng
- version hoặc hash của data training
- cấu hình training
- performance metric trên evaluation set
- version của các thư viện

---

### 7.5 Serialization format must be explicit / Format serialization phải tường minh

#### EN
Choose a serialization format intentionally based on the use case:

- `joblib` for scikit-learn compatible models
- `torch.save` / `state_dict` for PyTorch models
- `ONNX` for cross-framework inference
- `mlflow` model format when using MLflow

Do not mix formats across the same system without explicit justification.
Always test that a saved model loads and produces identical predictions before treating serialization as complete.

#### VI
Chọn format serialization có chủ đích dựa trên use case:

- `joblib` cho model tương thích scikit-learn
- `torch.save` / `state_dict` cho model PyTorch
- `ONNX` cho inference xuyên framework
- mlflow model format khi dùng MLflow

Không được trộn format trong cùng một hệ thống nếu không có lý do tường minh.
Luôn kiểm tra rằng model đã lưu load được và cho ra dự đoán giống hệt trước khi coi serialization là hoàn thành.

---

## 8. Experiment tracking conventions / Quy ước experiment tracking

### 8.1 Every training run must be logged / Mỗi training run phải được log

#### EN
Every meaningful training run must log at minimum:

- random seed
- data version or hash
- feature list
- hyperparameter configuration
- training duration
- metrics on train, validation, and test sets
- model artifact location
- library versions

#### VI
Mọi training run có ý nghĩa phải log tối thiểu:

- random seed
- version hoặc hash của data
- danh sách feature
- cấu hình hyperparameter
- thời gian training
- metric trên train, validation, và test set
- vị trí artifact model
- version của các thư viện

---

### 8.2 Experiment naming must be consistent / Đặt tên experiment phải nhất quán

#### EN
Experiments must follow a consistent naming pattern that makes it easy to identify the purpose and context.

Preferred pattern: `{project}_{model_type}_{focus}_{date}`

Examples:
- `churn_xgboost_feature_selection_20250317`
- `fraud_lstm_baseline_20250317`

Avoid vague names such as `test`, `final`, `new_model`, or `experiment_1`.

#### VI
Experiment phải theo một pattern đặt tên nhất quán giúp dễ xác định mục đích và ngữ cảnh.

Pattern ưu tiên: `{project}_{model_type}_{focus}_{date}`

Ví dụ:
- `churn_xgboost_feature_selection_20250317`
- `fraud_lstm_baseline_20250317`

Tránh tên mơ hồ như `test`, `final`, `new_model`, hoặc `experiment_1`.

---

### 8.3 Every model must be compared against a baseline / Mọi model phải được so sánh với baseline

#### EN
A baseline model must be defined before evaluating any new model.
The baseline must be:

- reproducible
- logged with the same metric set as candidate models
- referenced explicitly in experiment comparisons

A new model is not considered better than baseline until the comparison is documented.

#### VI
Model baseline phải được định nghĩa trước khi đánh giá bất kỳ model mới nào.
Baseline phải:

- có tính tái tạo được
- được log với cùng bộ metric như model candidate
- được tham chiếu tường minh khi so sánh experiment

Một model mới không được coi là tốt hơn baseline cho đến khi sự so sánh được tài liệu hóa.

---

### 8.4 Metrics must be logged per split / Metric phải được log cho từng split

#### EN
Log metrics separately for train, validation, and test sets.
Do not report only the final or test metric.
Log per-epoch or per-step metrics when the training process is iterative, to allow inspection of learning curves.

#### VI
Log metric riêng biệt cho train, validation, và test set.
Không chỉ báo cáo metric cuối cùng hoặc test metric.
Log metric theo từng epoch hoặc step khi quá trình training là lặp lại, để có thể kiểm tra learning curve.

---

## 9. Pipeline design conventions / Quy ước thiết kế pipeline

### 9.1 Each pipeline step must be idempotent / Mỗi bước pipeline phải idempotent

#### EN
Running any pipeline step multiple times with the same input must produce the same output.
Steps must not accumulate side effects across runs.

#### VI
Chạy bất kỳ bước pipeline nào nhiều lần với cùng đầu vào phải cho ra cùng đầu ra.
Các bước không được tích lũy side effect qua nhiều lần chạy.

---

### 9.2 Step boundaries must be explicit / Ranh giới bước phải tường minh

#### EN
Each pipeline step must have:

- clearly defined input: data artifact path, schema, or contract
- clearly defined output: artifact location and format
- a named, versioned intermediate artifact when the step is expensive

Do not allow step output to be ambiguously coupled to step implementation details.

#### VI
Mỗi bước pipeline phải có:

- đầu vào được định nghĩa rõ: artifact path, schema, hoặc contract của data
- đầu ra được định nghĩa rõ: vị trí artifact và format
- artifact trung gian được đặt tên, version hóa khi bước đó tốn kém

Không được để đầu ra của bước bị ghép chặt mơ hồ vào chi tiết implementation của bước.

---

### 9.3 Steps must not modify input data in-place / Bước không được modify data đầu vào in-place

#### EN
Pipeline steps must treat their input data as immutable.
Always produce a new DataFrame, array, or artifact rather than modifying the input.

#### VI
Bước pipeline phải coi data đầu vào là bất biến.
Luôn tạo ra DataFrame, array, hoặc artifact mới thay vì modify đầu vào.

---

### 9.4 Pipeline configuration must be externalized / Cấu hình pipeline phải được externalize

#### EN
All pipeline configuration including data paths, artifact locations, and parameters must go through the config system defined in `02-Config`.
Do not hard-code file paths, bucket names, or pipeline parameters inside pipeline definition files.

#### VI
Mọi cấu hình pipeline bao gồm data path, artifact location, và tham số phải đi qua hệ thống config được định nghĩa trong `02-Config`.
Không hard-code file path, bucket name, hoặc pipeline parameter bên trong file định nghĩa pipeline.

---

### 9.5 Long-running pipelines must support checkpointing / Pipeline chạy lâu phải hỗ trợ checkpoint

#### EN
Pipelines that take significant time to complete must save intermediate results at major step boundaries.
A failed pipeline must be resumable from the last successful checkpoint, not require a full restart.

#### VI
Pipeline tốn nhiều thời gian để hoàn thành phải lưu kết quả trung gian tại các ranh giới bước chính.
Pipeline bị fail phải có thể tiếp tục từ checkpoint thành công cuối cùng, không yêu cầu khởi động lại từ đầu.

---

## 10. Notebook conventions / Quy ước notebook

### 10.1 Notebooks are for exploration only / Notebook chỉ dùng cho khám phá

#### EN
Notebooks must not be used as:

- production data pipelines
- automated scheduled jobs
- shared business logic modules
- any code path that requires automated testing or CI validation

When notebook logic needs to be reused, it must be refactored into a proper Python module under `src/` before being promoted.

#### VI
Notebook không được dùng như:

- pipeline data production
- automated scheduled job
- module business logic dùng chung
- bất kỳ code path nào cần test tự động hoặc CI validation

Khi logic trong notebook cần được tái sử dụng, nó phải được refactor thành module Python hợp lệ trong `src/` trước khi được đưa vào sử dụng chính thức.

---

### 10.2 Notebook naming must be consistent / Đặt tên notebook phải nhất quán

#### EN
Notebook file names must follow this pattern:

`{number}-{author-initials}-{short-description}.ipynb`

Examples:
- `01-tn-exploratory-user-behavior.ipynb`
- `02-tn-feature-correlation-analysis.ipynb`
- `03-tn-churn-model-prototype.ipynb`

Avoid names such as `Untitled.ipynb`, `analysis.ipynb`, or `final_version2.ipynb`.

#### VI
Tên file notebook phải theo pattern sau:

`{number}-{initials-tác-giả}-{mô-tả-ngắn}.ipynb`

Ví dụ:
- `01-tn-exploratory-user-behavior.ipynb`
- `02-tn-feature-correlation-analysis.ipynb`
- `03-tn-churn-model-prototype.ipynb`

Tránh tên như `Untitled.ipynb`, `analysis.ipynb`, hoặc `final_version2.ipynb`.

---

### 10.3 Notebook structure must follow a standard layout / Cấu trúc notebook phải theo layout chuẩn

#### EN
Every notebook must contain:

1. A header cell at the top with:
   - notebook purpose
   - author
   - date
   - data sources used

2. An imports and configuration cell immediately after the header

3. A summary or conclusions cell at the end with:
   - key findings
   - next steps or follow-up work

Imports and configuration must not be scattered across the notebook body.

#### VI
Mọi notebook phải chứa:

1. Cell header ở đầu với:
   - mục đích notebook
   - tác giả
   - ngày
   - nguồn data được dùng

2. Cell import và cấu hình ngay sau header

3. Cell tóm tắt hoặc kết luận ở cuối với:
   - phát hiện chính
   - bước tiếp theo hoặc follow-up

Import và cấu hình không được rải khắp nội dung notebook.

---

### 10.4 Notebook outputs must be cleared before commit / Output của notebook phải được xóa trước khi commit

#### EN
Commit notebooks with cleared cell outputs to avoid bloating the repository and prevent accidental leakage of sensitive data through output cells.

Use `nbstripout` as a pre-commit hook to automate this.

Exception: notebooks intended as reports or communication artifacts may retain outputs, but must not contain sensitive data.

#### VI
Commit notebook với output của cell đã được xóa để tránh làm phình repository và ngăn rò rỉ dữ liệu nhạy cảm qua output cell.

Dùng `nbstripout` như pre-commit hook để tự động hóa điều này.

Ngoại lệ: notebook dùng như báo cáo hoặc artifact giao tiếp có thể giữ output, nhưng không được chứa dữ liệu nhạy cảm.

---

### 10.5 Notebooks must not contain secrets / Notebook không được chứa secret

#### EN
Notebooks must follow all rules in `08-Security`.
Tokens, passwords, API keys, and sensitive data must not appear in notebook cells, output cells, or metadata.
Load credentials from environment variables or config, never inline.

#### VI
Notebook phải tuân theo tất cả quy tắc trong `08-Security`.
Token, mật khẩu, API key, và dữ liệu nhạy cảm không được xuất hiện trong cell code, output cell, hoặc metadata.
Load credential từ environment variable hoặc config, không bao giờ inline.

---

## 11. ML-specific unit testing / Unit test đặc thù cho ML

### 11.1 All ML tests must be unit tests / Mọi test ML đều phải là unit test

#### EN
Every test scenario defined in this section must be implemented as a pytest unit test following `07-Testing`.

Mandatory requirements for ML unit tests:
- must run without external systems: no real databases, no S3, no model registries
- must use fixtures to create sample DataFrames and arrays inline
- must be deterministic: fix all seeds and avoid time-dependent assertions
- must run in the same CI pipeline as all other unit tests
- no notebook-based validation or script runner may substitute for a pytest test

#### VI
Mọi scenario test được định nghĩa trong section này phải được triển khai dưới dạng pytest unit test theo `07-Testing`.

Yêu cầu bắt buộc cho ML unit test:
- phải chạy không cần hệ thống ngoài: không có database thật, không có S3, không có model registry
- phải dùng fixture để tạo sample DataFrame và array inline
- phải có tính xác định: fix mọi seed và tránh assert phụ thuộc vào thời gian
- phải chạy trong cùng CI pipeline như mọi unit test khác
- không có notebook-based validation hay script runner nào thay thế được pytest test

---

### 11.2 Data validation must be unit tested / Validation data phải được unit test

#### EN
For each schema validator and data quality check, write unit tests that cover:

- valid data passes validation without error
- missing required column raises the expected error
- wrong column dtype raises the expected error
- null values in non-nullable columns raise the expected error
- out-of-range values are caught when range constraints exist

**Example test fixture pattern:**
```python
@pytest.fixture
def valid_user_df():
    return pd.DataFrame({
        "user_id": [1, 2, 3],
        "age": [25, 30, 45],
        "is_active": [True, False, True],
    })

def test_should_pass_validation_when_dataframe_is_valid(valid_user_df):
    result = validate_user_schema(valid_user_df)
    assert result.is_valid

def test_should_fail_validation_when_required_column_is_missing():
    df = pd.DataFrame({"user_id": [1, 2]})
    with pytest.raises(SchemaValidationError):
        validate_user_schema(df)
```

#### VI
Với mỗi schema validator và data quality check, viết unit test bao phủ:

- data hợp lệ pass validation không có lỗi
- thiếu cột bắt buộc raise đúng lỗi mong đợi
- dtype cột sai raise đúng lỗi mong đợi
- giá trị null trong cột không cho phép null raise đúng lỗi mong đợi
- giá trị ngoài phạm vi bị bắt khi có ràng buộc phạm vi

---

### 11.3 Feature engineering must be unit tested / Feature engineering phải được unit test

#### EN
For each feature function, write unit tests that cover:

- correct output value for known input
- correct output dtype
- correct output shape (number of rows preserved)
- behavior with a single-row input
- behavior with an empty DataFrame
- behavior with all-null input for the relevant column
- no mutation of the input DataFrame

**Scenarios that must be covered:**

| Scenario | What to assert |
|---|---|
| happy path with typical data | output value matches expected |
| input with nulls | output handles nulls per documented policy |
| empty DataFrame | returns empty DataFrame without error |
| single-row DataFrame | returns single-row result |
| input dtype variation | output dtype is correct regardless of input |
| input is not mutated | `df` before and after call are identical |

#### VI
Với mỗi hàm feature, viết unit test bao phủ:

- giá trị output đúng với input đã biết
- dtype output đúng
- shape output đúng (số row được giữ nguyên)
- hành vi với input một row
- hành vi với DataFrame rỗng
- hành vi với input toàn null cho cột liên quan
- không làm thay đổi DataFrame đầu vào

---

### 11.4 Data leakage prevention must be unit tested / Ngăn data leakage phải được unit test

#### EN
Write tests that assert the transform was fit on training data only.

**Mandatory scenarios:**

- assert that calling `transform()` without `fit()` raises an error
- assert that fitting on the training set and transforming on the test set produces different statistics than fitting on the full dataset
- assert that the transformer does not access any column it was not explicitly given during fit

#### VI
Viết test assert rằng transformer chỉ được fit trên training data.

**Scenario bắt buộc:**

- assert rằng gọi `transform()` mà không `fit()` raise lỗi
- assert rằng fit trên training set và transform test set cho ra thống kê khác khi fit trên toàn bộ dataset
- assert rằng transformer không truy cập cột nào nó không được nhận tường minh lúc fit

---

### 11.5 Model interface must be unit tested / Interface model phải được unit test

#### EN
For every model class, write unit tests that cover:

- `predict()` returns the correct output shape given known input shape
- `predict()` returns output in the documented format (numpy array, DataFrame, list)
- `predict()` does not modify the input array or DataFrame
- `predict()` is deterministic: calling it twice with the same input returns identical results
- `evaluate()` returns a dictionary containing the documented metric keys
- the model raises a clear error when called before training

**Example test pattern:**
```python
def test_should_return_correct_shape_when_predicting(trained_model, sample_features):
    predictions = trained_model.predict(sample_features)
    assert predictions.shape == (len(sample_features),)

def test_should_not_mutate_input_when_predicting(trained_model, sample_features):
    original = sample_features.copy()
    trained_model.predict(sample_features)
    pd.testing.assert_frame_equal(sample_features, original)

def test_should_return_identical_predictions_on_repeated_calls(trained_model, sample_features):
    first = trained_model.predict(sample_features)
    second = trained_model.predict(sample_features)
    np.testing.assert_array_equal(first, second)
```

#### VI
Với mỗi model class, viết unit test bao phủ:

- `predict()` trả về shape đầu ra đúng với shape đầu vào đã biết
- `predict()` trả về output đúng format được tài liệu hóa (numpy array, DataFrame, list)
- `predict()` không làm thay đổi array hoặc DataFrame đầu vào
- `predict()` có tính xác định: gọi hai lần với cùng đầu vào trả về kết quả giống hệt
- `evaluate()` trả về dictionary chứa các metric key được tài liệu hóa
- model raise lỗi rõ ràng khi được gọi trước khi training

---

### 11.6 Pipeline steps must be unit tested / Bước pipeline phải được unit test

#### EN
For each pipeline step function, write unit tests that cover:

- valid input produces valid output with the expected schema
- input is not mutated
- the step can be called multiple times with the same input and produce the same output (idempotency)
- the step fails with a clear error when required input columns are missing

Use small, inline-created DataFrames as fixtures. Do not read from real files in unit tests.

#### VI
Với mỗi hàm bước pipeline, viết unit test bao phủ:

- đầu vào hợp lệ tạo ra đầu ra hợp lệ với schema mong đợi
- đầu vào không bị thay đổi
- bước có thể được gọi nhiều lần với cùng đầu vào và cho ra cùng kết quả (idempotency)
- bước fail với lỗi rõ ràng khi cột đầu vào bắt buộc bị thiếu

Dùng DataFrame nhỏ được tạo inline làm fixture. Không đọc từ file thật trong unit test.

---

### 11.7 ML test fixtures must be minimal and inline / ML test fixture phải tối giản và inline

#### EN
ML unit test fixtures must:

- create DataFrames and arrays with the minimum rows needed to exercise the behavior
- not depend on external files, databases, or object stores
- be clearly named to indicate what scenario they represent
- fix all random seeds when creating synthetic data

Avoid fixtures with hundreds of rows. Three to ten rows is sufficient for most unit test scenarios.

#### VI
ML unit test fixture phải:

- tạo DataFrame và array với số row tối thiểu cần để kiểm tra hành vi
- không phụ thuộc vào file ngoài, database, hoặc object store
- được đặt tên rõ ràng để biểu đạt scenario mà chúng đại diện
- fix mọi random seed khi tạo dữ liệu tổng hợp

Tránh fixture có hàng trăm row. Ba đến mười row là đủ cho hầu hết scenario unit test.

---

## 12. ML-specific observability / Observability đặc thù cho ML

### 12.1 Data quality must be monitored in production / Chất lượng data phải được monitor trong production

#### EN
Production data pipelines must emit the following signals:

- missing rate per column for key features
- distribution statistics per feature (mean, std, min, max, percentiles) compared to training baseline
- schema validation pass/fail rate
- data freshness: time since last successful ingestion
- row count per batch or time window

Alerts must be triggered when:
- missing rate exceeds the threshold documented at training time
- feature distribution drift exceeds a configured threshold
- schema validation fails

#### VI
Pipeline data production phải phát ra các tín hiệu sau:

- missing rate theo cột cho các feature quan trọng
- thống kê phân phối theo feature (mean, std, min, max, percentiles) so với baseline lúc training
- tỷ lệ pass/fail của schema validation
- độ tươi mới của data: thời gian kể từ lần ingestion thành công gần nhất
- row count theo batch hoặc time window

Alert phải được kích hoạt khi:
- missing rate vượt ngưỡng được tài liệu hóa lúc training
- feature distribution drift vượt ngưỡng được cấu hình
- schema validation fail

---

### 12.2 Model serving must be observable / Model serving phải quan sát được

#### EN
Every model serving endpoint or batch scoring job must log:

- model name and version for each prediction batch
- inference latency (p50, p95, p99)
- prediction volume
- prediction distribution (mean, std, and class distribution for classifiers)
- error rate and error types

#### VI
Mọi endpoint model serving hoặc batch scoring job phải log:

- tên và version model cho mỗi batch dự đoán
- inference latency (p50, p95, p99)
- prediction volume
- phân phối dự đoán (mean, std, và phân phối class với classifier)
- tỷ lệ lỗi và loại lỗi

---

### 12.3 Model drift must be detectable / Model drift phải có thể phát hiện được

#### EN
Production ML systems must have mechanisms to detect:

- input feature drift: distribution shift of incoming data compared to training distribution
- prediction drift: shift in the output prediction distribution
- performance degradation: when ground truth labels are available

When drift is detected, the monitoring system must emit an alert that triggers review of whether retraining is needed.

#### VI
Hệ thống ML production phải có cơ chế phát hiện:

- input feature drift: phân phối data đầu vào thay đổi so với phân phối lúc training
- prediction drift: phân phối dự đoán đầu ra thay đổi
- suy giảm hiệu suất: khi ground truth label có sẵn

Khi drift được phát hiện, hệ thống monitoring phải phát alert kích hoạt việc xem xét liệu có cần retraining không.

---

### 12.4 Pipeline execution must be observable / Thực thi pipeline phải quan sát được

#### EN
Every pipeline run must log:

- start time and end time of each step
- input row count and output row count per step
- artifact locations written per step
- whether the run succeeded, failed, or was resumed from checkpoint
- a unique run identifier for end-to-end tracing

#### VI
Mỗi lần chạy pipeline phải log:

- thời gian bắt đầu và kết thúc của từng bước
- row count đầu vào và đầu ra theo từng bước
- vị trí artifact được ghi theo từng bước
- run thành công, fail, hay được resume từ checkpoint
- một run identifier duy nhất để truy vết đầu cuối

---

## 13. Python-specific ML code rules / Quy tắc code ML đặc thù Python

### 13.1 Type hints are mandatory for all public functions / Type hint bắt buộc cho mọi public function

#### EN
All public functions in data and ML modules must have explicit type hints.
Use specific types rather than `Any`:

- `pd.DataFrame` not `Any`
- `np.ndarray` not `Any`
- `list[float]` not `list`
- `dict[str, float]` not `dict`

#### VI
Mọi public function trong module data và ML phải có type hint tường minh.
Dùng kiểu cụ thể thay vì `Any`:

- `pd.DataFrame` không phải `Any`
- `np.ndarray` không phải `Any`
- `list[float]` không phải `list`
- `dict[str, float]` không phải `dict`

---

### 13.2 Vectorized operations must be preferred over loops / Vectorized operation phải được ưu tiên hơn loop

#### EN
Prefer pandas and numpy vectorized operations over Python loops when operating on data.
If a Python loop is necessary, document the reason.

Avoid:
```python
results = []
for _, row in df.iterrows():
    results.append(row["value"] * 2)
df["doubled"] = results
```

Prefer:
```python
df["doubled"] = df["value"] * 2
```

#### VI
Ưu tiên vectorized operation của pandas và numpy hơn Python loop khi xử lý data.
Nếu phải dùng Python loop, ghi rõ lý do.

---

### 13.3 Memory must be managed intentionally / Bộ nhớ phải được quản lý có chủ đích

#### EN
Delete large intermediate objects that are no longer needed:

```python
del large_df
import gc
gc.collect()
```

Use chunked reading when processing files that may not fit in memory.
Do not hold multiple large datasets in memory simultaneously if only one is needed at a time.

#### VI
Xóa các object trung gian lớn không còn cần thiết:

```python
del large_df
import gc
gc.collect()
```

Dùng đọc theo chunk khi xử lý file có thể không vừa bộ nhớ.
Không giữ nhiều dataset lớn trong bộ nhớ cùng lúc nếu chỉ cần một cái tại một thời điểm.

---

## 14. Anti-patterns / Mẫu xấu cần tránh

### EN
Avoid:

- using notebooks as production pipeline execution paths
- hard-coding file paths, thresholds, or hyperparameters in model or pipeline code
- fitting scalers or encoders on the full dataset before splitting
- committing model artifacts or large data files to version control
- training a model without logging data version, config, and metrics
- copy-pasting feature logic instead of creating a shared function
- allowing NaN values to propagate silently through transformations
- writing ML tests that depend on real files, databases, or external services
- defining random behavior without setting and logging seeds
- loading entire datasets into memory when chunked processing is sufficient
- creating notebooks with meaningful logic that is never refactored into modules
- shipping a model without a companion metadata file
- reporting only test metrics without logging train and validation metrics

### VI
Tránh:

- dùng notebook làm đường chạy pipeline production
- hard-code file path, threshold, hoặc hyperparameter trong code model hoặc pipeline
- fit scaler hoặc encoder trên toàn bộ dataset trước khi split
- commit artifact model hoặc file data lớn vào version control
- train model mà không log data version, config, và metrics
- copy-paste logic feature thay vì tạo hàm dùng chung
- để NaN lan truyền âm thầm qua các bước biến đổi
- viết ML test phụ thuộc vào file thật, database, hoặc dịch vụ ngoài
- định nghĩa hành vi ngẫu nhiên mà không set và log seed
- load toàn bộ dataset vào bộ nhớ khi chunked processing là đủ
- tạo notebook có logic có ý nghĩa mà không bao giờ được refactor thành module
- deploy model mà không có file metadata đi kèm
- chỉ báo cáo test metric mà không log train và validation metric

---

## 15. Review checklist / Checklist review

### EN
When reviewing data or ML code, check:

- Is raw data preserved before transformation?
- Is schema validation present and does it fail loudly?
- Are data types defined explicitly?
- Is the missing value handling strategy documented per column?
- Are all feature functions testable in isolation?
- Is there any risk of data leakage: was splitting done before fitting?
- Are all random seeds set centrally?
- Does the model expose a consistent interface?
- Are hyperparameters externalized through config?
- Is the model artifact named consistently and accompanied by a metadata file?
- Is the experiment logged with data version, config, and metrics per split?
- Is there a baseline comparison?
- Is the pipeline idempotent and resumable?
- Are notebooks clean of outputs and secrets before commit?
- Are all ML tests implemented as pytest unit tests without external dependencies?
- Are data quality and model serving signals observable in production?

### VI
Khi review code data hoặc ML, cần kiểm tra:

- Raw data có được lưu trước khi biến đổi không?
- Schema validation có hiện diện và fail rõ ràng không?
- Kiểu dữ liệu có được định nghĩa tường minh không?
- Chiến lược xử lý giá trị thiếu có được tài liệu hóa theo từng cột không?
- Mọi hàm feature có thể test độc lập không?
- Có rủi ro data leakage không: split có được thực hiện trước khi fit không?
- Mọi random seed có được set tập trung không?
- Model có expose interface nhất quán không?
- Hyperparameter có được externalize qua config không?
- Artifact model có được đặt tên nhất quán và kèm file metadata không?
- Experiment có được log với data version, config, và metric theo từng split không?
- Có so sánh với baseline không?
- Pipeline có idempotent và resume được không?
- Notebook có được xóa output và secret trước khi commit không?
- Mọi ML test có được triển khai dưới dạng pytest unit test không phụ thuộc hệ thống ngoài không?
- Tín hiệu chất lượng data và model serving có quan sát được trong production không?

---

## 16. Definition of done / Điều kiện hoàn thành

### EN
A data or ML module, pipeline, or model is considered done only if:

- raw data is preserved and schema is validated explicitly
- data types are explicit and missing value policy is documented
- feature engineering functions are isolated, typed, and unit tested
- data leakage is prevented by convention and verified by test
- model exposes a consistent interface with documented input and output contracts
- hyperparameters are externalized and random seeds are controlled
- the model artifact is named correctly and has a companion metadata file
- every training run is logged with data version, config, metrics per split, and a baseline comparison
- pipeline steps are idempotent, resumable, and configuration is externalized
- notebooks follow the naming, structure, and hygiene rules and contain no secrets
- all ML-specific unit tests run through pytest without external dependencies
- production observability covers data quality signals and model serving signals
- the change satisfies the definition of done in `11-Definition_of_done`

### VI
Một module data hoặc ML, pipeline, hoặc model chỉ được coi là done khi:

- raw data được lưu trữ và schema được validate tường minh
- kiểu dữ liệu tường minh và chính sách missing value được tài liệu hóa
- hàm feature engineering được cô lập, có type hint, và được unit test
- data leakage được ngăn bằng quy ước và được xác minh bằng test
- model expose interface nhất quán với contract đầu vào và đầu ra được tài liệu hóa
- hyperparameter được externalize và random seed được kiểm soát
- artifact model được đặt tên đúng và có file metadata đi kèm
- mọi training run được log với data version, config, metric theo từng split, và so sánh baseline
- bước pipeline idempotent, resume được, và cấu hình được externalize
- notebook tuân theo quy tắc đặt tên, cấu trúc, và vệ sinh và không chứa secret
- mọi unit test ML đặc thù chạy qua pytest không phụ thuộc hệ thống ngoài
- observability production bao phủ tín hiệu chất lượng data và model serving
- thay đổi thỏa mãn definition of done trong `11-Definition_of_done`
