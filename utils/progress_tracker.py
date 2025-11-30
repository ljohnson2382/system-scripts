#!/usr/bin/env python3
"""
Shared Progress Tracking Utility for System-Scripts Toolkit

This module provides standardized progress tracking capabilities that can be used
across all tools in the system-scripts toolkit. Based on the patterns established
in the network toolkit.

Author: System-Scripts Toolkit
Created: November 2025
"""

from tqdm import tqdm
import time
from typing import List, Optional, Callable, Any


class ProgressTracker:
    """
    Standardized progress tracker for long-running operations.
    
    Provides consistent progress bar styling and functionality across
    all toolkit components.
    """
    
    def __init__(self, total_steps: int, description: str = "Processing", 
                 unit: str = "steps", show_rate: bool = True):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps for the operation
            description: Description of the operation being tracked
            unit: Unit label for progress (e.g., "files", "tests", "checks")
            show_rate: Whether to show processing rate
        """
        self.total_steps = total_steps
        self.description = description
        self.unit = unit
        self.current_step = 0
        self.show_rate = show_rate
        self.pbar = None
        self.start_time = None
        
    def start(self):
        """Start the progress tracking."""
        self.start_time = time.time()
        self.pbar = tqdm(
            total=self.total_steps,
            desc=self.description,
            unit=self.unit,
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        )
        
    def update(self, step_name: str = "", increment: int = 1):
        """
        Update progress with current step information.
        
        Args:
            step_name: Name/description of current step
            increment: Number of steps to advance (default: 1)
        """
        if self.pbar is None:
            self.start()
            
        self.current_step += increment
        
        if step_name:
            self.pbar.set_postfix_str(f"- {step_name}")
        
        self.pbar.update(increment)
        
    def finish(self, final_message: str = "Complete"):
        """
        Complete the progress tracking.
        
        Args:
            final_message: Final message to display
        """
        if self.pbar:
            self.pbar.set_postfix_str(f"- {final_message}")
            self.pbar.close()
            
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        print(f"\n✅ {self.description} completed in {elapsed_time:.2f} seconds")


class MultiStageProgressTracker:
    """
    Progress tracker for multi-stage operations.
    
    Useful for operations that have distinct phases with different
    numbers of steps in each phase.
    """
    
    def __init__(self, stages: List[dict], overall_description: str = "Multi-stage Operation"):
        """
        Initialize multi-stage progress tracker.
        
        Args:
            stages: List of stage definitions, each with 'name', 'steps', and optional 'description'
            overall_description: Description of the overall operation
            
        Example:
            stages = [
                {'name': 'Scanning', 'steps': 10, 'description': 'Scanning system components'},
                {'name': 'Analysis', 'steps': 5, 'description': 'Analyzing results'},
                {'name': 'Reporting', 'steps': 3, 'description': 'Generating report'}
            ]
        """
        self.stages = stages
        self.overall_description = overall_description
        self.current_stage_index = 0
        self.current_stage_tracker = None
        self.total_stages = len(stages)
        
    def start_stage(self, stage_index: Optional[int] = None):
        """
        Start tracking a specific stage.
        
        Args:
            stage_index: Index of stage to start (if None, uses current stage)
        """
        if stage_index is not None:
            self.current_stage_index = stage_index
            
        if self.current_stage_index >= len(self.stages):
            return
            
        stage = self.stages[self.current_stage_index]
        stage_desc = stage.get('description', stage['name'])
        
        print(f"\n🔄 Stage {self.current_stage_index + 1}/{self.total_stages}: {stage['name']}")
        
        self.current_stage_tracker = ProgressTracker(
            total_steps=stage['steps'],
            description=stage_desc,
            unit="items"
        )
        self.current_stage_tracker.start()
        
    def update_stage(self, step_name: str = "", increment: int = 1):
        """Update the current stage progress."""
        if self.current_stage_tracker:
            self.current_stage_tracker.update(step_name, increment)
            
    def finish_stage(self):
        """Finish the current stage and advance to next."""
        if self.current_stage_tracker:
            stage_name = self.stages[self.current_stage_index]['name']
            self.current_stage_tracker.finish(f"{stage_name} completed")
            
        self.current_stage_index += 1
        
    def finish_all(self):
        """Complete all stages and show final summary."""
        if self.current_stage_tracker:
            self.finish_stage()
            
        print(f"\n🎉 {self.overall_description} completed successfully!")
        print(f"   Processed {self.total_stages} stages")


def simple_progress(items: List[Any], description: str = "Processing", 
                   processor: Optional[Callable] = None):
    """
    Simple progress wrapper for processing lists of items.
    
    Args:
        items: List of items to process
        description: Description of the operation
        processor: Optional function to process each item
        
    Returns:
        If processor is provided, returns list of results.
        If no processor, returns the items (useful for iteration).
        
    Example:
        # Simple iteration with progress
        for item in simple_progress(my_list, "Processing files"):
            do_something(item)
            
        # Processing with function
        results = simple_progress(files, "Converting files", convert_file)
    """
    tracker = ProgressTracker(len(items), description)
    results = []
    
    for item in items:
        if processor:
            result = processor(item)
            results.append(result)
            tracker.update(f"{getattr(item, 'name', str(item)[:50])}")
        else:
            tracker.update(f"{str(item)[:50]}")
            yield item
            
    tracker.finish()
    
    if processor:
        return results


if __name__ == "__main__":
    # Demo usage
    import time
    
    print("Demo: Simple Progress Tracker")
    tracker = ProgressTracker(10, "Demo Operation", "items")
    
    for i in range(10):
        time.sleep(0.2)  # Simulate work
        tracker.update(f"Processing item {i+1}")
        
    tracker.finish()
    
    print("\nDemo: Multi-Stage Progress Tracker")
    stages = [
        {'name': 'Initialize', 'steps': 3, 'description': 'Initializing system'},
        {'name': 'Process', 'steps': 7, 'description': 'Processing data'},
        {'name': 'Finalize', 'steps': 2, 'description': 'Finalizing results'}
    ]
    
    multi_tracker = MultiStageProgressTracker(stages, "Demo Multi-Stage Operation")
    
    for stage_idx in range(len(stages)):
        multi_tracker.start_stage(stage_idx)
        stage = stages[stage_idx]
        
        for step in range(stage['steps']):
            time.sleep(0.1)  # Simulate work
            multi_tracker.update_stage(f"Step {step + 1}")
            
        multi_tracker.finish_stage()
        
    multi_tracker.finish_all()