# Airflow Standards

Apply these Apache Airflow 3 and Astronomer (Astro CLI) standards whenever authoring DAGs or
working within an Astronomer project (based on
[Astronomer Best Practices](https://docs.astronomer.io/learn/dag-best-practices) and the
[Apache Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)).

General Python style (PEP 8/20/257, naming, type hints, docstrings, exceptions, idioms) is
covered by the parent `../SKILL.md` — read it first. Airflow DAG code additionally follows the
lightweight-architecture guidance in `../references/ddd-clean-architecture.md` (keep DAG files
orchestration-only; extract transformation logic into plain, unit-testable functions).

---

## 1. Guiding Principles

These principles define the philosophy of a robust data orchestration environment:

```
Airflow is an orchestrator, not an execution engine — offload heavy processing to specialized systems (Spark, Snowflake, dbt).
DAGs must be Idempotent — running them multiple times produces the same result as running them once.
Tasks must be Atomic — a single logical unit of work per task.
Tasks must be Deterministic — same inputs always yield the same outputs.
DAGs are configuration as code, not application logic.
Code outside of tasks (top-level code) blocks the scheduler — keep it minimal.
```

---

## 2. Astro Project Structure

When using the Astro CLI (`astro dev init`), leverage the standardized directory layout:

### 2.1 Directory Guidelines

| Directory / File | Purpose | Best Practices |
|---|---|---|
| `dags/` | Directed Acyclic Graph definitions | One DAG per Python file (unless dynamically generated). Avoid placing heavy operational scripts here. |
| `include/` | Supporting files used by tasks | Store SQL scripts, configurations, or data files here. Reference via `template_search_path`. |
| `plugins/` | Custom Airflow plugins | Use for custom UI views or database interactions. Requires restart on change. |
| `tests/` | Unit and integration tests | Test DAG integrity, custom operators, and complex logic (e.g., `pytest`). |
| `Dockerfile` | Defines the Astro Runtime image | Use for OS-level dependencies not covered by `packages.txt`. |
| `packages.txt` | OS-level package dependencies | Keeps `Dockerfile` clean (e.g., `libpq-dev`). |
| `requirements.txt` | Python package dependencies | Pin versions for reproducibility (e.g., `pandas==2.0.0`). |
| `airflow_settings.yaml`| Local Connections/Variables/Pools | Use for local development configuration; don't commit secrets. |

---

## 3. DAG Authoring & Configuration

### 3.1 Avoid Top-Level Code

The Airflow scheduler parses DAG files continuously (every few seconds). **Never** perform database queries, API calls, or heavy computations outside of a task execution context.

```python
# ❌ Wrong — Heavy processing at top-level; blocks the scheduler
import requests
from airflow.decorators import dag, task
from datetime import datetime

users = requests.get("https://api.example.com/users").json() # Bad!

@dag(start_date=datetime(2024, 1, 1), schedule="@daily", catchup=False)
def my_dag():
    @task
    def process_user(user): ...
    
    for user in users:
        process_user(user)

my_dag()

# ✅ Correct — Move external logic inside the task
from airflow.decorators import dag, task
from datetime import datetime

@dag(start_date=datetime(2024, 1, 1), schedule="@daily", catchup=False)
def my_dag():
    @task
    def get_users():
        import requests
        return requests.get("https://api.example.com/users").json()
        
    @task
    def process_users(users): ...
    
    users = get_users()
    process_users(users)

my_dag()
```

### 3.2 Dynamic Context via `kwargs`

Avoid using `datetime.now()` for logic inside tasks. Because tasks can be re-run for past dates, `datetime.now()` breaks idempotency.

```python
# ❌ Wrong — Non-deterministic based on execution time
@task
def extract_data():
    today = datetime.now().strftime("%Y-%m-%d") # Fails on historical backfill
    sql = f"SELECT * FROM sales WHERE date = '{today}'"

# ✅ Correct — Uses Airflow's logical execution environment (`data_interval_start`)
@task
def extract_data(**context):
    logical_date = context["data_interval_start"].strftime("%Y-%m-%d")
    sql = f"SELECT * FROM sales WHERE date = '{logical_date}'"
```

### 3.3 Default Arguments

Use `default_args` to centralize configuration and avoid repetitive task definitions:

```python
# ✅ Correct
from datetime import timedelta
from airflow.decorators import dag, task

default_args = {
    "owner": "data_engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["alerts@company.com"],
}

@dag(
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
)
def etl_pipeline():
    ...
```

### 3.4 Start Dates and Catchup

- Always use a **static `start_date`** (e.g., `datetime(2024, 1, 1)`). Never use `datetime.now()` or relative dates (`days_ago(1)`), as the scheduler evaluates this differently on every parse.
- Always explicitly define **`catchup=False`** unless you intentionally want the scheduler to retroactively execute all runs from the `start_date` to the present.

---

## 4. The TaskFlow API (Airflow 2/3 standard)

Modern Airflow code leverages the TaskFlow API (`@dag` and `@task` decorators), which handles XCom (cross-task communication) and dependencies natively.

### 4.1 Decorator Usage

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(start_date=datetime(2024, 1, 1), schedule="@daily", catchup=False)
def automated_reporting():
    
    @task
    def extract() -> dict:
        return {"total_sales": 5000}
        
    @task
    def transform(data: dict) -> float:
        return data["total_sales"] * 1.05
        
    @task
    def load(final_sales: float):
        print(f"Loading {final_sales} to warehouse.")

    # TaskFlow automatically handles dependencies based on data passage
    raw_data = extract()
    clean_data = transform(raw_data)
    load(clean_data)

automated_reporting()
```

### 4.2 XCom Limitations

- XCom is designed for passing **metadata**, not massive datasets.
- Default XCom stores data in the Airflow Metadata Database. Storing large DataFrames will crash the database.
- For passing large payloads, pass a **reference** (e.g., an S3 URI or a database table name) and let the task retrieve the data, or configure a Custom XCom Backend (e.g., S3/GCS).

---

## 5. Airflow 3 Specific Enhancements

Airflow 3 introduces major architectural shifts that influence DAG authoring:

### 5.1 Event-Driven Scheduling (Data-Aware Scheduling)

Airflow 3.0 renamed **Datasets to Assets** (`airflow.sdk.Asset`; the old `airflow.datasets.Dataset` name remains only as a deprecated alias). Use Assets instead of constant polling (`Sensor` operators) when waiting for data produced by other DAGs.

```python
from airflow.sdk import Asset, dag, task

# Define the asset
s3_sales_data = Asset("s3://bucket/sales/data.csv")

# DAG 1: Produces the asset
@dag(...)
def producer_dag():
    @task(outlets=[s3_sales_data])
    def load_to_s3(): ...

# DAG 2: Triggered by the asset update
@dag(schedule=[s3_sales_data], ...)
def consumer_dag():
    @task
    def analyze_sales(): ...
```

### 5.2 Task Execution API Independence

In Airflow 3, tasks execute remotely (via the Task Execution API) without direct access to the Airflow Metadata Database.

**Best Practice**: Never attempt to query the internal Airflow tables (`dag_run`, `task_instance`) directly from within task code using SQLAlchemy or standard DB connections. Always rely on standard Airflow Context variables (`**context`) or the Task REST API if necessary.

### 5.3 DAG Versioning

Airflow 3 natively tracks DAG versions.

**Best Practice**: Treat your DAG code like a managed software release. Commit changes incrementally, ensure idempotency so historical versions can be reasoned about, and tie CI/CD deployments into your Astronomer platform to leverage native DAG version visualization.

---

## 6. Robustness & Observability

### 6.1 Retries and Fault Tolerance

- Transient failures (API rate limits, brief network outages) are common in distributed systems.
- **Always set retries** globally via `default_args` or locally on specific flaky tasks.
- Use `retry_exponential_backoff` to prevent overwhelming failing services.

### 6.2 Modularity vs. Monoliths

Avoid "God DAGs" with hundreds of tasks.

- If tasks logically belong to different business domains or have drastically different SLA requirements, split them into separate DAGs.
- Use **Assets** (Data-Aware Scheduling) to elegantly stitch multiple separate DAGs together instead of using `TriggerDagRunOperator`.

### 6.3 Task Grouping

Use `@task_group` (TaskFlow) or `TaskGroup` (Classic) to visually organize tasks in the UI, improving readability without creating complex SubDAG architectures (which are deprecated).

```python
from airflow.decorators import task_group

@task_group(group_id="transformation_layer")
def transform_data(raw_data):
    clean = clean_text(raw_data)
    return validate_schema(clean)
```

---

## 7. Testing DAGs and Tasks

### 7.1 Unit Testing Tasks

Test task logic in isolation without spinning up a full Airflow environment:

```python
# ✅ Unit test a TaskFlow function directly
from dags.my_dag import transform_record

def test_transform_record_removes_nulls():
    result = transform_record({"name": "Alice", "email": None})
    assert result == {"name": "Alice"}
    assert "email" not in result

def test_transform_record_raises_on_empty():
    with pytest.raises(ValueError, match="empty record"):
        transform_record({})
```

### 7.2 DAG Integrity Tests

Run these in CI to catch structural issues before deployment:

```python
import pytest
from airflow.models import DagBag

@pytest.fixture(scope="session")
def dagbag():
    return DagBag(dag_folder="dags/", include_examples=False)

def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}, f"DAG import errors: {dagbag.import_errors}"

