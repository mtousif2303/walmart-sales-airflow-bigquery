# walmart-sales-airflow-bigquery Data Pipeline

A production-ready, automated ETL pipeline that orchestrates Walmart sales data from Google Cloud Storage to BigQuery using Apache Airflow. This pipeline implements best practices for data warehousing, including staging tables, dimensional modeling, and incremental UPSERT operations.

This project demonstrates a **modern data engineering solution** for processing retail sales data at scale. It automates the extraction, transformation, and loading (ETL) of Walmart sales transactions and merchant information, making the data readily available for business intelligence and analytics.


## 🏗️ Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Google Cloud Storage                         │
│  Bucket: bigquery_projects                                       │
│                                                                   │
│  ├── walmart_ingestion/merchants/merchants_1.json                │
│  └── walmart_ingestion/sales/walmart_sales_1.json                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Extract (GCSToBigQueryOperator)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Apache Airflow                              │
│  Environment: Cloud Composer / Self-hosted                       │
│                                                                   │
│  DAG: walmart_sales_etl_gcs                                      │
│  Schedule: @daily (Every 24 hours)                               │
│  Retries: 1                                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Load & Transform
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google BigQuery                             │
│  Project: project-040088dd-8c9a-464e-96f.walmart_dwh.merchants_tb                              │
│  Dataset: walmart_dwh                                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Staging Layer                               │    │
│  │  ├── merchants_tb (Dimension Table)                      │    │
│  │  └── walmart_sales_stage (Staging Table)                 │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                         │
│                         │ MERGE (UPSERT Operation)                │
│                         ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Production/Analytics Layer                     │    │
│  │  └── walmart_sales_tgt (Fact Table - Enriched)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Consume
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Analytics & BI Tools                                │
│  • Looker Studio  • Tableau  • Power BI  • Custom Apps          │
└─────────────────────────────────────────────────────────────────┘
```

a) The Airflow DAG Job

<img width="3022" height="1728" alt="image" src="https://github.com/user-attachments/assets/1b3b94c5-66f3-48c9-b3cd-225c3b6e60c1" />

b) The GCS buckets to upload the DAG

<img width="3108" height="1656" alt="image" src="https://github.com/user-attachments/assets/cb6f3f6b-6d9f-4fab-92e7-3817c4d36188" />

c) The Buckets sample data stored in GCS buckets

<img width="2962" height="1580" alt="image" src="https://github.com/user-attachments/assets/dc646a3d-f836-47e7-9f33-059be4b6d840" />

d) The BigQuery data warehoue where data is merged and upserted

<img width="3094" height="1784" alt="image" src="https://github.com/user-attachments/assets/892fbeaf-0472-431f-8f76-1baa440e22b1" />



## 🔄 Pipeline Workflow

### DAG Execution Flow

```
Start
  │
  ▼
┌──────────────────────┐
│  create_dataset      │  Creates BigQuery dataset 'walmart_dwh'
│  (if not exists)     │  Location: US
└──────────┬───────────┘
           │
           ▼
     ┌────────────┐
     │  Parallel  │
     │ Execution  │
     └────────────┘
           │
     ┌─────┴─────┬─────────────────┬───────────────────┐
     │           │                 │                   │
     ▼           ▼                 ▼                   ▼
┌─────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────────┐
│ create_ │ │ create_ │ │  create_     │ │              │
│merchants│ │walmart_ │ │  target_     │ │              │
│ _table  │ │sales_   │ │  table       │ │              │
│         │ │ table   │ │              │ │              │
└────┬────┘ └────┬────┘ └──────┬───────┘ └──────────────┘
     │           │              │
     └───────────┴──────────────┘
                 │
                 ▼
        ┌────────────────┐
        │   load_data    │  Task Group
        │   (Parallel)   │
        └────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
┌──────────────┐  ┌──────────────┐
│gcs_to_bq_    │  │gcs_to_bq_    │
│merchants     │  │walmart_sales │
│              │  │              │
│ GCS → BQ     │  │ GCS → BQ     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
   ┌────────────────────────┐
   │ merge_walmart_sales    │  UPSERT Operation
   │                        │
   │ • Join sales + merchant│
   │ • UPDATE if exists     │
   │ • INSERT if new        │
   └────────────────────────┘
                │
                ▼
              End
