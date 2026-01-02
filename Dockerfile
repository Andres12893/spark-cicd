FROM apache/airflow:3.1.5

# Cambiamos a root para instalar dependencias del sistema si hace falta
USER root

# (Opcional) Dependencias del sistema, Java para Spark
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Volvemos a airflow
USER airflow

# Copiamos requirements
COPY requirements.txt /requirements.txt

# Instalamos dependencias Python
RUN pip install --no-cache-dir -r /requirements.txt

# Copiamos el código del proyecto
COPY src /opt/airflow/src

# (Opcional) Seteamos PYTHONPATH
ENV PYTHONPATH="/opt/airflow"

WORKDIR /opt/airflow
