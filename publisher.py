import pika
from config import rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password

def publish_message_to_queue(customer_id, recommended_food):
    # Establish connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_username, rabbitmq_password)))
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue='recommendation_queue')

    # Prepare message
    message = f'Customer ID: {customer_id}, Recommended Food: {recommended_food}'

    # Publish message to queue
    channel.basic_publish(exchange='', routing_key='recommendation_queue', body=message)

    # Close connection
    connection.close()
