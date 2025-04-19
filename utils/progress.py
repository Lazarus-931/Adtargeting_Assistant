# utils/progress.py
from typing import Dict, Optional, Any
import sys


class ProgressTracker:
    """Tracks and displays progress of the analysis pipeline"""
    def __init__(self):
        self.active = False
        self.status = {}
    
    def start(self):
        """Start progress tracking"""
        self.active = True
        self.status = {}
    
    def stop(self):
        """Stop progress tracking"""
        self.active = False
        self.status = {}
    
    def update_status(self, agent_name: str, subject: Optional[str] = None, status: str = ""):
        """Update the status of an agent"""
        if not self.active:
            return
        
        # Create key for this agent+subject
        key = f"{agent_name}/{subject}" if subject else agent_name
        
        # Update status
        self.status[key] = status
        
        # Display current status
        self._display_status()
    
    def _display_status(self):
        """Display the current status"""
        # Clear previous status display
        sys.stdout.write("\033[F" * (len(self.status) + 2))
        sys.stdout.write("\033[J")
        
        # Print header
        print("\nAnalysis Progress:")
        print("-" * 50)
        
        # Print current status for each agent
        for key, status in sorted(self.status.items()):
            parts = key.split("/")
            agent = parts[0]
            subject = parts[1] if len(parts) > 1 else ""
            
            if subject:
                print(f"{agent:<15} [{subject:<20}]: {status}")
            else:
                print(f"{agent:<15}: {status}")


# Create a global instance for import
progress = ProgressTracker()