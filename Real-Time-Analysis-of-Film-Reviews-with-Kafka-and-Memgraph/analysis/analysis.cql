---------------------------------------------------------------------------
// General Analysis
---------------------------------------------------------------------------

// Get all nodes
MATCH p=(n)-[r]-(m)
RETURN p;

// Count of nodes for each node pattern
MATCH (n)
RETURN labels(n)[0] AS nodeLabels, COUNT(n) AS nodeCount;

// Count of relationships for each relationship pattern
MATCH ()-[r]->()
RETURN type(r) AS relationshipType, COUNT(r) AS relationshipCount;

---------------------------------------------------------------------------
// Category Analysis
---------------------------------------------------------------------------

// Get all categories names
MATCH (category:Category)
RETURN category.name;

// Get categories with highest movie count (most popular categories)
MATCH (category:Category)<-[:BELONGS_TO]-(movie:Movie)
WITH category, COUNT(movie) AS movieCount
ORDER BY movieCount DESC
LIMIT 10
RETURN category.name, movieCount;

// Get categories with highest average movie rating (best categories)
MATCH (category:Category)<-[:BELONGS_TO]-(movie:Movie)
WITH category, AVG(movie.average_rating) AS averageCategoryRating
ORDER BY averageCategoryRating DESC
LIMIT 10
RETURN category.name, averageCategoryRating;

---------------------------------------------------------------------------
// Movies Analysis
---------------------------------------------------------------------------

// Get movies with highest average_rating (best movies)
MATCH (movie:Movie)
WITH movie, movie.average_rating AS averageMovieRating
ORDER BY averageMovieRating DESC
LIMIT 10
RETURN movie.title, averageMovieRating;

// Get 10 movies of a category (most popular movies of a category)
MATCH (category:Category {name: "Comedy"})<-[:BELONGS_TO]-(movie:Movie)
RETURN movie.title
LIMIT 10;

// Get movies of a given year (most popular movies of a year)
// Result in graph view
MATCH q = (movie:Movie)-[:BELONGS_TO]->(category:Category)
WHERE movie.title CONTAINS '1995'
RETURN q;
// Result in table view
MATCH (movie:Movie)
WHERE movie.title CONTAINS '1995'
RETURN movie.title, movie.average_rating;

// Number of movies per year (analyse movie production over time)
MATCH (movie:Movie)
WITH movie, SUBSTRING(movie.title, size(movie.title) - 5, 4) AS movieYear
WHERE movieYear =~ '\\d{4}'
WITH movieYear, COUNT(movie) AS movieCount
ORDER BY movieYear DESC
LIMIT 10
RETURN movieYear, movieCount;


