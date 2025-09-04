import oracledb
import time

# Database connection details
dsn = oracledb.makedsn("your_host", "your_port", service_name="your_service_name")
connection = oracledb.connect(user="your_username", password="your_password", dsn=dsn)

def monitor_transactions():
    try:
        with connection.cursor() as cursor:
            # Query to fetch recent transactions
            query = """
                SELECT transaction_id, user_id, product_id, amount, status, transaction_date
                FROM ecommerce_transactions
                WHERE transaction_date >= SYSDATE - INTERVAL '1' MINUTE
                ORDER BY transaction_date DESC
            """
            while True:
                print("Fetching recent transactions...")
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    for row in rows:
                        print(f"Transaction ID: {row[0]}, User ID: {row[1]}, Product ID: {row[2]}, "
                              f"Amount: {row[3]}, Status: {row[4]}, Date: {row[5]}")
                else:
                    print("No new transactions in the last minute.")
                
                # Wait for a minute before checking again
                time.sleep(60)
    except oracledb.DatabaseError as e:
        print(f"Database error occurred: {e}")
    finally:
        connection.close()

# Start monitoring
monitor_transactions()
