import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Building,
  BookOpen,
  Plus,
  Trash2,
  Layers,
  BookPlus
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

export default function AdminAcademicsPage() {
  const [data, setData] = useState({ departments: [], subjects: [] });
  const [teachers, setTeachers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('departments'); // 'departments' | 'subjects'

  // Modals
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showSubjectModal, setShowSubjectModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Forms
  const [deptForm, setDeptForm] = useState({ name: '', code: '' });
  const [subjectForm, setSubjectForm] = useState({
    name: '',
    code: '',
    department_id: '',
    semester: '1',
    teacher_id: '',
  });

  useEffect(() => {
    loadAcademics();
  }, []);

  const loadAcademics = async () => {
    try {
      setIsLoading(true);
      const [structRes, teachersRes] = await Promise.all([
        adminService.getAcademicStructure(),
        adminService.getUsers('teacher').catch(() => ({ users: [] })),
      ]);
      setData(structRes);
      setTeachers(teachersRes.users || []);
      if (structRes.departments?.length > 0) {
        setSubjectForm((prev) => ({ ...prev, department_id: structRes.departments[0].id }));
      }
    } catch (err) {
      toast.error('Failed to load academic structure.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDept = async (e) => {
    e.preventDefault();
    if (!deptForm.name || !deptForm.code) {
      toast.error('Department name and code are required.');
      return;
    }
    try {
      setIsSubmitting(true);
      await adminService.createDepartment(deptForm);
      toast.success(`Department "${deptForm.name}" created!`);
      setShowDeptModal(false);
      setDeptForm({ name: '', code: '' });
      loadAcademics();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create department.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!subjectForm.name || !subjectForm.code || !subjectForm.department_id) {
      toast.error('Subject name, code, and department are required.');
      return;
    }
    try {
      setIsSubmitting(true);
      await adminService.createSubject(subjectForm);
      toast.success(`Subject "${subjectForm.name}" created!`);
      setShowSubjectModal(false);
      setSubjectForm({
        name: '',
        code: '',
        department_id: data.departments[0]?.id || '',
        semester: '1',
        teacher_id: '',
      });
      loadAcademics();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create subject.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            Academics Management
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Configure academic departments, curriculum subject catalog, and faculty subject mappings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {activeTab === 'departments' ? (
            <Button
              size="sm"
              variant="primary"
              icon={Plus}
              onClick={() => setShowDeptModal(true)}
            >
              Add Department
            </Button>
          ) : (
            <Button
              size="sm"
              variant="primary"
              icon={Plus}
              onClick={() => setShowSubjectModal(true)}
            >
              Add Subject
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 p-1 bg-light-bg dark:bg-dark-bg rounded-lg border border-light-border dark:border-dark-border w-fit">
        <button
          onClick={() => setActiveTab('departments')}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold transition-all ${
            activeTab === 'departments'
              ? 'bg-light-surface dark:bg-brand-teal/20 text-brand-teal dark:text-brand-darkAction shadow-subtle border border-light-border dark:border-brand-teal/30'
              : 'text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
          }`}
        >
          <Building className="w-4 h-4" />
          Departments ({data.departments?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold transition-all ${
            activeTab === 'subjects'
              ? 'bg-light-surface dark:bg-brand-teal/20 text-brand-teal dark:text-brand-darkAction shadow-subtle border border-light-border dark:border-brand-teal/30'
              : 'text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Subjects ({data.subjects?.length || 0})
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton type="table" />
      ) : activeTab === 'departments' ? (
        <Table
          headers={['Department Name', 'Code', 'Total Students', 'Total Subjects']}
          isEmpty={!data.departments || data.departments.length === 0}
          emptyText="No academic departments configured yet."
        >
          {data.departments?.map((dept) => (
            <tr key={dept.id} className="hover:bg-slate-50 dark:hover:bg-[#202b2c]/80 transition-colors">
              <td className="px-4 py-3.5 font-semibold text-xs text-light-text dark:text-dark-text">
                {dept.name}
              </td>
              <td className="px-4 py-3.5 text-xs font-mono text-brand-teal dark:text-brand-darkAction font-bold">
                {dept.code}
              </td>
              <td className="px-4 py-3.5 text-xs text-light-muted dark:text-dark-muted">
                {dept.students_count || 0} students
              </td>
              <td className="px-4 py-3.5 text-xs text-light-muted dark:text-dark-muted">
                {dept.subjects_count || 0} subjects
              </td>
            </tr>
          ))}
        </Table>
      ) : (
        <Table
          headers={['Subject Name', 'Code', 'Department', 'Semester', 'Assigned Teacher']}
          isEmpty={!data.subjects || data.subjects.length === 0}
          emptyText="No subjects configured yet."
        >
          {data.subjects?.map((sub) => (
            <tr key={sub.id} className="hover:bg-slate-50 dark:hover:bg-[#202b2c]/80 transition-colors">
              <td className="px-4 py-3.5 font-semibold text-xs text-light-text dark:text-dark-text">
                {sub.name}
              </td>
              <td className="px-4 py-3.5 text-xs font-mono text-brand-teal dark:text-brand-darkAction font-bold">
                {sub.code}
              </td>
              <td className="px-4 py-3.5 text-xs text-light-muted dark:text-dark-muted">
                {sub.department_name || '—'}
              </td>
              <td className="px-4 py-3.5 text-xs">
                Semester {sub.semester}
              </td>
              <td className="px-4 py-3.5 text-xs">
                {sub.teacher_name ? (
                  <Badge variant="purple" size="sm">
                    {sub.teacher_name}
                  </Badge>
                ) : (
                  <span className="text-light-muted dark:text-dark-muted">Unassigned</span>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}

      {/* CREATE DEPARTMENT MODAL */}
      <Modal
        isOpen={showDeptModal}
        onClose={() => setShowDeptModal(false)}
        title="Add Academic Department"
        subtitle="Register a new academic department into the college directory."
      >
        <form onSubmit={handleCreateDept} className="space-y-4">
          <Input
            label="Department Name"
            required
            placeholder="e.g. Computer Science and Engineering"
            value={deptForm.name}
            onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
          />
          <Input
            label="Department Code"
            required
            placeholder="e.g. CSE"
            value={deptForm.code}
            onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value.toUpperCase() })}
          />
          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowDeptModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Add Department
            </Button>
          </div>
        </form>
      </Modal>

      {/* CREATE SUBJECT MODAL */}
      <Modal
        isOpen={showSubjectModal}
        onClose={() => setShowSubjectModal(false)}
        title="Add Curriculum Subject"
        subtitle="Create a new laboratory/lecture subject and associate it with a faculty teacher."
      >
        <form onSubmit={handleCreateSubject} className="space-y-4">
          <Input
            label="Subject Name"
            required
            placeholder="e.g. Operating Systems Lab"
            value={subjectForm.name}
            onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Subject Code"
              required
              placeholder="e.g. CS401"
              value={subjectForm.code}
              onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value.toUpperCase() })}
            />
            <Select
              label="Semester"
              value={subjectForm.semester}
              onChange={(e) => setSubjectForm({ ...subjectForm, semester: e.target.value })}
              options={Array.from({ length: 8 }, (_, i) => ({
                label: `Semester ${i + 1}`,
                value: (i + 1).toString(),
              }))}
            />
          </div>
          <Select
            label="Department"
            value={subjectForm.department_id}
            onChange={(e) => setSubjectForm({ ...subjectForm, department_id: e.target.value })}
            options={data.departments?.map((d) => ({
              label: d.name,
              value: d.id,
            }))}
          />
          <Select
            label="Assign Faculty (Optional)"
            value={subjectForm.teacher_id}
            onChange={(e) => setSubjectForm({ ...subjectForm, teacher_id: e.target.value })}
            options={[
              { label: 'None (Unassigned)', value: '' },
              ...teachers.map((t) => ({
                label: `${t.name || t.username} (${t.email})`,
                value: t.teacher_id || t.id,
              })),
            ]}
          />
          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowSubjectModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Add Subject
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

