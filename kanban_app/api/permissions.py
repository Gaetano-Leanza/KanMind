from rest_framework.permissions import BasePermission
from kanban_app.models import Board, Task

# --- Board Level Permissions ---

class IsBoardMemberOrOwner(BasePermission):
    """
    Permission to allow access if the user is either the owner 
    of the object or a verified member of the associated board.
    """
    def has_object_permission(self, request, view, obj):
        # Checks for direct ownership or presence in the members list
        return request.user == obj.owner or request.user in obj.members.all()


class IsBoardMember(BasePermission):
    """
    Comprehensive permission for board access.
    Validates both general request data (has_permission) and 
    specific database objects (has_object_permission).
    """

    def has_permission(self, request, view):
        """
        Validates access based on the 'board' ID provided in query params or request body.
        If no board is specified, the request passes to the next check.
        """
        board_id = request.data.get('board') or request.query_params.get('board')
        if not board_id:
            return True 

        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return False

        # Access only for the owner or board members
        return request.user == board.owner or request.user in board.members.all()

    def has_object_permission(self, request, view, obj):
        """
        Ensures the user belongs to the specific board object being accessed.
        Automatically resolves the board if the object is a child (e.g., a Task).
        """
        board = obj.board if hasattr(obj, "board") else obj
        return request.user == board.owner or request.user in board.members.all()


# --- Task & Comment Level Permissions ---

class IsTaskCreatorOrBoardOwner(BasePermission):
    """
    Restrictive permission for sensitive actions like deletion.
    Only the task creator or the overall board owner are authorized.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Logic: Board owners should always be able to moderate content on their board
        return user == obj.owner or user == obj.board.owner


class IsBoardMemberForTask(BasePermission):
    """
    Permission that ensures a user belongs to the parent board 
    before they can interact with specific tasks or comments.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Determine the parent board depending on the object type
        if hasattr(obj, 'task'):
            board = obj.task.board
        elif hasattr(obj, 'board'):
            board = obj.board
        else:
            return False

        # Check for ownership or membership via ID for performance
        return user.id == board.owner.id or board.members.filter(id=user.id).exists()


class IsCommentAuthor(BasePermission):
    """
    Strict permission to ensure only the original author can edit or delete a comment.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user