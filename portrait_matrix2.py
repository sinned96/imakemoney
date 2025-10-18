"""
portrait_matrix2.py - Helper module for portrait matrix container with enhanced input mapping.

This module provides PortraitMatrixContainer, which extends the base PortraitContainer
with explicit set_inverse_matrix support and enhanced logging for debugging input
coordinate transformation issues.

This is used when PORTRAIT_PIPELINE=matrix and PORTRAIT_MATRIX_IMPL=rt to ensure
touch/mouse coordinates are correctly mapped to the rotated portrait UI.
"""

import logging

# Debug flag - set to True to enable verbose logging of coordinate mapping
DEBUG = False

logger = logging.getLogger(__name__)

# Import PortraitContainer from main module - we'll inherit from it
# This import happens at runtime to avoid circular dependencies
def get_portrait_container_class():
    """Lazy import to get PortraitContainer class"""
    import main
    return main.PortraitContainer


class PortraitMatrixContainer:
    """
    Enhanced portrait container with explicit inverse matrix management.
    
    This class inherits from PortraitContainer (from main.py) to get all visual
    transformation logic, and adds explicit set_inverse_matrix() support for
    external matrix updates.
    
    The set_inverse_matrix() method allows external code to update the inverse
    transformation matrix used for touch coordinate mapping.
    
    Key features:
    - Inherits all visual transformation from PortraitContainer
    - Inherits touch coordinate transformation from PortraitContainer
    - Adds set_inverse_matrix() for explicit matrix updates
    - Logs matrix updates and touch mapping for debugging
    
    Usage:
        container = PortraitMatrixContainer()
        # ... add children to container ...
        # When portrait transform is calculated externally:
        container.set_inverse_matrix(inverse_matrix)
    """
    
    def __new__(cls, **kwargs):
        """
        Create instance by dynamically inheriting from PortraitContainer.
        
        This uses dynamic class creation to inherit from PortraitContainer
        without causing circular import issues.
        """
        # Get PortraitContainer class
        PortraitContainerBase = get_portrait_container_class()
        
        # Create a new class that inherits from PortraitContainer
        class _PortraitMatrixContainer(PortraitContainerBase):
            """Dynamic subclass of PortraitContainer with set_inverse_matrix support"""
            
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                logger.info("[PortraitMatrixContainer] Container initialized (enhanced input mapping)")
            
            def set_inverse_matrix(self, matrix):
                """
                Set the inverse transformation matrix for input coordinate mapping.
                
                This method allows external code to update the inverse matrix used
                for touch coordinate transformation. The matrix is stored in self._inverse_matrix
                which is already used by the inherited touch handlers from PortraitContainer.
                
                Args:
                    matrix: Kivy Matrix object representing the inverse of the portrait transform,
                            or None to disable coordinate mapping.
                """
                self._inverse_matrix = matrix
                if DEBUG:
                    if matrix:
                        logger.debug(f"[PortraitMatrixContainer] Inverse matrix updated: {matrix}")
                    else:
                        logger.debug("[PortraitMatrixContainer] Inverse matrix cleared (None)")
                
                # Always log matrix updates at INFO level (non-DEBUG)
                if matrix:
                    logger.info("[PortraitMatrixContainer] Inverse matrix updated for input coordinate mapping")
                else:
                    logger.info("[PortraitMatrixContainer] Inverse matrix cleared")
            
            def on_touch_down(self, touch):
                """Override to add debug logging for touch events"""
                if DEBUG and self._inverse_matrix:
                    orig_x, orig_y = touch.x, touch.y
                    tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
                    logger.debug(f"[PortraitMatrixContainer] Touch down: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
                return super().on_touch_down(touch)
            
            def on_touch_move(self, touch):
                """Override to add debug logging for touch events"""
                if DEBUG and self._inverse_matrix:
                    orig_x, orig_y = touch.x, touch.y
                    tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
                    logger.debug(f"[PortraitMatrixContainer] Touch move: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
                return super().on_touch_move(touch)
            
            def on_touch_up(self, touch):
                """Override to add debug logging for touch events"""
                if DEBUG and self._inverse_matrix:
                    orig_x, orig_y = touch.x, touch.y
                    tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
                    logger.debug(f"[PortraitMatrixContainer] Touch up: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
                return super().on_touch_up(touch)
        
        # Create and return an instance of the dynamic class
        return _PortraitMatrixContainer(**kwargs)
    
    def on_touch_down(self, touch):
        """
        Transform touch coordinates before dispatching to children.
        
        If an inverse matrix is set, temporarily replaces touch position with
        the transformed coordinates, dispatches to children, then restores original position.
        """
        if self._inverse_matrix:
            # Save original position via push
            touch.push()
            
            # Apply inverse transform to map screen coordinates to virtual space
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            
            if DEBUG:
                logger.debug(f"[PortraitMatrixContainer] on_touch_down: ({touch.x:.1f}, {touch.y:.1f}) -> ({tx:.1f}, {ty:.1f})")
            
            # Update touch position
            touch.x, touch.y = tx, ty
        
        # Dispatch to children with transformed coordinates
        ret = super().on_touch_down(touch)
        
        # Restore original position
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """
        Transform touch coordinates before dispatching to children.
        
        If an inverse matrix is set, temporarily replaces touch position with
        the transformed coordinates, dispatches to children, then restores original position.
        """
        if self._inverse_matrix:
            # Save original position via push
            touch.push()
            
            # Apply inverse transform
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            
            if DEBUG:
                logger.debug(f"[PortraitMatrixContainer] on_touch_move: ({touch.x:.1f}, {touch.y:.1f}) -> ({tx:.1f}, {ty:.1f})")
            
            # Update touch position
            touch.x, touch.y = tx, ty
        
        # Dispatch to children
        ret = super().on_touch_move(touch)
        
        # Restore original position
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """
        Transform touch coordinates before dispatching to children.
        
        If an inverse matrix is set, temporarily replaces touch position with
        the transformed coordinates, dispatches to children, then restores original position.
        """
        if self._inverse_matrix:
            # Save original position via push
            touch.push()
            
            # Apply inverse transform
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            
            if DEBUG:
                logger.debug(f"[PortraitMatrixContainer] on_touch_up: ({touch.x:.1f}, {touch.y:.1f}) -> ({tx:.1f}, {ty:.1f})")
            
            # Update touch position
            touch.x, touch.y = tx, ty
        
        # Dispatch to children
        ret = super().on_touch_up(touch)
        
        # Restore original position
        if self._inverse_matrix:
            touch.pop()
        
        return ret
