import os
from dotenv import load_dotenv

from pyspark.sql import SparkSession, functions as F
from google.oauth2 import service_account
from googleapiclient.discovery import build


load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_GID = os.getenv("SHEET_GID")

if not all([SPREADSHEET_ID, SHEET_GID]):
    raise ValueError("Faltan variables de entorno requeridas")

spark = (
    SparkSession.builder
    .appName("Read Google Sheets with Spark")
    .getOrCreate()
)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

credentials_info = {
    "type": "service_account",
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("SERVICE_ACCOUNT"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('SERVICE_ACCOUNT')}",
}

credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=credentials)

sheet_metadata = service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID
).execute()

sheets = sheet_metadata.get("sheets", [])
sheet_name = None

for sheet in sheets:
    if str(sheet["properties"]["sheetId"]) == SHEET_GID:
        sheet_name = sheet["properties"]["title"]
        break

if not sheet_name:
    raise ValueError("No se encontró el sheet con ese GID")

result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=sheet_name
).execute()

values = result.get("values", [])

if not values:
    raise ValueError("El sheet está vacío")

headers = values[0]
rows = values[1:]


df = spark.createDataFrame(rows, headers).withColumn("ticker", F.concat(F.col("Identificación Mercado"), F.lit(".BA")))


