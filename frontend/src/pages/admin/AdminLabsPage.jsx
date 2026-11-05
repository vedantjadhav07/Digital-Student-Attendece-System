import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Plus,
  Cpu,
  MapPin,
  Network,
  CheckCircle2,
  AlertCircle
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

export default function AdminLabsPage() {
  const [labs, setLabs] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [labForm, setLabForm] = useState({
    name: '',
    code: '',
    capacity: '30',
    location: '',
    ip_range: '127.0.0.1',
    department_id: '',
  });

  useEffect(() => {
    loadLabs();
  }, []);

  const loadLabs = async () => {
    try {
      setIsLoading(true);
      const [labsRes, structRes] = await Promise.all([
        adminService.getLaboratories(),
        adminService.getAcademicStructure().catch(() => ({ departments: [] })),
      ]);
      setLabs(labsRes.laboratories || []);
      setDepartments(structRes.departments || []);
      if (structRes.departments?.length > 0) {
        setLabForm((prev) => ({ ...prev, department_id: structRes.departments[0].id }));
      }
    } catch (err) {
      toast.error('Failed to load laboratories.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateLab = async (e) => {
    e.preventDefault();
    if (!labForm.name || !labForm.code) {
      toast.error('Laboratory name and code are required.');
      return;
    }
    try {
      setIsSubmitting(true);
      await adminService.createLaboratory(labForm);
      toast.success(`Laboratory "${labForm.name}" created successfully!`);
      setShowModal(false);
      setLabForm({
        name: '',
        code: '',
        capacity: '30',
        location: '',
        ip_range: '127.0.0.1',
        department_id: departments[0]?.id || '',
      });
      loadLabs();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create laboratory.');
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
            Computer Laboratories
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Manage physical computer labs, workstation seat capacities (30/60/90), and authorized subnet bounds.
          </p>
        </div>
        <Button
          size="sm"
          variant="primary"
          icon={Plus}
          onClick={() => setShowModal(true)}
        >
          Add Laboratory
        </Button>
      </div>

      {/* Grid of Laboratories */}
      {isLoading ? (
        <LoadingSkeleton count={3} />
      ) : labs.length === 0 ? (
        <div className="p-8 text-center rounded-2xl border border-dashed border-light-border dark:border-dark-border">
          <FlaskConical className="w-10 h-10 text-light-muted mx-auto mb-2" />
          <h4 className="font-semibold text-sm">No Laboratories Registered</h4>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Add your campus computer laboratories to enable attendance sessions.
          </p>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowModal(true)}
            className="mt-4"
          >
            Create Lab
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {labs.map((lab) => (
            <Card key={lab.id} hover className="relative flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                    <FlaskConical className="w-5 h-5" />
                  </div>
                  <Badge variant={lab.is_active ? 'success' : 'danger'} size="sm" dot>
                    {lab.is_active ? 'Operational' : 'Inactive'}
                  </Badge>
                </div>

                <h3 className="text-base font-bold text-light-text dark:text-dark-text">
                  {lab.name}
                </h3>
                <p className="text-xs font-mono text-brand-teal dark:text-brand-darkAction font-semibold mt-0.5">
                  Code: {lab.code}
                </p>

                <div className="mt-4 space-y-2 text-xs text-light-muted dark:text-dark-muted">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-brand-teal/70 dark:text-brand-darkAction/70" />
                    <span>Capacity: <strong className="text-light-text dark:text-dark-text">{lab.capacity || 30} Workstations</strong></span>
                  </div>
                  {lab.location && (
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-brand-teal/70 dark:text-brand-darkAction/70" />
                      <span>{lab.location}</span>
                    </div>
                  )}
                  {lab.ip_range && (
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 text-brand-teal/70 dark:text-brand-darkAction/70" />
                      <span className="font-mono text-[11px]">{lab.ip_range}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-light-border dark:border-dark-border flex items-center justify-between text-xs">
                <span className="text-[11px] text-light-muted dark:text-dark-muted">
                  {lab.department_name || 'General Lab'}
                </span>
                <span className="font-semibold text-brand-teal dark:text-brand-darkAction">
                  {lab.total_workstations || lab.capacity || 30} Nodes Configured
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* CREATE LAB MODAL */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Register Computer Laboratory"
        subtitle="Create a new physical laboratory room and configure workstation capacity."
      >
        <form onSubmit={handleCreateLab} className="space-y-4">
          <Input
            label="Laboratory Name"
            required
            placeholder="e.g. Advanced Computing Lab 1"
            value={labForm.name}
            onChange={(e) => setLabForm({ ...labForm, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Lab Code"
              required
              placeholder="e.g. ACL-01"
              value={labForm.code}
              onChange={(e) => setLabForm({ ...labForm, code: e.target.value.toUpperCase() })}
            />
            <Select
              label="Workstation Capacity"
              value={labForm.capacity}
              onChange={(e) => setLabForm({ ...labForm, capacity: e.target.value })}
              options={[
                { label: '30 Workstations', value: '30' },
                { label: '60 Workstations', value: '60' },
                { label: '90 Workstations', value: '90' },
              ]}
            />
          </div>
          <Input
            label="Location / Room Number"
            placeholder="e.g. Tech Block 3rd Floor, Room 304"
            value={labForm.location}
            onChange={(e) => setLabForm({ ...labForm, location: e.target.value })}
          />
          <Input
            label="IP Subnet / CIDR Mask"
            placeholder="e.g. 192.168.1.0/24 or 127.0.0.1"
            value={labForm.ip_range}
            onChange={(e) => setLabForm({ ...labForm, ip_range: e.target.value })}
            helperText="Subnet used to verify student workstation connections."
          />
          {departments.length > 0 && (
            <Select
              label="Owning Department"
              value={labForm.department_id}
              onChange={(e) => setLabForm({ ...labForm, department_id: e.target.value })}
              options={departments.map((d) => ({
                label: d.name,
                value: d.id,
              }))}
            />
          )}
          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Create Laboratory
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

