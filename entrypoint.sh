#!/bin/sh

echo "Waiting for MySQL..."

until nc -z mysql-db 3306
do
  echo "MySQL not ready yet..."
  sleep 2
done

echo "MySQL is ready!"

echo "Creating tables..."
python -m app.init_db

echo "Starting FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 3000