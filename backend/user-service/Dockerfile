FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt] motor pymongo
EXPOSE 8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
