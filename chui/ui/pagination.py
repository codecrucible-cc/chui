"""
Pagination utilities for CHUI UI system.

This module provides a flexible pagination system that can be used
for tables, lists, and other data displays.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Callable, Union
from dataclasses import dataclass
import math


T = TypeVar('T')


@dataclass
class Page(Generic[T]):
    """Represents a single page of paginated data"""
    items: List[T]
    page_number: int
    total_pages: int
    total_items: int
    page_size: int
    has_next: bool
    has_previous: bool


class Paginator(Generic[T]):
    """Handles pagination of data collections"""
    
    def __init__(self, 
                 items: List[T],
                 page_size: int = 10):
        """
        Initialize a paginator
        
        Args:
            items: List of items to paginate
            page_size: Number of items per page
        """
        self.items = items
        self.page_size = max(1, page_size)  # Ensure at least 1 item per page
        self.total_items = len(items)
        self.total_pages = math.ceil(self.total_items / self.page_size)
    
    def get_page(self, page_number: int = 1) -> Page[T]:
        """
        Get a specific page of data
        
        Args:
            page_number: The page number to retrieve (1-based)
            
        Returns:
            Page object containing items and pagination info
        """
        # Ensure page_number is valid
        page_number = max(1, min(page_number, self.total_pages))
        
        # Calculate indices
        start_idx = (page_number - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, self.total_items)
        
        # Get page items
        page_items = self.items[start_idx:end_idx]
        
        # Create page object
        return Page(
            items=page_items,
            page_number=page_number,
            total_pages=self.total_pages,
            total_items=self.total_items,
            page_size=self.page_size,
            has_next=page_number < self.total_pages,
            has_previous=page_number > 1
        )
    
    def get_page_range(self, page_number: int, window: int = 2) -> List[int]:
        """
        Get a range of page numbers centered around the current page
        
        Args:
            page_number: Current page number
            window: Number of pages to show on each side
            
        Returns:
            List of page numbers to display
        """
        # Ensure page_number is valid
        page_number = max(1, min(page_number, self.total_pages))
        
        # Calculate start and end of range
        start = max(1, page_number - window)
        end = min(self.total_pages, page_number + window)
        
        # Always show first and last page
        page_range = []
        
        # First page(s)
        if start > 1:
            page_range.extend([1])
            if start > 2:
                page_range.append(None)  # Represents ellipsis
        
        # Main page range
        page_range.extend(range(start, end + 1))
        
        # Last page(s)
        if end < self.total_pages:
            if end < self.total_pages - 1:
                page_range.append(None)  # Represents ellipsis
            page_range.append(self.total_pages)
        
        return page_range


class FilterablePaginator(Paginator[T]):
    """Paginator with filtering and sorting capabilities"""
    
    def __init__(self, 
                 items: List[T],
                 page_size: int = 10,
                 filter_func: Optional[Callable[[T], bool]] = None,
                 sort_key: Optional[Callable[[T], Any]] = None,
                 reverse: bool = False):
        """
        Initialize a filterable paginator
        
        Args:
            items: List of items to paginate
            page_size: Number of items per page
            filter_func: Optional function to filter items
            sort_key: Optional key function for sorting
            reverse: Whether to reverse the sort order
        """
        # Apply filtering if provided
        if filter_func:
            items = [item for item in items if filter_func(item)]
            
        # Apply sorting if provided
        if sort_key:
            items = sorted(items, key=sort_key, reverse=reverse)
            
        super().__init__(items, page_size)
        self.filtered = filter_func is not None
        self.sorted = sort_key is not None
        
    @classmethod
    def from_dict_list(cls, 
                      items: List[Dict],
                      page_size: int = 10,
                      filters: Optional[Dict[str, Any]] = None,
                      sort_by: Optional[str] = None,
                      reverse: bool = False) -> 'FilterablePaginator[Dict]':
        """
        Create a paginator from a list of dictionaries with field-based filtering
        
        Args:
            items: List of dictionary items to paginate
            page_size: Number of items per page
            filters: Optional dictionary of field:value pairs to filter by
            sort_by: Optional field name to sort by
            reverse: Whether to reverse the sort order
            
        Returns:
            FilterablePaginator instance
        """
        filter_func = None
        sort_key = None
        
        # Create filter function if filters provided
        if filters:
            def filter_func(item: Dict) -> bool:
                return all(item.get(field) == value for field, value in filters.items())
                
        # Create sort key function if sort_by provided
        if sort_by:
            def sort_key(item: Dict) -> Any:
                return item.get(sort_by, "")
                
        return cls(items, page_size, filter_func, sort_key, reverse)


def paginate_list(items: List[T], 
                 page: int = 1, 
                 page_size: int = 10) -> Tuple[List[T], Dict[str, Any]]:
    """
    Utility function to paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Current page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (page_items, pagination_info)
    """
    paginator = Paginator(items, page_size)
    page_obj = paginator.get_page(page)
    
    pagination_info = {
        "page": page_obj.page_number,
        "total_pages": page_obj.total_pages,
        "total_items": page_obj.total_items,
        "page_size": page_obj.page_size,
        "has_next": page_obj.has_next,
        "has_previous": page_obj.has_previous
    }
    
    return page_obj.items, pagination_info