from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Neo4jConnector:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "legal_tech")
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                max_connection_lifetime=30
            )
            self.driver.verify_connectivity()
            print("✅ Successfully connected to Neo4j")
            return self.driver
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None

    def close(self):
        """Close the connection"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")

# Example usage:
if __name__ == "__main__":
    connector = Neo4jConnector()
    driver = connector.connect()
    
    if driver:
        # Execute queries here
        connector.close()