```

### Data Flow

1. **Source**: JSON files stored in GCS bucket (`bigquery_projects`)
2. **Ingestion**: Airflow operators extract data from GCS
3. **Staging**: Data loaded into BigQuery staging tables
4. **Transformation**: SQL MERGE operation joins and enriches data
5. **Target**: Final enriched dataset in `walmart_sales_tgt` table
6. **Consumption**: BI tools query BigQuery for analytics

---


## 🛠️ Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Orchestration** | Apache Airflow | 2.8+ | Workflow management |
| **Data Lake** | Google Cloud Storage | - | Raw data storage |
| **Data Warehouse** | Google BigQuery | - | Analytics database |
| **Language** | Python | 3.11+ | Pipeline development |
| **Provider** | airflow-providers-google | 10.0+ | GCP integration |
| **Format** | JSON (NDJSON) | - | Data serialization |
| **Version Control** | Git | - | Code management |

---

## 📁 Project Structure

```
walmart-sales-data-pipeline/
│
├── dags/
│   ├── airflow_bigquery_dag.py          # Main DAG definition
│   └── config/
│       └── dag_config.py                # Configuration parameters
│
├── data/
│   ├── sample/
│   │   ├── merchants_1.json             # Sample merchant data
│   │   └── walmart_sales_1.json         # Sample sales data
│   └── schema/
│       ├── merchants_schema.json        # BigQuery schema for merchants
│       └── sales_schema.json            # BigQuery schema for sales
│
├── sql/
│   ├── create_tables.sql                # DDL statements
│   └── merge_sales.sql                  # MERGE query
│
├── docs/
│   ├── architecture.md                  # Detailed architecture docs
│   ├── setup_guide.md                   # Setup instructions
│   └── troubleshooting.md               # Common issues
│
├── tests/
│   ├── test_dag_validation.py           # DAG validation tests
│   └── test_data_quality.py             # Data quality tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                       # CI/CD pipeline
│
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python dependencies
├── README.md                            # This file
└── LICENSE                              # MIT License
```

---

## 📊 Data Model

### Entity Relationship Diagram

```
┌─────────────────────────┐
│     merchants_tb        │
│   (Dimension Table)     │
├─────────────────────────┤
│ PK merchant_id          │◄─────┐
│    merchant_name        │      │
│    merchant_category    │      │
│    merchant_country     │      │
│    last_update          │      │
└─────────────────────────┘      │
                                  │
                                  │ LEFT JOIN
                                  │
