import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Download,
  Calendar,
  Cpu,
  BookOpen,
  Radio,
  FileSpreadsheet,
  Building,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Input from '../../components/common/Input';
import Table from '../../components/common/Table';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import studentService from '../../services/studentService';

export default function StudentDashboardPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [workstationNum, setWorkstationNum] = useState('1');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      const res = await studentService.getDashboard();
      setData(res);
      if (res.active_session?.my_workstation) {
        setWorkstationNum(res.active_session.my_workstation.toString());
      }
    } catch (err) {
      toast.error('Failed to load student dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkAttendance = async () => {
    if (!data?.active_session) return;
    if (!workstationNum) {
      toast.error('Please specify your current workstation number.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await studentService.markAttendance({
        session_id: data.active_session.id,
        workstation_number: parseInt(workstationNum, 10),
      });
      toast.success(res.message || 'Attendance verified successfully!');
      loadDashboard();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit attendance.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadExcel = async () => {
    try {
      toast.info('Generating your verified attendance report...');
      const res = await studentService.downloadExcel();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Student_Attendance_${data?.student?.roll_number || 'export'}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Attendance report downloaded.');
    } catch (err) {
      toast.error('Failed to export personal report.');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Student Portal</h1>
          <p className="text-xs text-light-muted">Synchronizing student records...</p>
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  const student = data?.student;
  const overall_attendance = data?.stats?.overall_percentage ?? data?.overall_attendance ?? 0;
  const subject_attendance = data?.stats?.subject_stats ?? data?.subject_attendance ?? [];
  const active_session = data?.active_session;
  const recent_logs = data?.stats?.recent_logs ?? data?.recent_logs ?? [];
  const isDefaulter = overall_attendance < 75;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Student Profile Banner */}
      <div className="p-6 rounded-lg bg-brand-deep text-white border border-brand-teal/30 shadow-card relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-lg bg-brand-teal/30 border border-brand-soft/30 flex items-center justify-center font-extrabold text-2xl text-brand-soft shadow-inner">
              {(student?.full_name || student?.name || student?.username || 'S')[0].toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-brand-soft">
                  Student Portal
                </span>
                <span className="text-[10px] bg-white/15 px-2 py-0.5 rounded font-mono text-white">
                  {student?.roll_number || student?.username || 'ROLL-N/A'}
                </span>
              </div>
              <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                {student?.full_name || student?.name || 'Student Name'}
              </h1>
              <p className="text-xs text-white/80 mt-1">
                {student?.department || student?.department_name || 'Engineering'} &bull; Semester {student?.semester || 1}
              </p>
            </div>
          </div>

          {/* Quick Excel Export button */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDownloadExcel}
              className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-brand-teal hover:bg-[#2E6561] text-white border border-brand-soft/30 transition-colors shadow-subtle"
            >
              <Download className="w-4 h-4 text-white" />
              <span>Export Attendance (.xlsx)</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Defaulter Warning Banner (if <75%) */}
      {isDefaulter && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 flex items-center gap-3 animate-fadeIn">
          <AlertTriangle className="w-5 h-5 min-w-5 text-rose-500" />
          <div className="text-xs">
            <span className="font-bold">Attendance Defaulter Warning:</span> Your overall attendance is currently{' '}
            <strong className="underline">{overall_attendance}%</strong>, which is below the mandatory 75% academic requirement.
            Please attend remaining practical sessions to avoid exam detention.
          </div>
        </div>
      )}

      {/* 3. ACTIVE SESSION CHECK-IN CARD (Single-Click Check-in) */}
      {active_session ? (
        <Card className="p-6 border-brand-teal/40 bg-brand-soft/10 dark:bg-brand-teal/10 shadow-card relative overflow-hidden">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-brand-deep text-brand-soft flex items-center justify-center shadow-subtle">
                <Radio className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-brand-teal dark:text-brand-darkAction uppercase tracking-wider">
                    Active Laboratory Attendance Open
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-ping" />
                </div>
                <h3 className="text-lg font-bold text-light-text dark:text-dark-text mt-0.5">
                  {active_session.subject_name}
                </h3>
                <p className="text-xs text-light-muted dark:text-dark-muted">
                  Lab: {active_session.lab_name} &bull; Faculty: {active_session.teacher_name || 'Assigned Instructor'}
                </p>
              </div>
            </div>

            {/* Check-in Action / Status */}
            <div>
              {active_session.already_marked ? (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                  <div className="text-xs">
                    <span className="font-bold block">Attendance Verified</span>
                    <span>Logged at WS-{active_session.my_workstation || '01'}</span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-32">
                    <Input
                      label="Workstation No."
                      type="number"
                      min="1"
                      max="90"
                      value={workstationNum}
                      onChange={(e) => setWorkstationNum(e.target.value)}
                      className="py-1.5 text-xs text-center font-bold"
                    />
                  </div>
                  <div className="pt-5">
                    <Button
                      variant="primary"
                      size="md"
                      isLoading={isSubmitting}
                      onClick={handleMarkAttendance}
                      icon={CheckCircle2}
                    >
                      Check In Now
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-5 border-dashed border-light-border dark:border-dark-border text-center">
          <p className="text-xs text-light-muted dark:text-dark-muted">
            No laboratory attendance session is currently open for your division. The check-in button will activate automatically when your faculty launches a session.
          </p>
        </Card>
      )}

      {/* 4. OVERALL ATTENDANCE & SUBJECT PROGRESS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 1 Col: Overall Attendance Card */}
        <Card className="p-6 text-center flex flex-col items-center justify-center">
          <span className="text-xs font-bold uppercase tracking-wider text-light-muted dark:text-dark-muted mb-2">
            Overall Attendance Rate
          </span>

          {/* Metric Ring */}
          <div className="relative w-36 h-36 rounded-full flex items-center justify-center my-3">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="72"
                cy="72"
                r="60"
                stroke="currentColor"
                strokeWidth="10"
                fill="transparent"
                className="text-light-secondary dark:text-dark-secondary"
              />
              <circle
                cx="72"
                cy="72"
                r="60"
                stroke="currentColor"
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={377}
                strokeDashoffset={377 - (377 * (overall_attendance || 0)) / 100}
                className={isDefaulter ? 'text-rose-500 transition-all duration-1000' : 'text-brand-teal dark:text-brand-darkAction transition-all duration-1000'}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={`text-3xl font-extrabold ${isDefaulter ? 'text-rose-600 dark:text-rose-400' : 'text-brand-teal dark:text-brand-darkAction'}`}>
                {overall_attendance}%
              </span>
              <span className="text-[10px] text-light-muted dark:text-dark-muted uppercase font-semibold">
                {isDefaulter ? 'At Risk' : 'Good Standing'}
              </span>
            </div>
          </div>

          <Badge variant={isDefaulter ? 'danger' : 'success'} size="sm" dot className="mt-2">
            {isDefaulter ? 'Below 75% Requirement' : 'Criteria Fulfilled (≥75%)'}
          </Badge>
        </Card>

        {/* Right 2 Cols: Subject-Wise Attendance Breakdown */}
        <div className="lg:col-span-2">
          <Card
            title="Curriculum Subjects Attendance"
            subtitle="Detailed attendance percentages for registered laboratory courses"
          >
            {subject_attendance.length === 0 ? (
              <p className="text-xs text-light-muted dark:text-dark-muted py-6 text-center">
                No enrolled laboratory courses found.
              </p>
            ) : (
              <div className="space-y-4">
                {subject_attendance.map((sub, idx) => {
                  const subDefaulter = (sub.percentage || 0) < 75;
                  const subName = sub.name || sub.subject_name || 'Subject';
                  const subCode = sub.code || sub.subject_code || 'CODE';
                  return (
                    <div key={sub.subject_id || idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-light-text dark:text-dark-text">
                          {subName}{' '}
                          <span className="text-[11px] font-mono text-light-muted dark:text-dark-muted">
                            ({subCode})
                          </span>
                        </span>
                        <span className="font-bold">
                          {sub.attended || 0} / {sub.total || 0} sessions ({sub.percentage || 0}%)
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-light-secondary dark:bg-dark-secondary overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            subDefaulter
                              ? 'bg-rose-500'
                              : 'bg-brand-teal dark:bg-brand-darkAction'
                          }`}
                          style={{ width: `${Math.min(sub.percentage || 0, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* 5. PERSONAL RECENT ATTENDANCE LOGS */}
      <Card
        title="Personal Attendance Log History"
        subtitle="Recent verified laboratory check-in records"
        action={
          <Button
            size="sm"
            variant="ghost"
            icon={Download}
            onClick={handleDownloadExcel}
          >
            Export All
          </Button>
        }
      >
        <Table
          headers={['Date & Time', 'Curriculum Subject', 'Laboratory', 'Workstation', 'Status']}
          isEmpty={recent_logs.length === 0}
          emptyText="No personal attendance logs recorded yet."
        >
          {recent_logs.map((log, idx) => (
            <tr key={log.id || idx} className="hover:bg-slate-50 dark:hover:bg-[#202b2c]/80 transition-colors">
              <td className="px-4 py-3 text-xs text-light-muted dark:text-dark-muted">
                {log.timestamp || (log.date ? new Date(log.date).toLocaleDateString() : 'Recent')}
              </td>
              <td className="px-4 py-3 text-xs font-semibold text-light-text dark:text-dark-text">
                {log.subject_name || 'Practical Lab'}
              </td>
              <td className="px-4 py-3 text-xs text-light-muted dark:text-dark-muted">
                {log.lab_name || 'Computer Lab'}
              </td>
              <td className="px-4 py-3 text-xs font-mono font-semibold text-brand-teal dark:text-brand-darkAction">
                WS-{(log.seat_number || log.workstation_number || 1).toString().padStart(2, '0')}
              </td>
              <td className="px-4 py-3">
                <Badge
                  variant={(log.status || 'present').toLowerCase() === 'present' ? 'success' : 'danger'}
                  size="sm"
                  dot
                >
                  {(log.status || 'PRESENT').toUpperCase()}
                </Badge>
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
}
