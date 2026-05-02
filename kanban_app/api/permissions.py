from rest_framework.permissions import BasePermission
from kanban_app.models import Board,Task



class IsBoardMemberOrOwner(BasePermission):
    """
    Allows access if the user is either the owner of the object
    or a member of the associated board.
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner or request.user in obj.members.all()


class IsBoardMember(BasePermission):
    """
    Combined permission for accessing boards.
    Checks both general access rights (e.g., POST requests with board specified)
    and object-level permissions on board objects.
    """

    def has_permission(self, request, view):
        """
        Checks if the user has access to the specified board,
        based on 'board' in the request data or query parameters.
        If no board is specified, access is not restricted.
        """
        board_id = request.data.get('board') or request.query_params.get('board')
        if not board_id:
            return True 

        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return False

        return request.user == board.owner or request.user in board.members.all()

    def has_object_permission(self, request, view, obj):
        """
        Checks access to a board object.
        If the object is a child object with a 'board' attribute,
        the board is determined and membership/ownership checked.
        """
        board = obj.board if hasattr(obj, "board") else obj
        return request.user == board.owner or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(BasePermission):
    """
    Allows actions (e.g., deletion) only to the creator of the task
    or the owner of the associated board.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        return user == obj.owner or user == obj.board.owner


class IsBoardMemberForTask(BasePermission):
    """
    Allows access only to members of the board linked to a task or comment.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if hasattr(obj, 'task'):
            board = obj.task.board
        elif hasattr(obj, 'board'):
            board = obj.board
        else:
            return False

        return user.id == board.owner.id or board.members.filter(id=user.id).exists()


class IsCommentAuthor(BasePermission):
    """
    Allows actions only to the author of the comment.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
