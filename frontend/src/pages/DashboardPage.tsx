import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Paper,
  Alert,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {useQuery} from '@tanstack/react-query';
import React, {useEffect} from 'react';

import {IUserProgress} from '@/types';
import {useAuth} from '@context/auth/AuthContext';
import ProgressIndicator from '@components/ProgressIndicator';
import {apiService} from '@services/api/apiService';

/**
 * Interface for progress response from API
 */
interface IProgressResponse {
  user_info: {
    id: string;
    username: string;
    display_name?: string;
    email?: string;
    [key: string]: any;
  };
  overall_stats: {
    courses_enrolled?: number;
    courses_completed?: number;
    completion_percentage?: number;
    total_tasks?: number;
    completed_tasks?: number;
    [key: string]: any;
  };
  courses: IUserProgress[];
}

/**
 * Student Dashboard Page
 *
 * Displays student progress information, overall statistics, and enrolled courses
 */
const Dashboard: React.FC = () => {
  const {user} = useAuth();

  useEffect(() => {
    console.info('Dashboard component mounted');
    console.info('User:', user);
    return () => {
      console.info('Dashboard component unmounted');
    };
  }, [user]);

  /**
   * Fetches user progress data from the API
   * @returns Complete progress response including user info, stats and course progress
   */
  const fetchUserProgress = async (): Promise<IProgressResponse> => {
    if (!user) {
      throw new Error('User not authenticated');
    }
    try {
      console.info('Fetching user progress for user ID:', user.id);
      const response = await apiService.get<IProgressResponse>('/api/v1/students/progress/');
      console.info('User progress response:', response);

      // If we get an array directly, adapt it to our expected format
      if (Array.isArray(response)) {
        console.warn('Received legacy array response format, adapting to expected structure');
        return {
          user_info: {
            id: user.id,
            username: user.username,
            display_name: user.display_name || user.username,
          },
          overall_stats: {
            courses_enrolled: response.length,
            completion_percentage: calculateAverageCompletion(response),
          },
          courses: response,
        };
      }

      // For well-formed response, ensure courses is an array
      if (response && !Array.isArray(response.courses)) {
        console.error('Error: Expected courses array in response', response);
        response.courses = [];
      }

      return response;
    } catch (error: any) {
      console.error('Error fetching user progress:', error.message);
      throw new Error('Failed to load progress data.');
    }
  };

  /**
   * Calculate average completion percentage across courses
   */
  const calculateAverageCompletion = (courses: IUserProgress[]): number => {
    if (!courses.length) return 0;
    const sum = courses.reduce((acc, course) => acc + (course.percentage || 0), 0);
    return Math.round(sum / courses.length);
  };

  // User progress data query using React Query
  const {
    data: progressResponse,
    isLoading,
    error,
  } = useQuery<IProgressResponse>({
    queryKey: ['userProgress'],
    queryFn: fetchUserProgress,
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{display: 'flex', justifyContent: 'center', mt: 4}}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{textAlign: 'center', mt: 4}}>
        <Alert severity="error" sx={{maxWidth: 600, mx: 'auto', mb: 3}}>
          {error instanceof Error ? error.message : 'An error occurred while loading data'}
        </Alert>
        <Typography variant="body1">
          Please try refreshing the page or contact support if the problem persists.
        </Typography>
      </Box>
    );
  }

  // Destructure the progress response data
  const {overall_stats: stats, courses: progressData = []} = progressResponse || {};

  return (
    <Box sx={{p: 3}}>
      <Typography variant="h4" gutterBottom>
        Student Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Welcome back, {user?.display_name || user?.username}!
      </Typography>

      {/* Overall Statistics Card */}
      <Paper elevation={2} sx={{p: 3, mt: 3}}>
        <Typography variant="h5" gutterBottom>
          Learning Overview
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined" sx={{height: '100%'}}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Enrolled Courses
                </Typography>
                <Typography variant="h4">{stats?.courses_enrolled || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined" sx={{height: '100%'}}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Completed Courses
                </Typography>
                <Typography variant="h4">{stats?.courses_completed || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined" sx={{height: '100%'}}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Overall Completion
                </Typography>
                <Typography variant="h4">{stats?.completion_percentage || 0}%</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined" sx={{height: '100%'}}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Completed Tasks
                </Typography>
                <Typography variant="h4">
                  {stats?.completed_tasks || 0}/{stats?.total_tasks || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Course Progress Section */}
      <Box sx={{mt: 4}}>
        <Typography variant="h5" gutterBottom>
          Course Progress
        </Typography>

        {!progressData || progressData.length === 0 ? (
          <Paper elevation={2} sx={{p: 3, textAlign: 'center'}}>
            <Typography variant="h6" gutterBottom>
              No Course Progress Yet
            </Typography>
            <Typography variant="body1" color="text.secondary">
              You have not started any courses yet. Enroll in courses to track your progress.
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {progressData.map((progress, idx) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                key={progress.id !== undefined ? progress.id : `progress-${idx}`}
              >
                <Paper
                  elevation={2}
                  sx={{p: 2, height: '100%', display: 'flex', flexDirection: 'column'}}
                >
                  <Typography variant="h6" gutterBottom align="center">
                    {progress.label || progress.course_name || `Course ${idx + 1}`}
                  </Typography>

                  <Box sx={{display: 'flex', justifyContent: 'center', my: 2}}>
                    <ProgressIndicator
                      value={progress.percentage || 0}
                      label={`${progress.percentage || 0}% Complete`}
                      size={120}
                    />
                  </Box>

                  <Divider sx={{my: 1}} />

                  <Box sx={{pt: 1}}>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Tasks Completed:</strong> {progress.completed_tasks || 0}/{progress.total_tasks || 0}
                    </Typography>
                    {progress.last_activity && (
                      <Typography variant="body2" color="text.secondary">
                        <strong>Last Activity:</strong> {new Date(progress.last_activity).toLocaleDateString()}
                      </Typography>
                    )}
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Quick Links Section */}
      <Box sx={{mt: 4}}>
        <Paper elevation={2} sx={{p: 3}}>
          <Typography variant="h5" gutterBottom>
            Quick Links
          </Typography>
          <Typography variant="body1" paragraph>
            Continue your learning journey by exploring the available courses and tasks.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Alert severity="info">
                Visit the <strong>Courses</strong> section to see your enrolled courses.
              </Alert>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Alert severity="info">
                Check the <strong>Tasks</strong> section for your pending learning tasks.
              </Alert>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    </Box>
  );
};

export default Dashboard;
