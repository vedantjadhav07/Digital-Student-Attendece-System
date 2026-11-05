import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Radio,
  BookOpen,
  Users,
  Clock,
  ArrowRight,
  PlayCircle,
  CheckCircle2,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import StatCard from '../../components/common/StatCard';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import teacherService from '../../services/teacherService';

export default function TeacherOverviewPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTeacherData();
  }, []);

  const loadTeacherData = async () => {
    try {
      setIsLoading(true);
      const res = await teacherService.getOverview();
      setData(res);
    } catch (err) {
      toast.error('Failed to load faculty dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Faculty Dashboard</h1>
          <p className="text-xs text-light-muted dark:text-dark-muted">Loading assigned curriculum and active sessions...</p>
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  const { stats, assigned_subjects = [], recent_sessions = [], active_session } = data || {};

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            Faculty Overview
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Real-time laboratory sessions, subject assignments, and student participation metrics.
          </p>
        </div>
        <Link to="/teacher/portal">
          <Button size="sm" variant="primary" icon={Radio}>
            Attendance Portal
          </Button>
        </Link>
      </div>

      {/* Active Session Alert Banner (if running) */}
      {active_session && (
        <div className="p-4 rounded-lg bg-brand-deep text-white border border-brand-teal/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-brand-teal text-white flex items-center justify-center">
              <Radio className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-brand-soft uppercase tracking-wider">
                  Live Laboratory Session In Progress
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-ping" />
              </div>
              <p className="text-sm font-semibold text-white">
                {active_session.subject_name} &bull; {active_session.lab_name}
              </p>
              <p className="text-xs text-white/80">
                Status: {active_session.status} &bull; {active_session.present_count || 0} students checked in
              </p>
            </div>
          </div>
          <Link to="/teacher/portal">
            <Button size="sm" variant="primary">
              Open Live Monitor <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>
      )}

      {/* Primary Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Assigned Subjects"
          value={stats?.total_subjects ?? assigned_subjects.length}
          subtitle="Active curriculum teaching load"
          icon={BookOpen}
          badgeText="Assigned"
          badgeType="teal"
        />

        <StatCard
          title="Total Lab Sessions"
          value={stats?.total_sessions ?? recent_sessions.length}
          subtitle="Completed laboratory practicals"
          icon={Clock}
          badgeText="Conducted"
          badgeType="success"
        />

        <StatCard
          title="Total Student Attendances"
          value={stats?.total_attendances ?? data?.total_students ?? 0}
          subtitle="Logged digital check-ins"
          icon={Users}
          badgeText="Verified"
          badgeType="teal"
        />
      </div>

      {/* Assigned Subjects & Recent Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Assigned Subjects */}
        <Card
          title="My Teaching Portfolio"
          subtitle="Subjects assigned to you for lab attendance"
          action={
            <Link to="/teacher/add-subject" className="text-xs font-semibold text-brand-teal dark:text-brand-darkAction hover:underline flex items-center gap-1">
              Add Subject <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          }
        >
          {assigned_subjects.length === 0 ? (
            <div className="text-center py-6">
              <BookOpen className="w-8 h-8 text-light-muted mx-auto mb-2 opacity-50" />
              <p className="text-xs text-light-muted dark:text-dark-muted">
                No subjects assigned to your account yet.
              </p>
              <Link to="/teacher/add-subject">
                <Button size="sm" variant="secondary" className="mt-3">
                  Assign Subjects
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {assigned_subjects.map((sub) => (
                <div
                  key={sub.id}
                  className="p-3.5 rounded-lg border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg flex items-center justify-between shadow-subtle"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-md bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center font-bold text-xs">
                      {sub.code?.substring(0, 3) || 'SUB'}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-light-text dark:text-dark-text">
                        {sub.name}
                      </h4>
                      <p className="text-[11px] text-light-muted dark:text-dark-muted font-mono">
                        {sub.code} &bull; Semester {sub.semester}
                      </p>
                    </div>
                  </div>
                  <Badge variant="teal" size="sm">
                    {sub.department_code || 'Enrolled'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Lab Sessions */}
        <Card
          title="Recent Laboratory Sessions"
          subtitle="Summary of recent attendance logs"
        >
          {recent_sessions.length === 0 ? (
            <div className="text-center py-6">
              <Calendar className="w-8 h-8 text-light-muted mx-auto mb-2 opacity-50" />
              <p className="text-xs text-light-muted dark:text-dark-muted">
                No lab sessions conducted yet. Launch your first session!
              </p>
              <Link to="/teacher/portal">
                <Button size="sm" variant="primary" className="mt-3">
                  Launch Portal
                </Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-light-border dark:divide-dark-border">
              {recent_sessions.map((sess) => (
                <div key={sess.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-light-text dark:text-dark-text">
                      {sess.subject_name}
                    </p>
                    <p className="text-[11px] text-light-muted dark:text-dark-muted">
                      {sess.lab_name} &bull; {new Date(sess.start_time).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-brand-teal dark:text-brand-darkAction">
                      {sess.present_count || 0} students
                    </span>
                    <Badge
                      variant={sess.status === 'completed' ? 'success' : sess.status === 'active' ? 'teal' : 'neutral'}
                      size="sm"
                    >
                      {sess.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

