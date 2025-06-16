import logging  # Add logging import

from rest_framework.permissions import BasePermission

from .models import \
    CourseEnrollment

# Configure logger for this module
logger = logging.getLogger(__name__)


class IsStudentOrReadOnly(BasePermission):
    """
    Custom permission to allow students to access their own data.
    """

    def has_permission(self, request, view):
        logger.debug(f"Checking permission for user {request.user}")  # Log to file
        return request.user.is_authenticated and request.user.role == "student"

    def has_object_permission(self, request, view, obj):
        # Allow access only if the object belongs to the authenticated student
        return request.user.role == "student" and obj.user == request.user


class IsInstructorOrAdmin(BasePermission):
    """
    Custom permission to allow only instructors or admins to access a view.
    """

    def has_permission(self, request, view):
        # Allow access only if the user is an instructor or admin
        return request.user.is_authenticated and (
            request.user.role == "instructor" or request.user.is_staff
        )


class IsEnrolledInCourse(BasePermission):
    """
    Custom permission to allow students enrolled in a course to access its data.
    """

    def has_permission(self, request, view):
        # Extract course ID from the view kwargs
        course_id = view.kwargs.get("course_id")
        user = request.user

        # Debug logging
        print(f"DEBUG: Checking enrollment for user {user} in course {course_id}")

        if not user.is_authenticated:
            print("DEBUG: User is not authenticated.")
            return False

        # Allow access to course details even if not enrolled
        if course_id is None:
            return True

        # Check if the user is enrolled in the course
        is_enrolled = CourseEnrollment.objects.filter(
            user=user, course_id=course_id
        ).exists()
        print(
            f"DEBUG: Enrollment status for user {user.id} in course {course_id}: {is_enrolled}"
        )

        return is_enrolled