┌─────────────────────────┐      │
│  walmart_sales_tgt      │      │
│     (Fact Table)        │      │
├─────────────────────────┤      │
│ PK sale_id              │      │
│    sale_date            │      │
│    product_id           │      │
│    quantity_sold        │      │
│    total_sale_amount    │      │
│ FK merchant_id          │──────┘
│    merchant_name        │ (Enriched)
│    merchant_category    │ (Enriched)
│    merchant_country     │ (Enriched)
│    last_update          │
└─────────────────────────┘
```

### Table Schemas

#### 1. merchants_tb (Dimension Table)

Stores merchant master data with business context.

| Column Name | Data Type | Mode | Description |
|------------|-----------|------|-------------|
| `merchant_id` | STRING | REQUIRED | Unique identifier for merchant (Primary Key) |
| `merchant_name` | STRING | NULLABLE | Business name of the merchant |
| `merchant_category` | STRING | NULLABLE | Business category (e.g., Electronics, Grocery) |
| `merchant_country` | STRING | NULLABLE | Country of merchant operation |
| `last_update` | TIMESTAMP | NULLABLE | Last modified timestamp for tracking changes |

**Sample Data:**
```json
{
  "merchant_id": "M001",
  "merchant_name": "Tech Solutions Inc",
  "merchant_category": "Electronics",
  "merchant_country": "USA",
  "last_update": "2026-01-17T08:47:30Z"
}
```

#### 2. walmart_sales_stage (Staging Table)

Temporary staging area for incoming sales transactions.

| Column Name | Data Type | Mode | Description |
|------------|-----------|------|-------------|
| `sale_id` | STRING | REQUIRED | Unique transaction identifier (Primary Key) |
| `sale_date` | DATE | NULLABLE | Date of the sale transaction |
| `product_id` | STRING | NULLABLE | Product SKU or identifier |
| `quantity_sold` | INT64 | NULLABLE | Number of units sold |
| `total_sale_amount` | FLOAT64 | NULLABLE | Total transaction value in USD |
| `merchant_id` | STRING | NULLABLE | Foreign key to merchants table |
| `last_update` | TIMESTAMP | NULLABLE | Record load timestamp |

#### 3. walmart_sales_tgt (Target/Fact Table)

Production table with enriched sales data joined with merchant information.

| Column Name | Data Type | Mode | Description |
|------------|-----------|------|-------------|
| `sale_id` | STRING | REQUIRED | Unique transaction identifier (Primary Key) |
| `sale_date` | DATE | NULLABLE | Date of the sale transaction |
| `product_id` | STRING | NULLABLE | Product SKU or identifier |
| `quantity_sold` | INT64 | NULLABLE | Number of units sold |
| `total_sale_amount` | FLOAT64 | NULLABLE | Total transaction value in USD |
| `merchant_id` | STRING | NULLABLE | Foreign key to merchants table |
| `merchant_name` | STRING | NULLABLE | **Enriched** - Merchant business name |
| `merchant_category` | STRING | NULLABLE | **Enriched** - Merchant category |
| `merchant_country` | STRING | NULLABLE | **Enriched** - Merchant country |
| `last_update` | TIMESTAMP | NULLABLE | Last update timestamp for audit |

**Sample Enriched Record:**
```json
{
  "sale_id": "S12345",
  "sale_date": "2026-01-17",
  "product_id": "P789",
  "quantity_sold": 5,
  "total_sale_amount": 499.99,
  "merchant_id": "M001",
  "merchant_name": "Tech Solutions Inc",
  "merchant_category": "Electronics",
  "merchant_country": "USA",
  "last_update": "2026-01-17T08:47:30Z"
}
```

---


### Task Details

#### Phase 1: Infrastructure Setup
- **Duration**: ~30 seconds
- **Tasks**: 4 parallel tasks
- Creates dataset and all required tables with proper schemas

#### Phase 2: Data Loading
- **Duration**: ~2-5 minutes (depends on data volume)
- **Tasks**: 2 parallel tasks in `load_data` task group
- Loads JSON data from GCS to BigQuery staging tables
- Uses `WRITE_TRUNCATE` for full refresh

#### Phase 3: Transformation
- **Duration**: ~1-2 minutes
- **Task**: Single MERGE operation
- Enriches sales data with merchant information
- Performs UPSERT (UPDATE existing, INSERT new records)

### Scheduling

```python
Schedule: @daily (00:00 UTC)
Start Date: days_ago(1)
Catchup: False
Retries: 1
Retry Delay: 5 minutes (default)
```

---

## 📋 Prerequisites

### Required Accounts & Access

1. **Google Cloud Platform Account**
   - Active GCP project with billing enabled
   - BigQuery API enabled
   - Cloud Storage API enabled
   - Appropriate IAM permissions

2. **Required IAM Roles**
   ```
   - BigQuery Data Editor
   - BigQuery Job User
   - Storage Object Viewer
   - Storage Object Creator (for logs)
   ```

3. **Apache Airflow Environment**
   - Self-hosted Airflow 2.8+ OR
   - Google Cloud Composer environment

### System Requirements

- **Python**: 3.11 or higher
- **Memory**: Minimum 4GB RAM for Airflow
- **Storage**: 10GB for logs and temporary files
- **Network**: Stable internet connection for GCP API calls

### Software Dependencies

```bash
apache-airflow>=2.8.0
apache-airflow-providers-google>=10.0.0
google-cloud-bigquery>=3.11.0
google-cloud-storage>=2.10.0
```

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/walmart-sales-data-pipeline.git
cd walmart-sales-data-pipeline
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Up GCP Credentials

```bash
# Export service account key path
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Or for Cloud Composer, upload the key via UI
```

### Step 5: Configure Airflow Connection

#### Option A: Using Airflow UI
1. Navigate to Admin → Connections
2. Create new connection:
   - Connection Id: `google_cloud_default`
   - Connection Type: `Google Cloud`
   - Keyfile Path: `/path/to/service-account-key.json`

#### Option B: Using CLI
```bash
airflow connections add 'google_cloud_default' \
    --conn-type 'google_cloud_platform' \
    --conn-extra '{"extra__google_cloud_platform__keyfile_path": "/path/to/key.json"}'
