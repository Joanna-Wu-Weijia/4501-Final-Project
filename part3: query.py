# Helper function to write the queries to file
def write_query_to_file(query, outfile):
    df = pd.read_sql(query, engine)
    df.to_csv(outfile, index=False)

### Q1
QUERY_1_FILENAME = "hourly_taxi_popularity.csv"
QUERY_1 = """
WITH hourly_counts AS (
    SELECT 
        CAST(strftime('%H', pickup_datetime) AS INTEGER) as X,
        COUNT(*) as Y
    FROM taxi_trips
    WHERE 
        pickup_datetime >= '2020-01-01' 
        AND pickup_datetime < '2024-09-01'
    GROUP BY strftime('%H', pickup_datetime)
)
SELECT 
    X,
    Y,
    ROUND(CAST(Y AS FLOAT) * 100 / (SELECT SUM(Y) FROM hourly_counts), 2) as percentage
FROM hourly_counts
ORDER BY X;
"""

# execute query either via sqlalchemy
#with engine.connect() as con:
    #results = con.execute(db.text(QUERY_1)).fetchall()
#results

# or via pandas
pd.read_sql(QUERY_1, con=engine)

write_query_to_file(QUERY_1, QUERY_1_FILENAME)

### Q2
QUERY_2_FILENAME = "daily_uber_popularity.csv"
QUERY_2 = """
WITH daily_counts AS (
    SELECT 
        weekday_num as X,
        COUNT(*) as Y
    FROM uber_trips
    WHERE 
        pickup_datetime >= '2020-01-01' 
        AND pickup_datetime < '2024-09-01'
    GROUP BY weekday_num
)
SELECT 
    X,
    Y,
    ROUND(CAST(Y AS FLOAT) * 100 / (SELECT SUM(Y) FROM daily_counts), 2) as percentage
FROM daily_counts
ORDER BY Y DESC;
"""
pd.read_sql(QUERY_2, con=engine)
write_query_to_file(QUERY_2, QUERY_2_FILENAME)

### Q3
QUERY_3_FILENAME = "ride_distance_percentile.csv"
QUERY_3 = """
WITH combined_trips AS (
    SELECT trip_distance as distance
    FROM taxi_trips
    WHERE 
        pickup_datetime >= '2024-01-01' 
        AND pickup_datetime < '2024-02-01'
    UNION ALL
    SELECT trip_miles as distance
    FROM uber_trips
    WHERE 
        pickup_datetime >= '2024-01-01' 
        AND pickup_datetime < '2024-02-01'
),
sorted_distances AS (
    SELECT 
        distance,
        (ROW_NUMBER() OVER (ORDER BY distance) - 1.0) / 
        (COUNT(*) OVER () - 1.0) * 100 as percentile
    FROM combined_trips
)
SELECT ROUND(distance, 2) as percentile_95
FROM sorted_distances
WHERE percentile >= 95
ORDER BY distance ASC
LIMIT 1;
"""

# Execute the query
percentile_95_result = pd.read_sql_query(QUERY_3, con=engine)
write_query_to_file(QUERY_3, QUERY_3_FILENAME)

### Q4
# Establish connection to the SQLite database
conn = sqlite3.connect('project.db')

# SQL query
query = """
WITH DailyRideStats AS (
    SELECT 
        DATE(pickup_datetime) AS ride_date,
        COUNT(*) AS total_rides,
        AVG(trip_distance) AS avg_distance
    FROM (
        SELECT pickup_datetime, trip_distance FROM taxi_trips
        UNION ALL
        SELECT pickup_datetime, trip_miles AS trip_distance FROM uber_trips
    )
    WHERE strftime('%Y', pickup_datetime) = '2023'
    GROUP BY DATE(pickup_datetime)
),
WeatherStats AS (
    SELECT 
        date AS weather_date,
        avg_precipitation,
        avg_windspeed
    FROM daily_weather
    WHERE strftime('%Y', date) = '2023'
)
SELECT 
    r.ride_date AS date,
    r.total_rides,
    r.avg_distance,
    w.avg_precipitation,
    w.avg_windspeed
FROM DailyRideStats r
LEFT JOIN WeatherStats w
ON r.ride_date = w.weather_date
ORDER BY r.total_rides DESC
LIMIT 10;
"""

# Execute the query and fetch results
result_df = pd.read_sql_query(query, conn)

# Display the result
print(result_df)

# Close the connection
conn.close()