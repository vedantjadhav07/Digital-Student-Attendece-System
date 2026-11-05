import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  FlaskConical,
  BookPlus,
  Radio,
  ChevronLeft,
  ChevronRight,
  LogOut,
  X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({
  role = 'admin',
  isCollapsed = false,
  setIsCollapsed,
  mobileOpen = false,
  setMobileOpen,
}) {
  const { user, logout } = useAuth();
  const location = useLocation();

  // Strict role navigation items per requirements
  const adminNavItems = [
    { label: 'Overview', path: '/admin', icon: LayoutDashboard },
    { label: 'User Accounts', path: '/admin/users', icon: Users },
    { label: 'Academics', path: '/admin/academics', icon: GraduationCap },
    { label: 'Laboratories', path: '/admin/laboratories', icon: FlaskConical },
  ];

  const teacherNavItems = [
    { label: 'Overview', path: '/teacher', icon: LayoutDashboard },
    { label: 'Add Subject', path: '/teacher/add-subject', icon: BookPlus },
    { label: 'Launch Attendance Portal', path: '/teacher/portal', icon: Radio },
  ];

  const studentNavItems = [
    { label: 'Dashboard', path: '/student', icon: LayoutDashboard },
  ];

  const navItems =
    role === 'admin'
      ? adminNavItems
      : role === 'teacher'
      ? teacherNavItems
      : studentNavItems;

  const NavContent = () => (
    <div className="flex flex-col h-full justify-between">
      <div>
        {/* Brand Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-light-border dark:border-dark-border">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 min-w-8 rounded-md bg-brand-deep p-1 flex items-center justify-center shrink-0">
              <img src="/logo.svg" alt="Labora" className="w-full h-full object-contain" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="text-sm font-bold tracking-tight text-light-text dark:text-dark-text leading-tight">
                  Labora
                </span>
                <span className="text-[10px] font-medium tracking-wide text-light-muted dark:text-dark-muted uppercase">
                  {role} Portal
                </span>
              </div>
            )}
          </div>
          {/* Mobile close button */}
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1 rounded-md text-light-muted hover:text-light-text hover:bg-light-secondary dark:text-dark-muted dark:hover:text-dark-text dark:hover:bg-dark-secondary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation items */}
        <nav className="p-2.5 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path !== `/${role}` && location.pathname.startsWith(item.path));

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                title={isCollapsed ? item.label : undefined}
                className={`relative group flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-teal text-white dark:bg-brand-teal/25 dark:text-brand-darkAction font-semibold'
                    : 'text-light-muted dark:text-dark-muted hover:bg-light-secondary dark:hover:bg-dark-secondary hover:text-light-text dark:hover:text-dark-text'
                }`}
              >
                <Icon
                  className={`w-4 h-4 min-w-4 ${
                    isActive ? 'text-white dark:text-brand-darkAction' : 'text-current'
                  }`}
                />
                {!isCollapsed && (
                  <span className="truncate whitespace-nowrap">{item.label}</span>
                )}
                {/* Floating tooltip on collapsed */}
                {isCollapsed && (
                  <div className="fixed left-[76px] hidden group-hover:flex items-center px-2 py-1 text-xs font-medium rounded-md bg-dark-surface text-dark-text shadow-modal border border-dark-border z-50 whitespace-nowrap pointer-events-none">
                    {item.label}
                  </div>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer with Collapse Toggle & User info */}
      <div className="p-2.5 border-t border-light-border dark:border-dark-border space-y-2">
        {!isCollapsed && user && (
          <div className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-md bg-light-secondary dark:bg-dark-secondary">
            <div className="w-7 h-7 min-w-7 rounded-md bg-brand-deep text-white font-bold text-xs flex items-center justify-center">
              {(user.name || user.username || 'U')[0].toUpperCase()}
            </div>
            <div className="flex flex-col truncate">
              <span className="text-xs font-medium text-light-text dark:text-dark-text truncate">
                {user.name || user.username}
              </span>
              <span className="text-[10px] text-light-muted dark:text-dark-muted uppercase">
                {user.role}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between gap-1">
          <button
            onClick={logout}
            title="Log Out"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 text-xs font-medium transition-colors w-full"
          >
            <LogOut className="w-3.5 h-3.5 min-w-3.5" />
            {!isCollapsed && <span>Sign Out</span>}
          </button>

          {/* Desktop collapse toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden lg:flex items-center justify-center p-1.5 rounded-md text-light-muted dark:text-dark-muted hover:bg-light-secondary dark:hover:bg-dark-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:block fixed top-0 left-0 bottom-0 z-30 bg-light-surface dark:bg-dark-surface border-r border-light-border dark:border-dark-border transition-all duration-200 ${
          isCollapsed ? 'w-[68px]' : 'w-60'
        }`}
      >
        <NavContent />
      </aside>

      {/* Mobile Backdrop & Drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-brand-ink/50 dark:bg-black/70 backdrop-blur-[2px] lg:hidden transition-opacity"
          onClick={() => setMobileOpen(false)}
        >
          <div
            className="w-60 h-full bg-light-surface dark:bg-dark-surface border-r border-light-border dark:border-dark-border shadow-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <NavContent />
          </div>
        </div>
      )}
    </>
  );
}