def test_dag_task_count(dagbag):
    dag = dagbag.get_dag("my_pipeline")
    assert dag is not None
    assert len(dag.tasks) >= 1

def test_dag_has_no_cycles(dagbag):
    # Airflow 3 removed dag.test_cycle(); cycles are detected at parse time and
    # surface as import errors, so a clean load already proves there is no cycle.
    assert dagbag.import_errors == {}
    assert dagbag.get_dag("my_pipeline") is not None

def test_dag_schedule(dagbag):
    dag = dagbag.get_dag("my_pipeline")
    # Airflow 3 removed dag.schedule_interval; inspect the timetable summary instead.
    assert dag.timetable.summary == "@daily"
```

### 7.3 Integration Testing with Mocks

Mock external connections in integration tests to avoid real API calls:

```python
from unittest.mock import patch, MagicMock

def test_extract_task_calls_api(dagbag):
    with patch("dags.my_dag.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"records": [{"id": 1}]}
        )
        from dags.my_dag import extract_data
        result = extract_data.function()
        assert result == [{"id": 1}]
        mock_get.assert_called_once()
```

### 7.4 Astronomer CI Test Job

Include a DAG integrity job in every CI pipeline:

```yaml
# CircleCI example
- run:
    name: Validate DAG syntax and imports
    command: |
      pip install apache-airflow apache-airflow-providers-common-sql
      python -m pytest tests/ -v --tb=short
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| API calls, DB queries, or heavy computation at DAG file top level | Move the logic inside `@task` functions |
| `datetime.now()` for date logic inside tasks | `context["data_interval_start"]` — survives backfills |
| Dynamic `start_date` (`datetime.now()`, `days_ago(1)`) | A static `start_date` such as `datetime(2024, 1, 1)` |
| Leaving `catchup` unset | Explicit `catchup=False` unless retroactive runs are intended |
| Passing large DataFrames through XCom | Pass a reference (S3 URI, table name) or configure a custom XCom backend |
| Airflow executing heavy data processing itself | Offload to specialized systems (Spark, Snowflake, dbt) — Airflow orchestrates |
| Sensors constantly polling for data produced by other DAGs | Assets (data-aware scheduling) |
| `TriggerDagRunOperator` to stitch DAGs together | Assets connecting producer and consumer DAGs |
| "God DAGs" with hundreds of tasks | Split by business domain / SLA into separate DAGs |
| SubDAGs for visual organization | `@task_group` / `TaskGroup` (SubDAGs are deprecated) |
| Querying internal Airflow tables (`dag_run`, `task_instance`) from task code | Airflow context variables (`**context`) or the Task REST API |
| Repeating `retries`/owner/email on every task | Centralize in `default_args` |
| No retries on tasks calling external services | Set `retries` and `retry_delay`; use `retry_exponential_backoff` for flaky services |
| Secrets committed in `airflow_settings.yaml` | Local development configuration only — never commit secrets |

