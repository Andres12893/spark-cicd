import yaml
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


@pytest.fixture(scope="session")
def spark():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("pytest-spark-schema")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def expected_schema():
    with open("tests/cedears_schema.yml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cedears_df(spark):
    data = [
        (
            "APPLE INC.",
            "AAPL",
            "20:1",
            "1,799,612,000.00",
            "NASDAQ GS",
            "Common Stock",
            "Quarter",
            "Estados Unidos",
            "Technology",
            "Technology Hardware",
            "AAPL.BA",
        )
    ]

    columns = [
        "DENOMINACION DEL PROGRAMA CEDEAR",
        "Identificación Mercado",
        "Ratio Cedear/Acción ó ADR",
        "Montos Máximos",
        "Mercado de Negociación",
        "Valor Subyacente",
        "Frecuencia de Pago",
        "País de Origen",
        "Industria",
        "Descripción de la Industria",
        "ticker",
    ]

    return spark.createDataFrame(data, columns)


def test_dataframe_schema(cedears_df, expected_schema):
    df_columns = cedears_df.columns
    schema_columns = expected_schema["columns"]

    # -----------------------
    # Column existence
    # -----------------------
    for col_def in schema_columns:
        assert col_def["name"] in df_columns, f"Missing column: {col_def['name']}"

    # -----------------------
    # Nullable checks
    # -----------------------
    for col_def in schema_columns:
        if not col_def.get("nullable", True):
            null_count = cedears_df.filter(col(col_def["name"]).isNull()).count()
            assert null_count == 0, f"Column {col_def['name']} contains NULLs"

    # -----------------------
    # Custom rules
    # -----------------------
    for col_def in schema_columns:
        rules = col_def.get("rules", {})
        col_name = col_def["name"]

        if "ends_with" in rules:
            invalid = (
                cedears_df
                .filter(~col(col_name).endswith(rules["ends_with"]))
                .count()
            )
            assert invalid == 0, f"Column {col_name} does not end with {rules['ends_with']}"
