FROM python:3.12-slim
WORKDIR /app
COPY simulate.py .
ENTRYPOINT ["python", "simulate.py"]
CMD ["--rps", "10", "--duration", "60"]