---

## Pre-flight checklist — run before delivering any Airflow DAG

When writing or reviewing Airflow DAGs, verify:

- [ ] **Architecture**: Is Airflow merely orchestrating, or improperly pushing large datasets?
- [ ] **Top-Level Code**: Are API calls or DB queries outside task functions? (They shouldn't be).
- [ ] **Idempotency**: Will the tasks produce duplicate data if re-run for the same logical date?
- [ ] **Date Handling**: Uses `context["data_interval_start"]` instead of `datetime.now()`?
- [ ] **Start Date**: Is `start_date` static? (e.g., `datetime(2024, 1, 1)` not `days_ago(1)`).
- [ ] **Catchup**: Is `catchup=False` explicitly set (unless specifically required)?
- [ ] **TaskFlow API**: Are `@dag` and `@task` decorators utilized where possible?
- [ ] **Retries**: Are sensible `retries` and `retry_delay` configured in `default_args`?
- [ ] **Structure**: Is the code housed cleanly in `dags/` with SQL queries delegated to `include/`?
- [ ] **XCom Payloads**: Are we passing references to large files/tables, rather than the data itself?
- [ ] **Modern Triggers**: Is the DAG using Assets instead of Sensors where cross-DAG triggers are needed?
- [ ] **Tests**: Are there DAG integrity tests (import errors, cycle check) running in CI?
- [ ] **Task Unit Tests**: Is business logic in task functions covered by pytest unit tests?
