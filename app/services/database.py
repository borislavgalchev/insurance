import mysql.connector
from typing import Dict, Any, List, Optional
import logging
from config.settings import DB_CONFIG
from app.utils.exceptions import DatabaseError
from app.utils.decorators import db_operation, log_operation

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for handling database connections and operations
    """
    def __init__(self):
        """Initialize database connection"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            logger.info("Database connection established")
        except mysql.connector.Error as err:
            logger.error(f"Database connection failed: {err}")
            raise DatabaseError(f"Failed to connect to database: {err}")
    
    def _execute(self, query: str, params: Optional[tuple] = None) -> None:
        """
        Execute a database query with parameters
        
        Args:
            query: SQL query string
            params: Parameters for the query
        """
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
    
    @db_operation("Query execution")
    def execute_query(self, query: str, params: Optional[tuple] = None) -> None:
        """
        Execute a database query
        
        Args:
            query: SQL query string
            params: Parameters for the query
            
        Raises:
            DatabaseError: If query execution fails
        """
        self._execute(query, params)
        self.conn.commit()
    
    @db_operation("Query fetch all")
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and fetch all results
        
        Args:
            query: SQL query string
            params: Parameters for the query
            
        Returns:
            list: List of dictionaries containing query results
            
        Raises:
            DatabaseError: If query execution fails
        """
        self._execute(query, params)
        return self.cursor.fetchall()
    
    @db_operation("Query fetch one")
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Execute a query and fetch one result
        
        Args:
            query: SQL query string
            params: Parameters for the query
            
        Returns:
            dict: Dictionary containing query results
            
        Raises:
            DatabaseError: If query execution fails
        """
        self._execute(query, params)
        return self.cursor.fetchone()
    
    @db_operation("Table creation")
    @log_operation("Table creation")
    def create_table(self, query: str) -> None:
        """
        Create a database table
        
        Args:
            query: SQL query for table creation
            
        Raises:
            DatabaseError: If table creation fails
        """
        self._execute(query)
        self.conn.commit()
    
    @log_operation("Database connection closing")
    def close(self) -> None:
        """Close database connection"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()