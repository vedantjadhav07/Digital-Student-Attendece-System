import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  GraduationCap,
  FlaskConical,
  ArrowRight,
  UserPlus,
  BookOpen,
  Building,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import StatCard from '../../components/common/StatCard';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import adminService from '../../services/adminService';

export default function AdminOverviewPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await adminService.getOverview();
      setData(res);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load administrative overview.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Administrative Overview</h1>
          <p className="text-xs text-light-muted dark:text-dark-muted">Loading platform telemetry...</p>
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400">
        <p className="font-semibold text-sm">Failed to load overview</p>
        <p className="text-xs mt-1">{error}</p>
        <Button size="sm" variant="secondary" onClick={fetchOverview} className="mt-3">
          Try Again
        </Button>
      </div>
    );
  }

  const stats = data?.stats || data || {};
  const totalStudents = data?.total_students ?? stats?.total_students ?? 0;
  const totalFaculty = data?.total_faculty ?? stats?.total_faculty ?? 0;
  const totalLaboratories = data?.total_labs ?? stats?.total_laboratories ?? 0;
  const totalDepartments = data?.total_departments ?? stats?.total_departments ?? 0;
  const totalSubjects = data?.total_subjects ?? stats?.total_subjects ?? 0;
  const recent_users = data?.recent_users || stats?.recent_users || [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Title & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            Administrative Overview
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Global monitoring of academic departments, faculty roster, and laboratory facilities.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/admin/users">
            <Button size="sm" variant="primary" icon={UserPlus}>
              Manage Accounts
            </Button>
          </Link>
        </div>
      </div>

      {/* EXACTLY 3 PRIMARY STAT CARDS PER INSTRUCTIONS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stat 1: Total Students */}
        <StatCard
          title="Total Students"
          value={totalStudents}
          subtitle="Enrolled active learners"
          icon={GraduationCap}
          badgeText="Active"
          badgeType="teal"
        />

        {/* Stat 2: Total Faculty */}
        <StatCard
          title="Total Faculty"
          value={totalFaculty}
          subtitle="Registered professors & teachers"
          icon={Users}
          badgeText="Teaching"
          badgeType="success"
        />

        {/* Stat 3: Total Computer Laboratories */}
        <StatCard
          title="Total Computer Laboratories"
          value={totalLaboratories}
          subtitle="Active campus computer labs"
          icon={FlaskConical}
          badgeText="Operational"
          badgeType="teal"
        />
      </div>

      {/* Academic Infrastructure Summary & Quick Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Academic Infrastructure & Recent Registrations */}
        <div className="lg:col-span-2 space-y-6">
          <Card
            title="Academic Infrastructure"
            subtitle="Departmental configuration and curriculum subject metrics"
            action={
              <Link to="/admin/academics" className="text-xs font-semibold text-brand-teal dark:text-brand-darkAction hover:underline flex items-center gap-1">
                View Academics <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                  <Building className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">Departments</span>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {totalDepartments}
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">Active Subjects</span>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {totalSubjects}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Recent Accounts Table */}
          <Card
            title="Recent User Registrations"
            subtitle="Latest student and faculty accounts created in Labora"
            action={
              <Link to="/admin/users" className="text-xs font-semibold text-brand-teal dark:text-brand-darkAction hover:underline flex items-center gap-1">
                All Users <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {recent_users.length === 0 ? (
              <p className="text-xs text-light-muted dark:text-dark-muted py-4 text-center">
                No user registrations recorded yet.
              </p>
            ) : (
              <div className="divide-y divide-light-border dark:divide-dark-border">
                {recent_users.map((u) => (
                  <div key={u.id} className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction font-bold flex items-center justify-center">
                        {(u.name || u.username)[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-light-text dark:text-dark-text">
                          {u.name || u.username}
                        </p>
                        <p className="text-light-muted dark:text-dark-muted text-[11px]">
                          @{u.username} &bull; {u.email}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={u.role === 'admin' ? 'teal' : u.role === 'teacher' ? 'info' : 'neutral'}
                        size="sm"
                      >
                        {u.role}
                      </Badge>
                      <Badge variant={u.is_active ? 'success' : 'danger'} size="sm" dot>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right 1 Col: Quick Control Shortcuts */}
        <div className="space-y-6">
          <Card title="Quick Management" subtitle="Frequent administrative tasks">
            <div className="space-y-3">
              <Link
                to="/admin/users"
                className="flex items-center justify-between p-3.5 rounded-lg border border-light-border dark:border-dark-border hover:border-brand-teal/50 hover:bg-slate-50 dark:hover:bg-[#2a383a] transition-all group shadow-subtle"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                    <Users className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-light-text dark:text-dark-text">User Accounts</p>
                    <p className="text-[11px] text-light-muted dark:text-dark-muted">Add or import students & faculty</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-light-muted group-hover:text-brand-teal dark:group-hover:text-brand-darkAction transition-colors" />
              </Link>

              <Link
                to="/admin/academics"
                className="flex items-center justify-between p-3.5 rounded-lg border border-light-border dark:border-dark-border hover:border-brand-teal/50 hover:bg-slate-50 dark:hover:bg-[#2a383a] transition-all group shadow-subtle"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                    <GraduationCap className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-light-text dark:text-dark-text">Academic Setup</p>
                    <p className="text-[11px] text-light-muted dark:text-dark-muted">Configure classes & subjects</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-light-muted group-hover:text-brand-teal dark:group-hover:text-brand-darkAction transition-colors" />
              </Link>

              <Link
                to="/admin/laboratories"
                className="flex items-center justify-between p-3.5 rounded-lg border border-light-border dark:border-dark-border hover:border-brand-teal/50 hover:bg-slate-50 dark:hover:bg-[#2a383a] transition-all group shadow-subtle"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <FlaskConical className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-light-text dark:text-dark-text">Laboratories</p>
                    <p className="text-[11px] text-light-muted dark:text-dark-muted">Capacity (30/60/90) & IP subnets</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-light-muted group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
              </Link>
            </div>
          </Card>

          {/* System Security Status */}
          <Card title="System Integrity" subtitle="Platform runtime status">
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-light-border dark:border-dark-border">
                <span className="text-light-muted dark:text-dark-muted">Database Storage</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> SQLite WAL Mode
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-light-border dark:border-dark-border">
                <span className="text-light-muted dark:text-dark-muted">Auth Security</span>
                <span className="font-semibold text-brand-teal dark:text-brand-darkAction flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Argon2id + CSRF
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-light-muted dark:text-dark-muted">Real-time Gateway</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Socket.IO Active
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
