import CssBaseline from '@mui/material/CssBaseline';
import {ThemeProvider} from '@mui/material/styles';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import React from 'react';

import ErrorBoundary from './components/ErrorBoundary';
import {ErrorProvider} from './components/ErrorNotifier/ErrorProvider';
import NavigationBar from './components/NavigationBar';
import AppRoutes from './routes/AppRoutes.tsx';
import {theme} from './styles/theme.ts';

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <ErrorProvider>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <NavigationBar />
            <AppRoutes />
          </ThemeProvider>
        </ErrorProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
};

export default App;
