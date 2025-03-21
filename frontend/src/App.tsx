import React, { use } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from '@theme/theme';
import { AuthProvider } from '@features/auth/AuthContext';
import ErrorBoundary from '@components/ErrorBoundary';
import LoginForm from '@features/auth/LoginForm';
import RegisterForm from '@features/auth/RegisterForm';
import { MainLayout } from '@components/layout/MainLayout';
import Dashboard from '@features/dashboard/Dashboard';
import ProgressTrackingUI from '@features/dashboard/ProgressTrackingUI';
import Profile from '@features/profile/Profile';
import CoursesPage from '@features/courses/CoursesPage';
import CourseTasksPage from '@features/courses/CourseTasksPage';
import CourseEditPage from '@features/courses/CourseEditPage';
import InstructorViews from '@features/instructor/InstructorViews';
import CourseDetailsPage from './pages/CourseDetailsPage';
import CourseEnrollmentPage from '@features/courses/CourseEnrollmentPage';
import { useAuth } from '@features/auth/AuthContext';

type Task = {
  title: string;
  status: string;
  createdDate: string;
  creator: string;
  description: string;
  actions: string;
  courseId: string;
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const isTokenAvailable = localStorage.getItem('access_token') !== null;

  // Use both the context state and token existence for most reliable check
  return (isAuthenticated || isTokenAvailable) ? <>{children}</> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
  const queryClient = new QueryClient();

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Routes>

              <Route path="/login" element={<LoginForm />} />
              <Route path="/register" element={<RegisterForm />} />
              <Route path="/dashboard" element={<ProtectedRoute><MainLayout><Dashboard /></MainLayout></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><MainLayout><Profile /></MainLayout></ProtectedRoute>} />
              <Route path="/courses" element={<ProtectedRoute><MainLayout><CoursesPage /></MainLayout></ProtectedRoute>} />
              <Route path="/courses/:courseId" element={<ProtectedRoute><MainLayout><CourseEnrollmentPage /></MainLayout></ProtectedRoute>} />
              <Route path="/courses/:courseId/edit" element={<ProtectedRoute><MainLayout><CourseEditPage /></MainLayout></ProtectedRoute>} />
              <Route path="/courses-old/:courseId" element={<ProtectedRoute><MainLayout><CourseDetailsPage /></MainLayout></ProtectedRoute>} />
              <Route path="/courses/:courseId/tasks" element={<ProtectedRoute><MainLayout><CourseTasksPage /></MainLayout></ProtectedRoute>} />
              <Route path="/progress-tracking/:courseId" element={<ProtectedRoute><MainLayout><ProgressTrackingUI courseId={useParams().courseId} /></MainLayout></ProtectedRoute>} />
              <Route path="/instructor" element={<ProtectedRoute><MainLayout><InstructorViews /></MainLayout></ProtectedRoute>} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
