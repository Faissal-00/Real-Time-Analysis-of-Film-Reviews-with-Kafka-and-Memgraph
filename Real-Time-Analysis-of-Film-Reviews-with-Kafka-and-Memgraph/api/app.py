from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pandas as pd

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["100000 per day", "4167 per hour"])

def read_data_files():
    # Read data from CSV files and return DataFrames
    u_data = pd.read_csv('C:/Users/YouCode/Desktop/saad/2023-11-15_Kafka_Memegraph_Neo4j_Movies_Recommendation/Live_Movies_Analysis_Kafka_And_Memgraph/api/data/u.data', sep='\t', names=['userId', 'movieId', 'rating', 'timestamp'])
    u_item = pd.read_csv('C:/Users/YouCode/Desktop/saad/2023-11-15_Kafka_Memegraph_Neo4j_Movies_Recommendation/Live_Movies_Analysis_Kafka_And_Memgraph/api/data/u.item', sep='|', encoding='latin-1', header=None, names=['movieId', 'title', 'release_date', 'video_release_date', 'IMDb_URL', 'unknown', 'Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'])
    u_user = pd.read_csv('C:/Users/YouCode/Desktop/saad/2023-11-15_Kafka_Memegraph_Neo4j_Movies_Recommendation/Live_Movies_Analysis_Kafka_And_Memgraph/api/data/u.user', sep='|', names=['userId', 'age', 'gender', 'occupation', 'zipcode'])
    return u_data, u_item, u_user

def extract_genres(row):
    # Extract genres for each movie
    genres = ['unknown', 'Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
    movie_genres = [genre for genre, val in zip(genres, row[5:]) if val == 1]
    return movie_genres

def create_modified_json_entry(row):
    # Create JSON entry for each row in the DataFrame
    movie_info = {
        "movieId": str(row['movieId']),
        "title": row['title'],
        "genres": row['genres']
    }
    return {
        "userId": str(row['userId']),
        "movie": movie_info,
        "rating": str(row['rating']),
        "timestamp": str(row['timestamp'])
    }

def paginate_data(data, page_number, per_page):
    # Paginate the data based on page number and items per page
    start = (page_number - 1) * per_page
    end = start + per_page
    return data[start:end]

@app.route('/movies/page<int:page_number>', methods=['GET'])
@limiter.limit("70 per minute")
def get_movie_data(page_number):
    u_data, u_item, u_user = read_data_files()

    u_item['genres'] = u_item.apply(extract_genres, axis=1)

    merged_data = pd.merge(u_data, u_item[['movieId', 'title', 'genres']], on='movieId')
    merged_data = pd.merge(merged_data, u_user[['userId', 'age', 'gender', 'occupation']], on='userId')

    total_items = len(merged_data)
    per_page = int(request.args.get('per_page', 10))  # Get items per page, default to 1000

    total_pages = total_items // per_page + (total_items % per_page > 0)  # Calculate total pages

    if page_number > total_pages:
        return jsonify({'message': f'There are only {total_pages} pages available.'}), 404

    json_data = merged_data.apply(create_modified_json_entry, axis=1).tolist()

    paginated_data = paginate_data(json_data, page_number, per_page)

    return jsonify({
        "page": page_number,
        "total_pages": total_pages,
        "results": paginated_data
    })

if __name__ == '__main__':
    app.run(debug=True)