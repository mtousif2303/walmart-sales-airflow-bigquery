from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}

with DAG(
    'walmart_sales_etl_gcs',
    default_args=default_args,
    description='ETL pipeline for Walmart sales data from GCS',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # Task 1: Create BigQuery Dataset if it doesn't exist
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id='create_dataset',
        dataset_id='walmart_dwh',
        location='US',
        exists_ok=True
    )

    # Task 2: Create BigQuery Tables using BigQueryInsertJobOperator
    create_merchants_table = BigQueryInsertJobOperator(
        task_id='create_merchants_table',
        configuration={
            "query": {
                "query": """
                    CREATE TABLE IF NOT EXISTS `project-040088dd-8c9a-464e-96f.walmart_dwh.merchants_tb` (
                        merchant_id STRING NOT NULL,
                        merchant_name STRING,
                        merchant_category STRING,
                        merchant_country STRING,
                        last_update TIMESTAMP
                    )
                """,
                "useLegacySql": False
            }
        }
    )

    create_walmart_sales_table = BigQueryInsertJobOperator(
        task_id='create_walmart_sales_table',
        configuration={
            "query": {
                "query": """
                    CREATE TABLE IF NOT EXISTS `project-040088dd-8c9a-464e-96f.walmart_dwh.walmart_sales_stage` (
                        sale_id STRING NOT NULL,
                        sale_date DATE,
                        product_id STRING,
                        quantity_sold INT64,
                        total_sale_amount FLOAT64,
                        merchant_id STRING,
                        last_update TIMESTAMP
                    )
                """,
                "useLegacySql": False
            }
        }
    )

    create_target_table = BigQueryInsertJobOperator(
        task_id='create_target_table',
        configuration={
            "query": {
                "query": """
                    CREATE TABLE IF NOT EXISTS `project-040088dd-8c9a-464e-96f.walmart_dwh.walmart_sales_tgt` (
                        sale_id STRING NOT NULL,
                        sale_date DATE,
                        product_id STRING,
                        quantity_sold INT64,
                        total_sale_amount FLOAT64,
                        merchant_id STRING,
                        merchant_name STRING,
                        merchant_category STRING,
                        merchant_country STRING,
                        last_update TIMESTAMP
                    )
                """,
                "useLegacySql": False
            }
        }
    )

    # Task 3: Load data from GCS to BigQuery
    with TaskGroup("load_data") as load_data:

        gcs_to_bq_merchants = GCSToBigQueryOperator(
            task_id='gcs_to_bq_merchants',
            bucket='bigquery_projects_de',
            source_objects=['walmart_ingestion/merchants/merchants_1.json'],
            destination_project_dataset_table='project-040088dd-8c9a-464e-96f.walmart_dwh.merchants_tb',
            write_disposition='WRITE_TRUNCATE',
            source_format='NEWLINE_DELIMITED_JSON',
        )

        gcs_to_bq_walmart_sales = GCSToBigQueryOperator(
            task_id='gcs_to_bq_walmart_sales',
            bucket='bigquery_projects_de',
            source_objects=['walmart_ingestion/sales/walmart_sales_1.json'],
            destination_project_dataset_table='project-040088dd-8c9a-464e-96f.walmart_dwh.walmart_sales_stage',
            write_disposition='WRITE_TRUNCATE',
            source_format='NEWLINE_DELIMITED_JSON',
        )

    # Task 4: Perform UPSERT using MERGE Query
    merge_walmart_sales = BigQueryInsertJobOperator(
        task_id='merge_walmart_sales',
        configuration={
            "query": {
                "query": """
                    MERGE `project-040088dd-8c9a-464e-96f.walmart_dwh.walmart_sales_tgt` T
                    USING (
                      SELECT 
                        S.sale_id, 
                        S.sale_date, 
                        S.product_id, 
                        S.quantity_sold, 
                        S.total_sale_amount, 
                        S.merchant_id, 
                        M.merchant_name, 
                        M.merchant_category, 
                        M.merchant_country,
                        CURRENT_TIMESTAMP() as last_update
                      FROM `project-040088dd-8c9a-464e-96f.walmart_dwh.walmart_sales_stage` S
                      LEFT JOIN `project-040088dd-8c9a-464e-96f.walmart_dwh.merchants_tb` M
                      ON S.merchant_id = M.merchant_id
                    ) S
                    ON T.sale_id = S.sale_id
                    WHEN MATCHED THEN 
                      UPDATE SET
                        T.sale_date = S.sale_date,
                        T.product_id = S.product_id,
                        T.quantity_sold = S.quantity_sold,
                        T.total_sale_amount = S.total_sale_amount,
                        T.merchant_id = S.merchant_id,
                        T.merchant_name = S.merchant_name,
                        T.merchant_category = S.merchant_category,
                        T.merchant_country = S.merchant_country,
                        T.last_update = S.last_update
                    WHEN NOT MATCHED THEN 
                      INSERT (
                        sale_id, sale_date, product_id, quantity_sold, total_sale_amount, 
                        merchant_id, merchant_name, merchant_category, merchant_country, last_update
                      )
                      VALUES (
                        S.sale_id, S.sale_date, S.product_id, S.quantity_sold, S.total_sale_amount, 
                        S.merchant_id, S.merchant_name, S.merchant_category, S.merchant_country, S.last_update
                      )
                """,
                "useLegacySql": False
            }
        }
    )

    # Define Task Dependencies
    create_dataset >> [create_merchants_table, create_walmart_sales_table, create_target_table] >> load_data
    load_data >> merge_walmart_sales