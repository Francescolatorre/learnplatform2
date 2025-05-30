import {Button, Container, Typography, Box, TextField, MenuItem, CircularProgress, Alert} from '@mui/material';
import React, {useState} from 'react';
import {useNavigate, useParams} from 'react-router-dom';

import {useAuth} from '@context/auth/AuthContext';
import {courseService} from 'src/services/resources/courseService';
import {ICourse} from 'src/types/course';

const EditCourse: React.FC = () => {
  const navigate = useNavigate();
  const {courseId} = useParams<{courseId: string}>();
  const {getUserRole, setError} = useAuth();
  const userRole = getUserRole(); // Use utility function

  const [courseData, setCourseData] = useState<Partial<ICourse>>({
    title: 'test',
    description: 'test description',
    status: 'draft',
    visibility: 'private',
  });
  const [isLoading, setIsLoading] = useState(false);
  const error = null;


  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {name, value} = e.target;
    setCourseData(prev => ({...prev, [name]: value}));
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await courseService.updateCourse(courseId!, courseData as ICourse);
      navigate(userRole === 'admin' ? '/admin/courses' : '/instructor/courses');
    } catch (err: unknown) {
      console.error('Failed to save course details:', err);
      setError('Failed to save course details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    navigate(userRole === 'admin' ? '/admin/courses' : '/instructor/courses');
  };

  if (isLoading) {
    return (
      <Box
        sx={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{p: 3}}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        {userRole === 'admin' ? 'Edit Course (Admin)' : 'Edit Course (Instructor)'}
      </Typography>
      <Box component="form" sx={{mt: 3}}>
        <TextField
          label="Title"
          name="title"
          value={courseData.title || ''}
          onChange={handleInputChange}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Description"
          name="description"
          value={courseData.description || ''}
          onChange={handleInputChange}
          fullWidth
          margin="normal"
          multiline
          rows={4}
        />
        <TextField
          label="Status"
          name="status"
          value={courseData.status || ''}
          onChange={handleInputChange}
          select
          fullWidth
          margin="normal"
        >
          <MenuItem value="draft">Draft</MenuItem>
          <MenuItem value="published">Published</MenuItem>
        </TextField>
        <TextField
          label="Visibility"
          name="visibility"
          value={courseData.visibility || ''}
          onChange={handleInputChange}
          select
          fullWidth
          margin="normal"
        >
          <MenuItem value="private">Private</MenuItem>
          <MenuItem value="public">Public</MenuItem>
        </TextField>
        <Box sx={{mt: 3}}>
          <Button variant="contained" color="primary" sx={{mr: 2}} onClick={handleSave}>
            Save
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleCancel}>
            Cancel
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default EditCourse;
