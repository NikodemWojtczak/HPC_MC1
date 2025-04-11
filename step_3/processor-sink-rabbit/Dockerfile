FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY processor_sink_rabbit.py ./

# Set default RabbitMQ host, can be overridden by docker-compose environment
ENV RABBITMQ_HOST=rabbitmq1
ENV RABBITMQ_USER=user
ENV RABBITMQ_PASS=password

CMD ["python", "processor_sink_rabbit.py"]