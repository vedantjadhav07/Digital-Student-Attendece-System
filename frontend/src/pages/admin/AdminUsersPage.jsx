import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Upload,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Edit2,
  Trash2,
  AlertTriangle,
  FileSpreadsheet,
  Download
} from 'lucide-react';
import { toast } from 'sonner';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Select from '../../components/common/Select';
import Modal from '../../components/common/Modal';
import Badge from '../../components/common/Badge';
import Table from '../../components/common/Table';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import adminService from '../../services/adminService';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [academicData, setAcademicData] = useState({ departments: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'teacher' | 'student'
  const [searchTerm, setSearchTerm] = useState('');

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Add User Form state
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    name: '',
    role: 'student',
    password: '',
    // Student specifics
    department_id: '',
    year: '1',
    division: 'A',
    roll_number: '',
    enrollment_number: '',
    // Teacher specifics
    employee_id: '',
    designation: 'Assistant Professor',
  });

  // Bulk Import state
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkPreview, setBulkPreview] = useState([]);
  const [bulkErrors, setBulkErrors] = useState([]);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const roleParam = activeTab === 'all' ? undefined : activeTab;
      const [usersRes, structRes] = await Promise.all([
        adminService.getUsers(roleParam),
        adminService.getAcademicStructure().catch(() => ({ departments: [] })),
      ]);
      setUsers(usersRes.users || []);
      setAcademicData(structRes);
      if (structRes.departments?.length > 0 && !formData.department_id) {
        setFormData((prev) => ({ ...prev, department_id: structRes.departments[0].id }));
      }
    } catch (err) {
      toast.error('Failed to load users.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!formData.username || !formData.email || !formData.password || !formData.name) {
      toast.error('Please fill in all required account fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      await adminService.createUser(formData);
      toast.success(`User @${formData.username} created successfully!`);
      setShowAddModal(false);
      resetForm();
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create user account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (user) => {
    const newStatus = !user.is_active;
    try {
      await adminService.updateUser(user.id, { is_active: newStatus });
      toast.success(`Account @${user.username} is now ${newStatus ? 'active' : 'deactivated'}.`);
      setUsers(users.map((u) => (u.id === user.id ? { ...u, is_active: newStatus } : u)));
    } catch (err) {
      toast.error('Failed to update account status.');
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      name: '',
      role: 'student',
      password: '',
      department_id: academicData.departments[0]?.id || '',
      year: '1',
      division: 'A',
      roll_number: '',
      enrollment_number: '',
      employee_id: '',
      designation: 'Assistant Professor',
    });
  };

  // CSV parsing for Bulk Import
  const handleBulkFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setBulkFile(file);
    setBulkErrors([]);
    setBulkPreview([]);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const lines = text.split(/\r\n|\n/).filter((l) => l.trim().length > 0);
      if (lines.length < 2) {
        setBulkErrors(['The file contains no data rows.']);
        return;
      }

      const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
      const required = ['username', 'email', 'name', 'roll_number'];
      const missing = required.filter((r) => !headers.includes(r));
      if (missing.length > 0) {
        setBulkErrors([`Missing required CSV column headers: ${missing.join(', ')}`]);
        return;
      }

      const rows = [];
      const errors = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map((v) => v.trim());
        if (values.length < headers.length) {
          errors.push(`Row ${i + 1}: Incomplete columns`);
          continue;
        }
        const rowObj = {};
        headers.forEach((h, idx) => {
          rowObj[h] = values[idx];
        });
        rows.push(rowObj);
      }

      setBulkPreview(rows.slice(0, 5));
      if (errors.length > 0) {
        setBulkErrors(errors);
      }
    };
    reader.readAsText(file);
  };

  const handleBulkSubmit = async () => {
    if (!bulkFile) {
      toast.error('Please choose a file to upload.');
      return;
    }
    try {
      setIsSubmitting(true);
      const res = await adminService.bulkImportUsers(bulkFile);
      toast.success(res.message || 'Users imported successfully!');
      setShowBulkModal(false);
      setBulkFile(null);
      setBulkPreview([]);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Bulk import failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const query = searchTerm.toLowerCase();
    const matchSearch =
      (u.name && u.name.toLowerCase().includes(query)) ||
      (u.username && u.username.toLowerCase().includes(query)) ||
      (u.email && u.email.toLowerCase().includes(query)) ||
      (u.roll_number && u.roll_number.toLowerCase().includes(query));
    return matchSearch;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            User Accounts
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Manage student registrations, faculty accounts, role assignments, and bulk roster imports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            icon={Upload}
            onClick={() => setShowBulkModal(true)}
          >
            Bulk Import CSV
          </Button>
          <Button
            size="sm"
            variant="primary"
            icon={UserPlus}
            onClick={() => setShowAddModal(true)}
          >
            Add New User
          </Button>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Tabs */}
          <div className="flex items-center gap-1.5 p-1 bg-light-bg dark:bg-dark-bg rounded-lg border border-light-border dark:border-dark-border">
            {[
              { id: 'all', label: 'All Accounts' },
              { id: 'teacher', label: 'Faculty' },
              { id: 'student', label: 'Students' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-1.5 rounded text-xs font-semibold transition-all ${
                  activeTab === tab.id
                    ? 'bg-light-surface dark:bg-brand-teal/20 text-brand-teal dark:text-brand-darkAction shadow-subtle border border-light-border dark:border-brand-teal/30'
                    : 'text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="w-full md:w-72">
            <Input
              icon={Search}
              placeholder="Search by name, roll no, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="py-1.5 text-xs"
            />
          </div>
        </div>
      </Card>

      {/* Users Table */}
      {isLoading ? (
        <LoadingSkeleton type="table" />
      ) : (
        <Table
          headers={[
            'User Profile',
            'Role',
            'Department / Division',
            'Roll / Emp ID',
            'Status',
            { label: 'Actions', className: 'text-right' },
          ]}
          isEmpty={filteredUsers.length === 0}
          emptyText="No user accounts found matching your query."
        >
          {filteredUsers.map((u) => (
            <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-[#202b2c]/80 transition-colors">
              <td className="px-4 py-3.5">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction font-bold text-xs flex items-center justify-center">
                    {(u.name || u.username)[0].toUpperCase()}
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-light-text dark:text-dark-text block">
                      {u.name || u.username}
                    </span>
                    <span className="text-[11px] text-light-muted dark:text-dark-muted">
                      {u.email}
                    </span>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3.5">
                <Badge
                  variant={u.role === 'admin' ? 'teal' : u.role === 'teacher' ? 'info' : 'neutral'}
                  size="sm"
                >
                  {u.role}
                </Badge>
              </td>
              <td className="px-4 py-3.5 text-xs">
                {u.department_name ? (
                  <span>
                    {u.department_name}{' '}
                    {u.division ? `(Div ${u.division}, Yr ${u.year})` : ''}
                  </span>
                ) : (
                  <span className="text-light-muted dark:text-dark-muted">N/A</span>
                )}
              </td>
              <td className="px-4 py-3.5 text-xs font-mono">
                {u.roll_number || u.employee_id || '—'}
              </td>
              <td className="px-4 py-3.5">
                <Badge variant={u.is_active ? 'success' : 'danger'} size="sm" dot>
                  {u.is_active ? 'Active' : 'Disabled'}
                </Badge>
              </td>
              <td className="px-4 py-3.5 text-right">
                <Button
                  size="sm"
                  variant={u.is_active ? 'ghost' : 'outline'}
                  onClick={() => handleToggleStatus(u)}
                  className="text-xs py-1"
                >
                  {u.is_active ? 'Deactivate' : 'Activate'}
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      )}

      {/* MODAL 1: ADD USER MODAL */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add New User Account"
        subtitle="Create a new administrator, faculty member, or student."
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <Select
            label="Account Role"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            options={[
              { label: 'Student', value: 'student' },
              { label: 'Faculty / Teacher', value: 'teacher' },
              { label: 'Administrator', value: 'admin' },
            ]}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              required
              placeholder="e.g. John Doe"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <Input
              label="Username"
              required
              placeholder="e.g. jdoe21"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email Address"
              type="email"
              required
              placeholder="jdoe@college.edu"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Input
              label="Initial Password"
              type="password"
              required
              placeholder="Min 8 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {/* Conditional Fields: Student */}
          {formData.role === 'student' && (
            <div className="p-4 rounded-xl border border-light-border dark:border-dark-border bg-light-secondary/30 dark:bg-dark-surface/30 space-y-4">
              <span className="text-xs font-bold text-brand-violet uppercase tracking-wider block">
                Student Academic Details
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Select
                  label="Department"
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  options={academicData.departments.map((d) => ({
                    label: d.name,
                    value: d.id,
                  }))}
                />
                <Select
                  label="Academic Year"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                  options={[
                    { label: 'Year 1', value: '1' },
                    { label: 'Year 2', value: '2' },
                    { label: 'Year 3', value: '3' },
                    { label: 'Year 4', value: '4' },
                  ]}
                />
                <Input
                  label="Division / Section"
                  placeholder="e.g. A"
                  value={formData.division}
                  onChange={(e) => setFormData({ ...formData, division: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  label="Roll Number"
                  placeholder="e.g. 21CS001"
                  value={formData.roll_number}
                  onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })}
                />
                <Input
                  label="Enrollment / PRN"
                  placeholder="e.g. PRN20210091"
                  value={formData.enrollment_number}
                  onChange={(e) => setFormData({ ...formData, enrollment_number: e.target.value })}
                />
              </div>
            </div>
          )}

          {/* Conditional Fields: Faculty / Teacher */}
          {formData.role === 'teacher' && (
            <div className="p-4 rounded-xl border border-light-border dark:border-dark-border bg-light-secondary/30 dark:bg-dark-surface/30 space-y-4">
              <span className="text-xs font-bold text-brand-violet uppercase tracking-wider block">
                Faculty Details
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Select
                  label="Department"
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  options={academicData.departments.map((d) => ({
                    label: d.name,
                    value: d.id,
                  }))}
                />
                <Input
                  label="Designation"
                  placeholder="e.g. Assistant Professor"
                  value={formData.designation}
                  onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                />
              </div>
              <Input
                label="Employee ID"
                placeholder="e.g. FAC-2024-09"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Create Account
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 2: BULK IMPORT MODAL */}
      <Modal
        isOpen={showBulkModal}
        onClose={() => setShowBulkModal(false)}
        title="Bulk Student Import"
        subtitle="Upload a CSV file to enroll multiple students simultaneously."
      >
        <div className="space-y-4">
          <div className="p-4 rounded-lg border border-dashed border-brand-teal/40 bg-brand-soft/10 text-center flex flex-col items-center justify-center">
            <FileSpreadsheet className="w-10 h-10 text-brand-teal dark:text-brand-darkAction mb-2" />
            <p className="text-xs font-semibold text-light-text dark:text-dark-text">
              Select CSV Roster File
            </p>
            <p className="text-[11px] text-light-muted dark:text-dark-muted mt-0.5">
              Must include: <span className="font-mono text-brand-teal dark:text-brand-darkAction">username, email, name, roll_number</span>
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleBulkFileChange}
              className="mt-3 text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-brand-teal file:text-white dark:file:bg-brand-darkAction dark:file:text-[#151D1E] hover:file:opacity-90 cursor-pointer"
            />
          </div>

          {/* Error messages */}
          {bulkErrors.length > 0 && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs space-y-1">
              <div className="font-semibold flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Validation Errors:
              </div>
              {bulkErrors.map((err, i) => (
                <p key={i}>&bull; {err}</p>
              ))}
            </div>
          )}

          {/* Preview Table */}
          {bulkPreview.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-light-text dark:text-dark-text">
                Preview (First 5 Rows)
              </span>
              <div className="overflow-x-auto rounded-lg border border-light-border dark:border-dark-border text-[11px]">
                <table className="w-full text-left">
                  <thead className="bg-light-secondary dark:bg-dark-surface font-semibold text-light-muted dark:text-dark-muted">
                    <tr>
                      <th className="p-2">Username</th>
                      <th className="p-2">Name</th>
                      <th className="p-2">Roll No</th>
                      <th className="p-2">Email</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-light-border dark:divide-dark-border">
                    {bulkPreview.map((row, idx) => (
                      <tr key={idx}>
                        <td className="p-2 font-mono">{row.username}</td>
                        <td className="p-2">{row.name}</td>
                        <td className="p-2 font-mono">{row.roll_number}</td>
                        <td className="p-2">{row.email}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowBulkModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!bulkFile || bulkErrors.length > 0}
              isLoading={isSubmitting}
              onClick={handleBulkSubmit}
            >
              Upload & Process Roster
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

