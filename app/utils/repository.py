"""
  - Role: Base repository functionality
  - Key Functions: Common CRUD operations

  Includes query execution, result mapping, and error handling with
  consistent patterns across all data access components.
"""
from typing import List, Type, TypeVar, Generic, Dict, Any, Callable, Optional
import logging
from app.services.database import DatabaseService
from app.utils.decorators import log_operation
from app.utils.exceptions import DatabaseError

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations
    
    Generic type T should be a model class that has:
    - A from_dict method that converts a dict to model instance
    - A to_dict method that converts a model instance to a dict
    """
    
    def __init__(self, db_service: DatabaseService, table_name: str, model_class: Type[T]):
        """
        Initialize with database service
        
        Args:
            db_service: Database service instance
            table_name: Name of the table this repository manages
            model_class: Model class for type T
        """
        self.db = db_service
        self.table_name = table_name
        self.model_class = model_class
        self.logger = logging.getLogger(__name__)
    
    def _dict_to_model(self, data: Dict[str, Any]) -> T:
        """Convert dictionary to model instance"""
        return self.model_class.from_dict(data)
    
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return model.to_dict()
    
    @log_operation("fetch all records")
    def get_all(self) -> List[T]:
        """
        Get all records from the table
        
        Returns:
            List[T]: List of all records
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            result = self.db.fetch_all(query)
            return [self._dict_to_model(item) for item in result]
        except DatabaseError as e:
            self.logger.error(f"Failed to get all records: {e}")
            raise
    
    @log_operation("fetch record by ID")
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get a record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Optional[T]: Record if found, None otherwise
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = %s"
            result = self.db.fetch_one(query, (id,))
            return self._dict_to_model(result) if result else None
        except DatabaseError as e:
            self.logger.error(f"Failed to get record by ID {id}: {e}")
            raise
    
    @log_operation("fetch records by custom query")
    def get_by_query(self, query: str, params: tuple = None) -> List[T]:
        """
        Get records using a custom query
        
        Args:
            query: SQL query string
            params: Parameters for the query
            
        Returns:
            List[T]: List of records matching the query
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            result = self.db.fetch_all(query, params)
            return [self._dict_to_model(item) for item in result]
        except DatabaseError as e:
            self.logger.error(f"Failed to get records by custom query: {e}")
            raise
    
    def check_duplicate(self, item: T) -> bool:
        """
        Check if a record already exists (to be implemented by subclasses)
        
        Args:
            item: Record to check
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        return False
        
    @log_operation("insert record")
    def insert(self, item: T, skip_duplicates: bool = True) -> bool:
        """
        Insert a record into the database
        
        Args:
            item: Record to insert
            skip_duplicates: Whether to skip duplicate records (default: True)
            
        Returns:
            bool: True if record was inserted, False if skipped as duplicate
            
        Raises:
            DatabaseError: If insertion fails
        """
        try:
            # Check for duplicates if supported by the repository
            if skip_duplicates and self.check_duplicate(item):
                self.logger.info(f"Skipped inserting duplicate record into {self.table_name}")
                return False
                
            item_dict = self._model_to_dict(item)
            
            # Remove ID if present (for auto-increment)
            if 'id' in item_dict:
                del item_dict['id']
            
            columns = ', '.join(item_dict.keys())
            placeholders = ', '.join(['%s'] * len(item_dict))
            values = tuple(item_dict.values())
            
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            self.db.execute_query(query, values)
            self.logger.debug(f"Inserted record into {self.table_name}")
            return True
        except DatabaseError as e:
            self.logger.error(f"Failed to insert record: {e}")
            raise
