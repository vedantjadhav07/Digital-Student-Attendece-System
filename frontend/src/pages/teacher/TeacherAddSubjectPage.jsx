import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookPlus,
  BookOpen,
  CheckCircle,
  Plus,
  Search,
  ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Badge from '../../components/common/Badge';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import teacherService from '../../services/teacherService';

export default function TeacherAddSubjectPage() {
  const navigate = useNavigate();
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      setIsLoading(true);
      const res = await teacherService.getSubjects();
      setAvailableSubjects(res.available_subjects || []);
      setAssignedSubjects(res.assigned_subjects || []);
    } catch (err) {
      toast.error('Failed to load subjects catalog.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClaimSubject = async (subjectId) => {
    try {
      setIsAdding(true);
      await teacherService.addSubject(subjectId);
      toast.success('Subject assigned to your teaching portfolio successfully!');
      loadSubjects();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to claim subject.');
    } finally {
      setIsAdding(false);
    }
  };

  const filteredAvailable = availableSubjects.filter((s) => {
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            Add Subject to Teaching Portfolio
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Claim and link curriculum laboratory subjects to conduct live attendance portals.
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate('/teacher')}
        >
          Back to Overview
        </Button>
      </div>

      {/* Currently Assigned Subjects */}
      <Card
        title="My Assigned Subjects"
        subtitle={`You are currently conducting ${assignedSubjects.length} subject(s)`}
      >
        {isLoading ? (
          <LoadingSkeleton count={2} />
        ) : assignedSubjects.length === 0 ? (
          <p className="text-xs text-light-muted dark:text-dark-muted py-2">
            You do not have any assigned subjects yet. Select one from the catalog below.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {assignedSubjects.map((sub) => (
              <div
                key={sub.id}
                className="p-4 rounded-xl border border-light-border dark:border-dark-border bg-light-secondary/30 dark:bg-dark-surface/30 flex items-center justify-between"
              >
                <div>
                  <h4 className="text-xs font-bold text-light-text dark:text-dark-text">
                    {sub.name}
                  </h4>
                  <p className="text-[11px] font-mono text-brand-teal dark:text-brand-darkAction font-semibold mt-0.5">
                    {sub.code} &bull; Sem {sub.semester}
                  </p>
                </div>
                <Badge variant="success" size="sm" dot>
                  Active
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Available Catalog */}
      <Card
        title="Available Curriculum Subjects"
        subtitle="Claim available college laboratory subjects"
        action={
          <div className="w-64">
            <Input
              placeholder="Filter subjects..."
              icon={Search}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="py-1 text-xs"
            />
          </div>
        }
      >
        {isLoading ? (
          <LoadingSkeleton count={3} />
        ) : filteredAvailable.length === 0 ? (
          <div className="text-center py-8">
            <BookOpen className="w-8 h-8 text-light-muted mx-auto mb-2 opacity-50" />
            <p className="text-xs text-light-muted dark:text-dark-muted">
              No additional available subjects found.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-light-border dark:divide-dark-border">
            {filteredAvailable.map((sub) => (
              <div
                key={sub.id}
                className="py-3.5 flex items-center justify-between gap-4 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-light-text dark:text-dark-text text-sm">
                      {sub.name}
                    </span>
                    <span className="font-mono text-brand-teal dark:text-brand-darkAction font-semibold">
                      [{sub.code}]
                    </span>
                  </div>
                  <p className="text-[11px] text-light-muted dark:text-dark-muted mt-0.5">
                    {sub.department_name} &bull; Semester {sub.semester}
                  </p>
                </div>

                <Button
                  size="sm"
                  variant="primary"
                  icon={Plus}
                  isLoading={isAdding}
                  onClick={() => handleClaimSubject(sub.id)}
                >
                  Assign to Me
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

