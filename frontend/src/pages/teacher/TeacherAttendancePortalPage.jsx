import React, { useState, useEffect, useRef } from 'react';
import {
  Radio,
  Play,
  Pause,
  Clock,
  PlusCircle,
  Square,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Cpu,
  BarChart3,
  RefreshCw,
  Search,
  ExternalLink
} from 'lucide-react';
import { io } from 'socket.io-client';
import { toast } from 'sonner';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Select from '../../components/common/Select';
import Input from '../../components/common/Input';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import Table from '../../components/common/Table';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import teacherService from '../../services/teacherService';

const CHART_COLORS = ['#397C78', '#163B42', '#10B981', '#E11D48'];

export default function TeacherAttendancePortalPage() {
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'analysis'
  const [session, setSession] = useState(null);
  const [workstations, setWorkstations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [remainingTime, setRemainingTime] = useState(0);

  // Launcher state
  const [showLaunchModal, setShowLaunchModal] = useState(false);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [laboratories, setLaboratories] = useState([]);
  const [launchForm, setLaunchForm] = useState({
    subject_id: '',
    laboratory_id: '',
    duration: '60',
    capacity: '30',
  });
  const [isLaunching, setIsLaunching] = useState(false);

  // Analysis state
  const [analysisData, setAnalysisData] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisSearch, setAnalysisSearch] = useState('');

  // Confirm Stop Modal
  const [showStopModal, setShowStopModal] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  // Selected workstation modal
  const [selectedSeat, setSelectedSeat] = useState(null);

  const socketRef = useRef(null);

  useEffect(() => {
    loadPortalData();
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Timer countdown
  useEffect(() => {
    if (!session || session.status !== 'active' || remainingTime <= 0) return;
    const interval = setInterval(() => {
      setRemainingTime((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [session, remainingTime]);

  const loadPortalData = async () => {
    try {
      setIsLoading(true);
      const overview = await teacherService.getOverview();
      const subs = overview.assigned_subjects || [];
      setAssignedSubjects(subs);

      if (overview.active_session) {
        await loadSessionDetails(overview.active_session.id);
      } else {
        setSession(null);
        // Load labs for launching
        const subjRes = await teacherService.getSubjects().catch(() => ({}));
        if (subs.length > 0) {
          setLaunchForm((prev) => ({ ...prev, subject_id: subs[0].id }));
        }
      }
    } catch (err) {
      toast.error('Failed to load attendance portal state.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadSessionDetails = async (sessionId) => {
    try {
      const liveData = await teacherService.getSessionLive(sessionId);
      setSession(liveData.session);
      setWorkstations(liveData.workstations || []);
      setRemainingTime(liveData.session.remaining_seconds || 0);

      // Setup Socket.IO real-time listener
      setupSocket(sessionId);
    } catch (err) {
      toast.error('Failed to connect to live session.');
    }
  };

  const setupSocket = (sessionId) => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }

    const socket = io('/', {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => {
      socket.emit('join_session', { session_id: sessionId });
    });

    socket.on('student_checkin', (data) => {
      toast.success(`${data.student_name || 'Student'} checked in at WS-${data.workstation_number || data.workstation_id}!`);
      // Update workstation in local state
      setWorkstations((prev) =>
        prev.map((ws) =>
          ws.workstation_number === data.workstation_number || ws.id === data.workstation_id
            ? {
                ...ws,
                status: 'occupied',
                student_name: data.student_name,
                roll_number: data.roll_number,
                checked_in_at: data.checked_in_at || new Date().toISOString(),
                ip_address: data.ip_address,
              }
            : ws
        )
      );
      setSession((prev) => (prev ? { ...prev, present_count: (prev.present_count || 0) + 1 } : prev));
    });

    socket.on('session_paused', () => {
      toast.info('Session paused.');
      setSession((prev) => (prev ? { ...prev, status: 'paused' } : prev));
    });

    socket.on('session_resumed', () => {
      toast.info('Session resumed.');
      setSession((prev) => (prev ? { ...prev, status: 'active' } : prev));
    });

    socket.on('session_stopped', () => {
      toast.warning('Session has ended.');
      setSession((prev) => (prev ? { ...prev, status: 'completed' } : prev));
    });

    socketRef.current = socket;
  };

  const handleLaunchSession = async (e) => {
    e.preventDefault();
    if (!launchForm.subject_id) {
      toast.error('Please select a subject to launch.');
      return;
    }

    try {
      setIsLaunching(true);
      const res = await teacherService.startSession(launchForm);
      toast.success('Attendance session launched successfully!');
      setShowLaunchModal(false);
      await loadSessionDetails(res.session_id);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to start session.');
    } finally {
      setIsLaunching(false);
    }
  };

  const handleTogglePause = async () => {
    if (!session) return;
    try {
      const res = await teacherService.pauseSession(session.id);
      setSession((prev) => ({ ...prev, status: res.status }));
      toast.info(`Session is now ${res.status}.`);
    } catch (err) {
      toast.error('Failed to change session status.');
    }
  };

  const handleExtendDuration = async () => {
    if (!session) return;
    try {
      const res = await teacherService.extendSession(session.id, 10);
      setRemainingTime((prev) => prev + 600);
      toast.success('Session extended by 10 minutes!');
    } catch (err) {
      toast.error('Failed to extend session.');
    }
  };

  const handleStopSession = async () => {
    if (!session) return;
    try {
      setIsStopping(true);
      await teacherService.stopSession(session.id);
      toast.success('Attendance session closed.');
      setShowStopModal(false);
      loadPortalData();
    } catch (err) {
      toast.error('Failed to close session.');
    } finally {
      setIsStopping(false);
    }
  };

  // Switch to Analysis tab and fetch analytics
  const handleTabChange = async (tab) => {
    setActiveTab(tab);
    if (tab === 'analysis' && (!analysisData || session)) {
      try {
        setAnalysisLoading(true);
        const subjId = session?.subject_id || (assignedSubjects[0]?.id);
        if (subjId) {
          const res = await teacherService.getStudentAnalysis(subjId);
          setAnalysisData(res);
        }
      } catch (err) {
        toast.error('Failed to load student analysis.');
      } finally {
        setAnalysisLoading(false);
      }
    }
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Attendance Portal</h1>
          <p className="text-xs text-light-muted">Initializing telemetry stream...</p>
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text flex items-center gap-3">
            Attendance Portal
            {session && session.status === 'active' && (
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            )}
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Real-time interactive workstation monitoring and comprehensive student attendance analytics.
          </p>
        </div>

        {/* Action button if no active session */}
        {!session && (
          <Button
            size="md"
            variant="primary"
            icon={Radio}
            onClick={() => setShowLaunchModal(true)}
          >
            Launch Lab Session
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 p-1 bg-light-bg dark:bg-dark-bg rounded-lg border border-light-border dark:border-dark-border w-fit">
        <button
          onClick={() => handleTabChange('live')}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold transition-all ${
            activeTab === 'live'
              ? 'bg-light-surface dark:bg-brand-teal/20 text-brand-teal dark:text-brand-darkAction shadow-subtle border border-light-border dark:border-brand-teal/30 font-bold'
              : 'text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
          }`}
        >
          <Radio className="w-4 h-4" />
          Live Monitoring
        </button>
        <button
          onClick={() => handleTabChange('analysis')}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold transition-all ${
            activeTab === 'analysis'
              ? 'bg-light-surface dark:bg-brand-teal/20 text-brand-teal dark:text-brand-darkAction shadow-subtle border border-light-border dark:border-brand-teal/30 font-bold'
              : 'text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Student Analysis & Defaulters
        </button>
      </div>

      {/* TAB 1: LIVE MONITORING */}
      {activeTab === 'live' && (
        <>
          {!session ? (
            <Card className="p-12 text-center flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center mb-4">
                <Radio className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-light-text dark:text-dark-text">
                No Active Attendance Session
              </h3>
              <p className="text-xs text-light-muted dark:text-dark-muted max-w-md mt-1 mb-6">
                Ready to begin your laboratory practical? Launch a new session by selecting your subject, lab, and workstation seat configuration.
              </p>
              <Button
                variant="primary"
                size="md"
                icon={Radio}
                onClick={() => setShowLaunchModal(true)}
              >
                Launch Laboratory Session
              </Button>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Live Session Control Banner */}
              <div className="p-5 rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-card flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div>
                  <div className="flex items-center gap-2.5">
                    <Badge
                      variant={session.status === 'active' ? 'success' : session.status === 'paused' ? 'warning' : 'neutral'}
                      size="sm"
                      dot
                    >
                      {session.status.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-light-muted dark:text-dark-muted font-mono">
                      Session #{session.id}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-light-text dark:text-dark-text mt-1">
                    {session.subject_name}
                  </h2>
                  <p className="text-xs text-light-muted dark:text-dark-muted">
                    {session.lab_name} &bull; Capacity: {workstations.length || session.capacity || 30} Workstations
                  </p>
                </div>

                {/* Center Timer & Stats */}
                <div className="flex items-center gap-6">
                  {/* Countdown clock */}
                  <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border">
                    <Clock className="w-5 h-5 text-brand-teal dark:text-brand-darkAction" />
                    <div>
                      <span className="text-[10px] uppercase font-bold text-light-muted dark:text-dark-muted block">
                        Remaining Time
                      </span>
                      <span className="font-mono text-xl font-extrabold text-light-text dark:text-dark-text">
                        {formatTimer(remainingTime)}
                      </span>
                    </div>
                  </div>

                  {/* Attendance count */}
                  <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border">
                    <Users className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    <div>
                      <span className="text-[10px] uppercase font-bold text-light-muted dark:text-dark-muted block">
                        Checked In
                      </span>
                      <span className="font-mono text-xl font-extrabold text-emerald-600 dark:text-emerald-400">
                        {workstations.filter((w) => w.status === 'occupied').length} / {workstations.length || 30}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Session Control Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={session.status === 'paused' ? Play : Pause}
                    onClick={handleTogglePause}
                  >
                    {session.status === 'paused' ? 'Resume' : 'Pause'}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={PlusCircle}
                    onClick={handleExtendDuration}
                  >
                    +10 Min
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    icon={Square}
                    onClick={() => setShowStopModal(true)}
                  >
                    End Portal
                  </Button>
                </div>
              </div>

              {/* Dynamic Interactive Workstation Grid (30/60/90 nodes) */}
              <Card
                title={`Workstation Telemetry Grid (${workstations.length || 30} Nodes)`}
                subtitle="Live status indicators. Green nodes represent authenticated student check-ins."
              >
                <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-10 gap-3 py-2">
                  {workstations.map((ws, idx) => {
                    const isOccupied = ws.status === 'occupied';
                    return (
                      <button
                        key={ws.id || idx}
                        type="button"
                        onClick={() => setSelectedSeat(ws)}
                        className={`h-20 p-2.5 rounded-lg border flex flex-col justify-between text-left transition-all duration-150 relative ${
                          isOccupied
                            ? 'bg-brand-soft/20 border-brand-teal/40 text-brand-teal dark:text-brand-darkAction dark:bg-brand-teal/15 shadow-subtle hover:border-brand-teal'
                            : 'bg-light-surface dark:bg-dark-surface border-light-border dark:border-dark-border hover:border-brand-teal/40 hover:bg-slate-50 dark:hover:bg-[#2a383a]'
                        }`}
                      >
                        <div className="flex items-center justify-between w-full">
                          <span className={`font-mono text-xs font-bold ${isOccupied ? 'text-brand-deep dark:text-brand-darkAction' : 'text-light-text dark:text-dark-text'}`}>
                            WS-{(ws.workstation_number || idx + 1).toString().padStart(2, '0')}
                          </span>
                          <span
                            className={`w-2 h-2 rounded-full ${
                              isOccupied ? 'bg-brand-teal dark:bg-brand-darkAction animate-pulse' : 'bg-light-border dark:bg-dark-border'
                            }`}
                          />
                        </div>

                        {isOccupied ? (
                          <div className="overflow-hidden">
                            <span className="text-[11px] font-bold block truncate text-light-text dark:text-dark-text">
                              {ws.student_name || 'Enrolled'}
                            </span>
                            <span className="text-[10px] font-mono text-brand-teal dark:text-brand-darkAction block truncate">
                              {ws.roll_number}
                            </span>
                          </div>
                        ) : (
                          <span className="text-[10px] font-medium text-light-muted dark:text-dark-muted">
                            Vacant
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </Card>
            </div>
          )}
        </>
      )}

      {/* TAB 2: STUDENT ANALYSIS & DEFAULTERS */}
      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {analysisLoading ? (
            <LoadingSkeleton count={3} />
          ) : !analysisData ? (
            <p className="text-xs text-light-muted dark:text-dark-muted">
              Select an active subject or conduct sessions to view student attendance analytics.
            </p>
          ) : (
            <>
              {/* Overview Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="p-4 border-l-4 border-l-brand-teal">
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">Total Enrolled</span>
                  <p className="text-2xl font-extrabold mt-1 text-light-text dark:text-dark-text">
                    {analysisData.total_enrolled || 0}
                  </p>
                </Card>
                <Card className="p-4 border-l-4 border-l-emerald-500">
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">Regular Attendance (≥75%)</span>
                  <p className="text-2xl font-extrabold mt-1 text-emerald-600 dark:text-emerald-400">
                    {analysisData.regular_count || 0}
                  </p>
                </Card>
                <Card className="p-4 border-l-4 border-l-rose-500">
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">At-Risk Defaulters (&lt;75%)</span>
                  <p className="text-2xl font-extrabold mt-1 text-rose-600 dark:text-rose-400">
                    {analysisData.defaulter_count || 0}
                  </p>
                </Card>
                <Card className="p-4 border-l-4 border-l-amber-500">
                  <span className="text-xs text-light-muted dark:text-dark-muted font-medium">Class Attendance Average</span>
                  <p className="text-2xl font-extrabold mt-1 text-amber-600 dark:text-amber-400">
                    {analysisData.average_percentage || 0}%
                  </p>
                </Card>
              </div>

              {/* Visual Analytics Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Attendance Distribution" subtitle="Proportion of regular vs at-risk students">
                  <div className="h-64 flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Regular (≥75%)', value: analysisData.regular_count || 0 },
                            { name: 'Defaulters (<75%)', value: analysisData.defaulter_count || 0 },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          <Cell fill="#10B981" />
                          <Cell fill="#E11D48" />
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                <Card title="Top Defaulter Alert" subtitle="Students requiring immediate academic attendance intervention">
                  <div className="space-y-3">
                    {analysisData.defaulters?.length === 0 ? (
                      <p className="text-xs text-emerald-600 dark:text-emerald-400 py-4 text-center font-medium">
                        Excellent! No students have attendance below 75%.
                      </p>
                    ) : (
                      analysisData.defaulters?.slice(0, 5).map((def) => (
                        <div
                          key={def.student_id}
                          className="p-3 rounded-xl border border-rose-500/20 bg-rose-500/5 flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-bold text-light-text dark:text-dark-text block">
                              {def.student_name}
                            </span>
                            <span className="text-[11px] font-mono text-light-muted dark:text-dark-muted">
                              Roll: {def.roll_number}
                            </span>
                          </div>
                          <Badge variant="danger" size="sm">
                            {def.attendance_percentage}% Attendance
                          </Badge>
                        </div>
                      ))
                    )}
                  </div>
                </Card>
              </div>

              {/* Comprehensive Student Roster Table */}
              <Card
                title="Student Roster & Attendance History"
                subtitle="Detailed breakdown per enrolled student"
                action={
                  <div className="w-64">
                    <Input
                      placeholder="Filter student..."
                      icon={Search}
                      value={analysisSearch}
                      onChange={(e) => setAnalysisSearch(e.target.value)}
                      className="py-1 text-xs"
                    />
                  </div>
                }
              >
                <Table
                  headers={['Student Name', 'Roll Number', 'Attended / Total', 'Percentage', 'Status']}
                  isEmpty={!analysisData.students || analysisData.students.length === 0}
                >
                  {analysisData.students
                    ?.filter((s) => {
                      const q = analysisSearch.toLowerCase();
                      return s.student_name.toLowerCase().includes(q) || s.roll_number.toLowerCase().includes(q);
                    })
                    .map((s) => {
                      const isDefaulter = s.attendance_percentage < 75;
                      return (
                        <tr key={s.student_id} className="hover:bg-light-secondary/40 dark:hover:bg-dark-surface/40">
                          <td className="px-4 py-3 font-semibold text-xs text-light-text dark:text-dark-text">
                            {s.student_name}
                          </td>
                          <td className="px-4 py-3 text-xs font-mono">
                            {s.roll_number}
                          </td>
                          <td className="px-4 py-3 text-xs text-light-muted dark:text-dark-muted">
                            {s.attended_sessions} / {s.total_sessions}
                          </td>
                          <td className="px-4 py-3 text-xs font-bold">
                            <span className={isDefaulter ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}>
                              {s.attendance_percentage}%
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={isDefaulter ? 'danger' : 'success'} size="sm" dot>
                              {isDefaulter ? 'Defaulter' : 'Regular'}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                </Table>
              </Card>
            </>
          )}
        </div>
      )}

      {/* LAUNCH SESSION MODAL */}
      <Modal
        isOpen={showLaunchModal}
        onClose={() => setShowLaunchModal(false)}
        title="Launch Laboratory Session"
        subtitle="Initialize a real-time digital attendance portal."
      >
        <form onSubmit={handleLaunchSession} className="space-y-4">
          <Select
            label="Curriculum Subject"
            required
            value={launchForm.subject_id}
            onChange={(e) => setLaunchForm({ ...launchForm, subject_id: e.target.value })}
            options={assignedSubjects.map((s) => ({
              label: `${s.name} (${s.code})`,
              value: s.id,
            }))}
          />

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Workstation Capacity"
              value={launchForm.capacity}
              onChange={(e) => setLaunchForm({ ...launchForm, capacity: e.target.value })}
              options={[
                { label: '30 Workstations', value: '30' },
                { label: '60 Workstations', value: '60' },
                { label: '90 Workstations', value: '90' },
              ]}
            />
            <Select
              label="Session Duration"
              value={launchForm.duration}
              onChange={(e) => setLaunchForm({ ...launchForm, duration: e.target.value })}
              options={[
                { label: '30 Minutes', value: '30' },
                { label: '45 Minutes', value: '45' },
                { label: '60 Minutes', value: '60' },
                { label: '90 Minutes', value: '90' },
                { label: '120 Minutes', value: '120' },
              ]}
            />
          </div>

          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowLaunchModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isLaunching}>
              Start Attendance Session
            </Button>
          </div>
        </form>
      </Modal>

      {/* STOP SESSION MODAL */}
      <Modal
        isOpen={showStopModal}
        onClose={() => setShowStopModal(false)}
        title="End Attendance Session?"
        subtitle="This will lock the attendance roster and archive the check-in logs."
      >
        <p className="text-xs text-light-muted dark:text-dark-muted mb-4">
          Are you sure you want to end this attendance portal? Students will no longer be able to check in at their workstations.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setShowStopModal(false)}>
            Keep Active
          </Button>
          <Button variant="danger" isLoading={isStopping} onClick={handleStopSession}>
            Yes, Close Session
          </Button>
        </div>
      </Modal>

      {/* WORKSTATION SEAT DETAILS MODAL */}
      <Modal
        isOpen={!!selectedSeat}
        onClose={() => setSelectedSeat(null)}
        title={`Workstation WS-${selectedSeat?.workstation_number || selectedSeat?.id}`}
        subtitle="Live telemetry and check-in inspection"
      >
        {selectedSeat && (
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-light-border dark:border-dark-border">
              <span className="text-light-muted dark:text-dark-muted">Status</span>
              <Badge variant={selectedSeat.status === 'occupied' ? 'success' : 'neutral'} size="sm" dot>
                {selectedSeat.status === 'occupied' ? 'Occupied' : 'Vacant'}
              </Badge>
            </div>
            {selectedSeat.status === 'occupied' && (
              <>
                <div className="flex justify-between py-1.5 border-b border-light-border dark:border-dark-border">
                  <span className="text-light-muted dark:text-dark-muted">Student Name</span>
                  <span className="font-semibold">{selectedSeat.student_name}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-light-border dark:border-dark-border">
                  <span className="text-light-muted dark:text-dark-muted">Roll Number</span>
                  <span className="font-mono">{selectedSeat.roll_number}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-light-border dark:border-dark-border">
                  <span className="text-light-muted dark:text-dark-muted">Check-In Timestamp</span>
                  <span>{new Date(selectedSeat.checked_in_at).toLocaleTimeString()}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-light-muted dark:text-dark-muted">Client IP</span>
                  <span className="font-mono">{selectedSeat.ip_address || '127.0.0.1'}</span>
                </div>
              </>
            )}
            <div className="pt-3 flex justify-end">
              <Button size="sm" variant="secondary" onClick={() => setSelectedSeat(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

