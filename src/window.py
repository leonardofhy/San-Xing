"""Window selection with character budget management"""

from typing import List, Tuple
from .models import DiaryEntry
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class WindowBuilder:
    """Manages entry selection within character budget"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def build_window(self, entries: List[DiaryEntry], char_budget: int) -> Tuple[List[DiaryEntry], int]:
        """
        Select entries fitting in character budget
        Returns: (selected_entries, total_chars)
        """
        if not entries:
            return [], 0
        
        # Start from newest, work backwards
        selected = []
        total_chars = 0
        
        for entry in reversed(entries):
            entry_chars = len(entry.diary_text) + 50  # Add overhead for date/formatting
            if total_chars + entry_chars > char_budget:
                break
            selected.append(entry)
            total_chars += entry_chars
        
        # Re-sort chronologically
        selected.reverse()
        
        logger.info("Window: %d entries, %d chars (budget: %d)", 
                   len(selected), total_chars, char_budget)
        return selected, total_chars