```

---

## ⚙️ Configuration

### Update Project-Specific Variables

Edit `dags/airflow_bigquery_dag.py`:

```python
# Replace with your GCP project ID
PROJECT_ID = "your-project-id"

# Replace with your GCS bucket name
GCS_BUCKET = "your-bucket-name"

# Update dataset location if needed
LOCATION = "US"  # or "EU", "asia-east1", etc.

# Update file paths in GCS
MERCHANTS_FILE = "walmart_ingestion/merchants/merchants_1.json"
SALES_FILE = "walmart_ingestion/sales/walmart_sales_1.json"
```

### Environment Variables

Create `.env` file (optional):

```bash
AIRFLOW__CORE__DAGS_FOLDER=/path/to/dags
AIRFLOW__CORE__LOAD_EXAMPLES=False
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GCP_PROJECT_ID=your-project-id
```

---

## 💻 Usage

### Running the Pipeline

#### 1. Start Airflow (Local Development)

```bash
# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start webserver
airflow webserver --port 8080

# In another terminal, start scheduler
airflow scheduler
```

#### 2. Access Airflow UI

Open browser: `http://localhost:8080`

#### 3. Enable and Trigger DAG

```bash
# Enable DAG
airflow dags unpause walmart_sales_etl_gcs

# Trigger manual run
airflow dags trigger walmart_sales_etl_gcs

# Trigger with specific execution date
airflow dags trigger walmart_sales_etl_gcs --exec-date 2026-01-17
```

#### 4. Monitor Execution

```bash
# Check DAG status
airflow dags list

# View task instances
airflow tasks list walmart_sales_etl_gcs

# Check logs
airflow tasks logs walmart_sales_etl_gcs merge_walmart_sales 2026-01-17
```

### Querying the Data

```sql
-- View enriched sales data
SELECT 
  sale_date,
  merchant_name,
  merchant_category,
  COUNT(*) as total_transactions,
  SUM(total_sale_amount) as total_revenue,
  SUM(quantity_sold) as total_units
FROM `mindful-pillar-426308-k1.walmart_dwh.walmart_sales_tgt`
GROUP BY sale_date, merchant_name, merchant_category
ORDER BY sale_date DESC;

-- Top performing merchants
SELECT 
  merchant_name,
  merchant_category,
  SUM(total_sale_amount) as revenue
FROM `mindful-pillar-426308-k1.walmart_dwh.walmart_sales_tgt`
WHERE sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY merchant_name, merchant_category
ORDER BY revenue DESC
LIMIT 10;
```

---

## 📈 Monitoring

### Key Metrics to Track

1. **DAG Success Rate**: Should be > 95%
2. **Average Run Duration**: Baseline ~5-10 minutes
3. **Data Freshness**: Last load timestamp
4. **Row Counts**: Compare source vs target
5. **Error Rate**: Task failures and retries

### Airflow Alerts

Configure email alerts in `airflow.cfg`:

```ini
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your-email@gmail.com
smtp_password = your-app-password
smtp_port = 587
smtp_mail_from = airflow@example.com
```

Update DAG for email alerts:

```python
default_args = {
    'owner': 'airflow',
    'email': ['data-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Error: Cannot import BigQueryCreateEmptyTableOperator

**Solution**: Use `BigQueryInsertJobOperator` instead (already fixed in current version)

#### 2. Permission Denied Errors

```
Error: 403 Permission denied on BigQuery dataset
```

**Solution**: 
- Verify service account has `BigQuery Data Editor` role
- Check dataset location matches configuration
- Ensure billing is enabled on GCP project

#### 3. GCS File Not Found

```
Error: 404 Object not found: gs://bucket/path/file.json
```

**Solution**:
- Verify file path in GCS bucket
- Check bucket permissions
- Ensure service account has `Storage Object Viewer` role

#### 4. DAG Import Errors

**Solution**:
```bash
# Test DAG syntax
python dags/airflow_bigquery_dag.py

