import React, {useEffect} from 'react';

import {authEventService} from './AuthEventService';
import {AuthEventType, AuthInterceptorProps} from './types';

// Keine Abhängigkeit mehr zu AuthContext!
export const AuthInterceptor: React.FC<AuthInterceptorProps> = ({
    onAuthFailure,
    onRefreshToken
}) => {
    useEffect(() => {
        // Setup API-Interceptors (z.B. mit axios)
        const setupInterceptors = () => {
            // Beispiel mit axios:
            // axios.interceptors.response.use(
            //   (response) => response,
            //   async (error) => {
            //     if (error.response?.status === 401) {
            //       try {
            //         const newToken = await onRefreshToken();
            //         if (newToken) {
            //           // Token zur ursprünglichen Anfrage hinzufügen und wiederholen
            //           error.config.headers.Authorization = `Bearer ${newToken}`;
            //           return axios(error.config);
            //         }
            //       } catch (refreshError) {
            //         authEventService.publish({ type: AuthEventType.AUTH_ERROR });
            //         onAuthFailure();
            //       }
            //     }
            //     return Promise.reject(error);
            //   }
            // );
        };

        setupInterceptors();
    }, [onAuthFailure, onRefreshToken]);

    // Der Interceptor rendert nichts, er fügt nur Logik hinzu
    return null;
};
