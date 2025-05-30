import logging
from django.db import models
from django.db.models import Avg
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authentication import get_authorization_header
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Course,
    CourseEnrollment,
    CourseVersion,
    LearningTask,
    QuizAttempt,
    QuizOption,
    QuizQuestion,
    QuizResponse,
    QuizTask,
    TaskProgress,
    User,
)
from .serializers import (
    CourseEnrollmentSerializer,
    CourseSerializer,
    CourseVersionSerializer,
    CustomTokenObtainPairSerializer,
    LearningTaskSerializer,
    QuizAttemptSerializer,
    QuizOptionSerializer,
    QuizQuestionSerializer,
    QuizResponseSerializer,
    QuizTaskSerializer,
    RegisterSerializer,
    TaskProgressSerializer,
    UserSerializer,
)
from .permissions import IsEnrolledInCourse, IsInstructorOrAdmin, IsStudentOrReadOnly

# Configure logger for this module
logger = logging.getLogger(__name__)


# Example usage of logger
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint to verify the API is running
    """
    logger.info("Health check endpoint accessed.")  # Log to file
    return Response({"status": "healthy"}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses our enhanced JWT serializer
    """

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class LogoutView(APIView):
    """
    API endpoint for user logout (blacklists the refresh token)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        """
        Allow users to view their own profile
        """
        if self.action == "retrieve" and self.request.user.is_authenticated:
            if str(self.request.user.id) == self.kwargs.get("pk"):
                return [permissions.IsAuthenticated()]
        return super().get_permissions()


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for courses
    """

    queryset = Course.objects.all().order_by("id")  # Ensure consistent ordering
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        url_path="instructor/courses",
        permission_classes=[IsInstructorOrAdmin],  # Apply IsInstructorOrAdmin
    )
    def instructor_courses(self, request):
        """
        Fetch courses created by the instructor or all courses for admin.
        """
        try:
            # Allow access for both instructors and admins
            if request.user.role not in ["instructor", "admin"]:
                return Response(
                    {"error": "You do not have permission to access this resource."},
                    status=403,
                )

            if request.user.role == "admin":
                # Admins can view all courses
                queryset = self.get_queryset()
            else:
                # Instructors can only view courses they created
                queryset = self.get_queryset().filter(creator=request.user)

            if not queryset.exists():
                return Response({"message": "No courses found."}, status=404)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            # Log the error for debugging
            print(f"Error fetching instructor courses: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred while fetching courses."},
                status=500,
            )

    @action(
        detail=True,
        methods=["get"],
        url_path="student-progress/(?P<user_id>[^/.]+)",  # Add user_id to the URL
        permission_classes=[IsAuthenticated],  # Allow all authenticated users
    )
    def student_progress(self, request, pk=None, user_id=None):
        """
        Fetch student progress for a specific course and user.
        """
        try:
            course = self.get_object()

            # Check if the user is enrolled
            is_enrolled = CourseEnrollment.objects.filter(
                user_id=user_id, course_id=course.id
            ).exists()

            if not is_enrolled:
                # Return limited course details for non-enrolled users
                return Response(
                    {
                        "course_title": course.title,
                        "description": course.description,
                        "learning_objectives": course.learning_objectives,
                        "prerequisites": course.prerequisites,
                        "message": "Enroll in the course to access progress details.",
                    },
                    status=200,
                )

            # Fetch progress for the specified user
            progress = TaskProgress.objects.filter(
                user_id=user_id, task__course_id=course.id
            )
            if not progress.exists():
                return Response(
                    {"message": "No progress found for this course."}, status=404
                )

            serializer = TaskProgressSerializer(progress, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(
                "Error fetching student progress for course %s: %s",
                pk,
                str(e),
                exc_info=True,
            )
            return Response(
                {"error": "An unexpected error occurred while fetching progress."},
                status=500,
            )

    @action(
        detail=True,
        methods=["get"],
        url_path="details",
        permission_classes=[IsAuthenticated],
    )
    def course_details(self, request, pk=None):
        """
        Fetch course details without progress data.
        """
        try:
            logger.info("Fetching course details for course ID: %s", pk)
            course = self.get_object()

            # Fetch tasks related to the course
            tasks = LearningTask.objects.filter(course=course)
            logger.info("Found %s tasks for course ID: %s", tasks.count(), pk)

            return Response(
                {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "learning_objectives": course.learning_objectives,
                    "prerequisites": course.prerequisites,
                    "tasks": [
                        {"id": task.id, "title": task.title, "type": task.type}
                        for task in tasks
                    ],
                }
            )
        except Course.DoesNotExist:
            logger.error("Course with ID %s does not exist.", pk)
            return Response({"error": "Course not found."}, status=404)
        except Exception as e:
            logger.error(
                "Error fetching course details for course ID %s: %s",
                pk,
                str(e),
                exc_info=True,
            )
            return Response(
                {
                    "error": "An unexpected error occurred while fetching course details."
                },
                status=500,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="enroll",
        permission_classes=[IsAuthenticated],
    )
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user

        if CourseEnrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {"detail": "You are already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        CourseEnrollment.objects.create(user=user, course=course, status="active")
        return Response(
            {"detail": "Successfully enrolled in the course."},
            status=status.HTTP_201_CREATED,
        )

    def get_permissions(self):
        """
        Allow students to view course details.
        """
        if self.action == "retrieve" and self.request.user.is_authenticated:
            if self.request.user.role == "student":
                return [permissions.IsAuthenticated()]
        return super().get_permissions()


class CourseVersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course versions
    """

    queryset = CourseVersion.objects.all().order_by("created_at")
    serializer_class = CourseVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class LearningTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for learning tasks
    """

    queryset = LearningTask.objects.all()
    serializer_class = LearningTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = LearningTask.objects.all()
        course_id = self.request.query_params.get("course")
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    @action(detail=False, methods=["get"], url_path="course/(?P<course_id>[^/.]+)")
    def tasks_by_course(self, request, course_id=None):
        """
        Fetch tasks for a specific course.
        """
        try:
            tasks = LearningTask.objects.filter(course_id=course_id).order_by("order")
            if not tasks.exists():
                return Response(
                    {"error": "No tasks found for this course."}, status=404
                )
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(
                "Error fetching tasks for course %s: %s",
                course_id,
                str(e),
                exc_info=True,
            )
            return Response(
                {"error": "An unexpected error occurred while fetching tasks."},
                status=500,
            )


class QuizTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for quiz tasks
    """

    queryset = QuizTask.objects.all()
    serializer_class = QuizTaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuizQuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for quiz questions
    """

    queryset = QuizQuestion.objects.all()
    serializer_class = QuizQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuizOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for quiz options
    """

    queryset = QuizOption.objects.all()
    serializer_class = QuizOptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course enrollments
    """

    queryset = CourseEnrollment.objects.all().order_by("id")
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle schema generation for Swagger
        if getattr(self, "swagger_fake_view", False):
            return CourseEnrollment.objects.none()

        # Handle AnonymousUser
        if isinstance(self.request.user, AnonymousUser):
            return CourseEnrollment.objects.none()

        # Regular queryset logic
        queryset = CourseEnrollment.objects.all()

        # Safely check user role and staff status
        user_role = getattr(self.request.user, "role", None)
        is_staff = getattr(self.request.user, "is_staff", False)

        if is_staff or user_role == "admin":
            return queryset

        # Filter enrollments for the current user
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskProgressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task progress
    """

    queryset = TaskProgress.objects.all()
    serializer_class = TaskProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter progress to only show those belonging to the current user
        return TaskProgress.objects.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        # Allow updating the status of a task
        instance = self.get_object()
        instance.status = request.data.get("status", instance.status)
        instance.save()
        return Response({"status": "Task progress updated"})


class QuizAttemptViewSet(viewsets.ModelViewSet):
    """
    API endpoint for quiz attempts
    """

    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter attempts to only show those belonging to the current user
        unless the user is staff/admin
        """
        if self.request.user.is_staff or self.request.user.role == "admin":
            return QuizAttempt.objects.all()
        return QuizAttempt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuizResponseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for quiz responses
    """

    queryset = QuizResponse.objects.all()
    serializer_class = QuizResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter responses to only show those belonging to the current user's attempts
        unless the user is staff/admin
        """
        if self.request.user.is_staff or self.request.user.role == "admin":
            return QuizResponse.objects.all()
        return QuizResponse.objects.filter(attempt__user=self.request.user)


@api_view(["GET"])
def validate_token(request):
    """
    Validate the access token.
    """
    auth_header = get_authorization_header(request).split()
    if not auth_header or auth_header[0].lower() != b"bearer":
        return Response(
            {"detail": "Authorization header missing or invalid."}, status=401
        )
    try:
        token = auth_header[1].decode("utf-8")
        AccessToken(token)  # Validate the token
        return Response({"detail": "Token is valid."}, status=200)
    except (TokenError, InvalidToken) as e:
        return Response({"detail": str(e)}, status=401)


class UserTaskProgressAPI(APIView):
    """
    API endpoint to retrieve task progress for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Use the authenticated user to filter data
        user = request.user
        task_progress = TaskProgress.objects.filter(user=user)
        data = [{"task_id": tp.task.id, "status": tp.status} for tp in task_progress]
        return Response(data)


class InstructorDashboardAPI(APIView):
    """
    API endpoint for instructor-specific dashboard data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "instructor":
            return Response(
                {"error": "You do not have permission to access this resource."},
                status=403,
            )

        # Fetch courses created by the instructor
        courses_created = Course.objects.filter(creator=request.user).count()
        # Fetch students enrolled in the instructor's courses
        students_enrolled = (
            CourseEnrollment.objects.filter(course__creator=request.user)
            .values("user")
            .distinct()
            .count()
        )
        # Fetch recent activity in the instructor's courses
        recent_activity = (
            TaskProgress.objects.filter(task__course__creator=request.user)
            .order_by("-updated_at")[:5]
            .values("task__title", "status", "updated_at")
        )

        data = {
            "courses_created": courses_created,
            "students_enrolled": students_enrolled,
            "recent_activity": list(recent_activity),
        }
        return Response(data)


class AdminDashboardAPI(APIView):
    """
    API endpoint for admin-specific dashboard data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response(
                {"error": "You do not have permission to access this resource."},
                status=403,
            )

        # Example data for the admin dashboard
        data = {
            "totalTasks": TaskProgress.objects.count(),
            "completedTasks": TaskProgress.objects.filter(status="completed").count(),
            "averageScore": QuizAttempt.objects.aggregate(Avg("score"))["score__avg"]
            or 0,
        }
        return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard_summary(request):
    """
    API endpoint for admin dashboard summary.
    """
    if request.user.role != "admin":
        return Response(
            {"error": "You do not have permission to access this resource."},
            status=403,
        )

    data = {
        "total_completed_tasks": TaskProgress.objects.filter(
            status="completed"
        ).count(),
        "total_tasks": TaskProgress.objects.count(),
        "overall_average_score": QuizAttempt.objects.aggregate(Avg("score"))[
            "score__avg"
        ]
        or 0,
        "overall_completion_percentage": (
            (
                TaskProgress.objects.filter(status="completed").count()
                / TaskProgress.objects.count()
            )
            * 100
            if TaskProgress.objects.count() > 0
            else 0
        ),
        "total_time_spent": TaskProgress.objects.aggregate(
            total_time=models.Sum("time_spent")
        )["total_time"]
        or 0,
    }
    return Response(data)


class StudentProgressView(APIView):
    permission_classes = [IsAuthenticated, IsEnrolledInCourse]

    def get(self, request, course_id):
        # Debug logging
        print(
            f"DEBUG: Accessing student progress for course {course_id} by user {request.user}"
        )

        # ...existing logic...
        return Response({"message": "Student progress data"})


def get_course_details(request, course_id):
    # Check if the user is enrolled
    is_enrolled = CourseEnrollment.objects.filter(
        user=request.user, course_id=course_id
    ).exists()

    if not is_enrolled:
        # Return limited course details for non-enrolled users
        course = Course.objects.get(id=course_id)
        return Response(
            {
                "course": {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                },
                "progress": [],
            }
        )

    # Fetch full course details including progress for enrolled users
    course = Course.objects.get(id=course_id)
    tasks = Task.objects.filter(course=course)
    progress = CourseProgress.objects.filter(user=request.user, course_id=course_id)
    return Response(
        {
            "course": {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "tasks": [{"id": task.id, "title": task.title} for task in tasks],
            },
            "progress": [{"task_id": p.task_id, "status": p.status} for p in progress],
        }
    )


class UserProfileAPI(APIView):
    """
    API endpoint to fetch the authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