# Check Airflow can parse DAG
airflow dags list-import-errors
```

#### 5. Connection Timeout

**Solution**:
- Check network connectivity to GCP
- Verify firewall rules
- Increase timeout in operator parameters

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
   ```bash
   git commit -m "Add: feature description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Code Standards

- Follow PEP 8 style guide
- Add docstrings to functions
- Include unit tests for new features
- Update documentation as needed

### Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs/screenshots

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 👥 Authors & Acknowledgments

**Author**: Your Name  
**Email**: your-email@example.com  
**LinkedIn**: [Your Profile](https://linkedin.com/in/yourprofile)  
**GitHub**: [@yourusername](https://github.com/yourusername)

### Acknowledgments

- Apache Airflow community for excellent documentation
- Google Cloud Platform for reliable infrastructure
- Walmart (for the use case inspiration)

---

## 📚 Additional Resources

### Documentation
- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [GCS Documentation](https://cloud.google.com/storage/docs)
- [Cloud Composer Guide](https://cloud.google.com/composer/docs)

### Tutorials
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [Data Pipeline Patterns](https://cloud.google.com/architecture/data-lifecycle-cloud-platform)

### Community
- [Airflow Slack Channel](https://apache-airflow.slack.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/apache-airflow)
- [GCP Community](https://www.googlecloudcommunity.com/)

---

## 🗺️ Roadmap

### Planned Features

- [ ] Add data quality checks with Great Expectations
- [ ] Implement CDC (Change Data Capture) for incremental loads
- [ ] Add dbt for transformation layer
- [ ] Create Looker Studio dashboard
- [ ] Add CI/CD pipeline with GitHub Actions
- [ ] Implement data cataloging with DataHub
- [ ] Add monitoring with Datadog/Prometheus
- [ ] Partition tables by date for better performance
- [ ] Add unit tests and integration tests
- [ ] Create Terraform scripts for infrastructure

---


### Business Use Cases

- **Sales Analytics**: Track daily sales performance across merchants and products
- **Merchant Intelligence**: Analyze merchant performance by category and geography
- **Data Warehousing**: Centralized data repository for reporting and dashboards
- **Real-time Updates**: Daily incremental loads ensure data freshness
- **Historical Tracking**: Maintains audit trail with `last_update` timestamps

---

## ✨ Features

### Core Capabilities

- ✅ **Automated Orchestration**: Scheduled daily execution with Apache Airflow
- ✅ **Idempotent Operations**: Safe re-runs with `CREATE IF NOT EXISTS` and `WRITE_TRUNCATE`
- ✅ **Incremental Loading**: UPSERT logic for efficient data updates
- ✅ **Data Enrichment**: Automatic joining of sales with merchant dimensional data
- ✅ **Error Handling**: Configurable retries and failure notifications
- ✅ **Scalability**: Handles growing data volumes with GCS and BigQuery
- ✅ **Task Grouping**: Organized workflow with logical task groups
- ✅ **Audit Trail**: Timestamp tracking for data lineage

### Technical Highlights

- **Declarative Pipeline**: Infrastructure as Code (IaC) approach
- **Cloud-Native**: Fully serverless architecture on GCP
- **Version Control**: Git-based deployment and rollback
- **Modular Design**: Reusable components and operators
- **Standard SQL**: BigQuery Standard SQL for transformations

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/yourusername/walmart-sales-data-pipeline/issues)
3. Create a [new issue](https://github.com/yourusername/walmart-sales-data-pipeline/issues/new) with details
4. Contact: your-email@example.com

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ for the data engineering community

[Report Bug](https://github.com/yourusername/walmart-sales-data-pipeline/issues) · [Request Feature](https://github.com/yourusername/walmart-sales-data-pipeline/issues)

</div>
