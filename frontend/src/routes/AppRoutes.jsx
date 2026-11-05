import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import PublicLayout from '../layouts/PublicLayout';
import AdminLayout from '../layouts/AdminLayout';
import TeacherLayout from '../layouts/TeacherLayout';
import StudentLayout from '../layouts/StudentLayout';

// Pages
import LandingPage from '../pages/landing/LandingPage';
import LoginPage from '../pages/auth/LoginPage';
import AdminOverviewPage from '../pages/admin/AdminOverviewPage';
import AdminUsersPage from '../pages/admin/AdminUsersPage';
import AdminAcademicsPage from '../pages/admin/AdminAcademicsPage';
import AdminLabsPage from '../pages/admin/AdminLabsPage';
import TeacherOverviewPage from '../pages/teacher/TeacherOverviewPage';
import TeacherAddSubjectPage from '../pages/teacher/TeacherAddSubjectPage';
import TeacherAttendancePortalPage from '../pages/teacher/TeacherAttendancePortalPage';
import StudentDashboardPage from '../pages/student/StudentDashboardPage';
import NotFoundPage from '../pages/errors/NotFoundPage';

// Protection
import ProtectedRoute from './ProtectedRoute';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>

      {/* Auth */}
      <Route path="/login" element={<LoginPage />} />

      {/* Admin Portal (Strictly 4 sections: Overview, User Accounts, Academics, Laboratories) */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminOverviewPage />} />
        <Route path="overview" element={<Navigate to="/admin" replace />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="academics" element={<AdminAcademicsPage />} />
        <Route path="laboratories" element={<AdminLabsPage />} />
      </Route>

      {/* Teacher Portal (Strictly 3 sections: Overview, Add Subject, Launch Attendance Portal) */}
      <Route
        path="/teacher"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TeacherOverviewPage />} />
        <Route path="overview" element={<Navigate to="/teacher" replace />} />
        <Route path="add-subject" element={<TeacherAddSubjectPage />} />
        <Route path="portal" element={<TeacherAttendancePortalPage />} />
      </Route>

      {/* Student Portal */}
      <Route
        path="/student"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboardPage />} />
      </Route>

      {/* 404 Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

