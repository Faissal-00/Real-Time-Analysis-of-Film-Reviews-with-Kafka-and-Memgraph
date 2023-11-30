from confluent_kafka import Consumer
from py2neo import Graph, Node, Relationship
import json
import time

# Set up Kafka Consumer
conf = {
    'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker's address
    'group.id': 'movies_data_consumer',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['movies'])

def write_into_memgraph(data):
    # Connect to Memgraph
    graph = Graph("bolt://localhost:7687")

    # Extract data from the data
    user_id = data["userId"]
    movie_id = data["movie"]["movieId"]
    movie_title = data["movie"]["title"]
    genres = data["movie"]["genres"]
    rating_value = int(data["rating"])
    timestamp = data["timestamp"]

    # Create User node if it doesn't exist
    user_node = graph.nodes.match("User", user_id=user_id).first()
    if not user_node:
        user_node = Node("User", user_id=user_id)
        graph.create(user_node)

    # Create Movie node if it doesn't exist
    movie_node = graph.nodes.match("Movie", movie_id=movie_id).first()
    if not movie_node:
        movie_node = Node("Movie", movie_id=movie_id, title=movie_title, average_rating=0, count_ratings=0)
        graph.create(movie_node)

    # Get or create the relationship between the user and the movie
    relationship = graph.match((user_node, movie_node), "RATED").first()
    if not relationship:
        relationship = Relationship(user_node, "RATED", movie_node)
        graph.create(relationship)

    # Update the rating attribute in the relationship
    relationship["rating"] = rating_value
    graph.push(relationship)

    # Update average rating and count ratings in the movie_node
    current_average_rating = int(movie_node["average_rating"])
    current_count_ratings = int(movie_node["count_ratings"])

    new_average_rating = (current_average_rating * current_count_ratings + rating_value) / (current_count_ratings + 1)
    new_count_ratings = current_count_ratings + 1

    movie_node["average_rating"] = new_average_rating
    movie_node["count_ratings"] = new_count_ratings

    graph.push(movie_node)

    # Create Category nodes and BELONGS_TO relationships
    for genre in genres:
        category_node = graph.nodes.match("Category", name=genre).first()
        if not category_node:
            category_node = Node("Category", name=genre)
            graph.create(category_node)
        graph.merge(Relationship(movie_node, "BELONGS_TO", category_node))

    return f'Wrote rating {rating_value} for movie {movie_title} by user {user_id} into Memgraph.'

try:
    while True:
        msg = consumer.poll(1.0)  # Wait for 1 second for new messages
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        # into a python dictionary
        # data = json.loads(msg.value().decode('utf-8'))
        data_string = msg.value().decode('utf-8')
        # Replace single quotes with double quotes to make it a valid JSON string
        json_string = data_string.replace("'", "\"")
        # Convert the JSON string to a Python dictionary
        try:
            data_dict = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            continue
        # Write data into Memgraph
        print("Writing data into Memgraph...")
        time.sleep(1)
        print(write_into_memgraph(data_dict))
except KeyboardInterrupt:
    pass
finally:
    # Close Kafka consumer
    consumer.close()