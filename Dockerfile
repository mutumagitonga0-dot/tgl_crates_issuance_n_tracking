FROM python:3.11-slim

# Install prerequisites
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https unixodbc-dev gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Add Microsoft repo for ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list

# Install msodbcsql17
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
