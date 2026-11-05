import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Plus,
  Cpu,
  MapPin,
  Network,
  CheckCircle2,
  AlertCircle,
  Eye,
  Trash2,
  ShieldCheck,
  Server,
  Layers,
  Building,
  Key
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

  // Creation / Edit Modal
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [labForm, setLabForm] = useState({
    name: '',
    code: '',
    capacity: '30',
    location: '',
    room_number: '',
    department_id: '',
    ip_start: '127.0.0.1',
  });

  // Workstations Viewer Modal
  const [viewingLab, setViewingLab] = useState(null);
  const [workstations, setWorkstations] = useState([]);
  const [isLoadingWorkstations, setIsLoadingWorkstations] = useState(false);
  const [workstationSearch, setWorkstationSearch] = useState('');

  // Delete Confirm Modal
  const [labToDelete, setLabToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

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
      setLabs(labsRes || []);
      const depts = structRes.departments || [];
      setDepartments(depts);
      if (depts.length > 0 && !labForm.department_id) {
        setLabForm((prev) => ({ ...prev, department_id: depts[0].id }));
      }
    } catch (err) {
      toast.error('Failed to load laboratories.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateLab = async (e) => {
    e.preventDefault();
    if (!labForm.name.trim() || !labForm.code.trim()) {
      toast.error('Laboratory Name and Unique Code are required.');
      return;
    }
    if (!labForm.ip_start.trim()) {
      toast.error('Please enter a valid starting IP address (e.g. 127.0.0.1).');
      return;
    }

    try {
      setIsSubmitting(true);
      await adminService.createLaboratory(labForm);
      toast.success(`Laboratory "${labForm.name}" created with ${labForm.capacity} sequential PCs!`);
      setShowModal(false);
      setLabForm({
        name: '',
        code: '',
        capacity: '30',
        location: '',
        room_number: '',
        department_id: departments[0]?.id || '',
        ip_start: '127.0.0.1',
      });
      loadLabs();
    } catch (err) {
      toast.error(err.response?.data?.message || err.response?.data?.error || 'Failed to create laboratory.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewWorkstations = async (lab) => {
    setViewingLab(lab);
    setWorkstationSearch('');
    try {
      setIsLoadingWorkstations(true);
      const res = await adminService.getLaboratoryWorkstations(lab.id);
      setWorkstations(res.workstations || []);
    } catch (err) {
      toast.error('Failed to load workstations for this laboratory.');
    } finally {
      setIsLoadingWorkstations(false);
    }
  };

  const handleDeleteLab = async () => {
    if (!labToDelete) return;
    try {
      setIsDeleting(true);
      await adminService.deleteLaboratory(labToDelete.id);
      toast.success(`Laboratory "${labToDelete.name}" deleted successfully.`);
      setLabToDelete(null);
      loadLabs();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to delete laboratory.');
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredWorkstations = workstations.filter((ws) => {
    const q = workstationSearch.toLowerCase();
    return (
      (ws.workstation_code && ws.workstation_code.toLowerCase().includes(q)) ||
      (ws.ip_address && ws.ip_address.toLowerCase().includes(q)) ||
      (ws.mac_address && ws.mac_address.toLowerCase().includes(q)) ||
      (ws.device_id && ws.device_id.toLowerCase().includes(q)) ||
      ws.seat_number.toString().includes(q)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-light-text dark:text-dark-text">
            Laboratory Management
          </h1>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Configure campus computer laboratories, automatic sequential PC IP provisioning, registered MAC addresses, and unique device IDs.
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
        <div className="p-8 text-center rounded-lg border border-dashed border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface">
          <FlaskConical className="w-10 h-10 text-brand-teal dark:text-brand-darkAction mx-auto mb-2 opacity-60" />
          <h4 className="font-semibold text-sm text-light-text dark:text-dark-text">No Laboratories Registered</h4>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Add your campus computer laboratories to automatically generate sequential workstations and enable practical sessions.
          </p>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowModal(true)}
            className="mt-4"
          >
            Create Laboratory
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {labs.map((lab) => (
            <Card key={lab.id} hover className="relative flex flex-col justify-between shadow-card">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center">
                    <FlaskConical className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={lab.is_active ? 'success' : 'danger'} size="sm" dot>
                      {lab.is_active ? 'Operational' : 'Inactive'}
                    </Badge>
                    <button
                      type="button"
                      onClick={() => setLabToDelete(lab)}
                      title="Delete Laboratory"
                      className="p-1 rounded text-light-muted hover:text-rose-600 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="text-base font-bold text-light-text dark:text-dark-text">
                  {lab.name}
                </h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs font-mono text-brand-teal dark:text-brand-darkAction font-bold">
                    {lab.code}
                  </span>
                  {lab.room_number && (
                    <span className="text-[11px] px-1.5 py-0.5 rounded bg-light-bg dark:bg-dark-bg text-light-muted dark:text-dark-muted font-medium border border-light-border dark:border-dark-border">
                      {lab.room_number}
                    </span>
                  )}
                </div>

                <div className="mt-4 space-y-2 text-xs text-light-muted dark:text-dark-muted">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-brand-teal/80 dark:text-brand-darkAction/80" />
                    <span>Working Capacity: <strong className="text-light-text dark:text-dark-text">{lab.capacity || 30} PCs</strong></span>
                  </div>
                  {lab.location && (
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-brand-teal/80 dark:text-brand-darkAction/80" />
                      <span>{lab.location}</span>
                    </div>
                  )}
                  {lab.department_name && (
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4 text-brand-teal/80 dark:text-brand-darkAction/80" />
                      <span>{lab.department_name}</span>
                    </div>
                  )}
                  {lab.ip_start && (
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 text-brand-teal/80 dark:text-brand-darkAction/80" />
                      <span className="font-mono text-[11px]">
                        IP Range: {lab.ip_start} &rarr; {lab.ip_end || `${lab.ip_start.substring(0, lab.ip_start.lastIndexOf('.'))}.${parseInt(lab.ip_start.split('.').pop()) + (lab.capacity || 30) - 1}`}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-light-border dark:border-dark-border flex items-center justify-between text-xs">
                <Button
                  size="sm"
                  variant="secondary"
                  icon={Eye}
                  onClick={() => handleViewWorkstations(lab)}
                  className="py-1 px-2.5 text-xs"
                >
                  View PCs ({lab.workstation_count || lab.capacity || 30})
                </Button>
                <span className="text-[11px] font-semibold text-brand-teal dark:text-brand-darkAction">
                  Hardware Bound
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
        subtitle="Configure physical lab details. PCs with sequential IPs, MAC addresses, and unique Device IDs will be generated automatically."
      >
        <form onSubmit={handleCreateLab} className="space-y-4">
          <Input
            label="Laboratory Name"
            required
            placeholder="e.g. Advanced Software Engineering Lab"
            value={labForm.name}
            onChange={(e) => setLabForm({ ...labForm, name: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Unique Lab Code"
              required
              placeholder="e.g. ASEL-01"
              value={labForm.code}
              onChange={(e) => setLabForm({ ...labForm, code: e.target.value.toUpperCase() })}
            />
            <Select
              label="Working Capacity"
              value={labForm.capacity}
              onChange={(e) => setLabForm({ ...labForm, capacity: e.target.value })}
              options={[
                { label: '30 Workstations (PCs)', value: '30' },
                { label: '60 Workstations (PCs)', value: '60' },
                { label: '90 Workstations (PCs)', value: '90' },
              ]}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Room Number"
              placeholder="e.g. Room 304"
              value={labForm.room_number}
              onChange={(e) => setLabForm({ ...labForm, room_number: e.target.value })}
            />
            <Input
              label="Physical Location"
              placeholder="e.g. Tech Block, 3rd Floor"
              value={labForm.location}
              onChange={(e) => setLabForm({ ...labForm, location: e.target.value })}
            />
          </div>

          <Input
            label="Starting IP Address"
            required
            placeholder="e.g. 127.0.0.1 or 192.168.1.1"
            value={labForm.ip_start}
            onChange={(e) => setLabForm({ ...labForm, ip_start: e.target.value })}
            helperText="The system will generate sequential IP addresses for each PC by incrementing the last octet (e.g. 127.0.0.1 to 127.0.0.30)."
          />

          {departments.length > 0 && (
            <Select
              label="Owning Academic Department"
              value={labForm.department_id}
              onChange={(e) => setLabForm({ ...labForm, department_id: e.target.value })}
              options={departments.map((d) => ({
                label: `${d.name} (${d.code})`,
                value: d.id,
              }))}
            />
          )}

          <div className="p-3 rounded-lg bg-brand-soft/10 border border-brand-teal/20 text-xs text-light-muted dark:text-dark-muted flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-teal dark:text-brand-darkAction shrink-0 mt-0.5" />
            <span>
              Each generated PC will be provisioned with a sequential IP address, a registered hardware MAC address, and a unique Device ID token for strict attendance verification.
            </span>
          </div>

          <div className="flex justify-end gap-3 pt-3">
            <Button variant="ghost" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Create Laboratory & Generate PCs
            </Button>
          </div>
        </form>
      </Modal>

      {/* WORKSTATIONS VIEWER MODAL */}
      <Modal
        isOpen={!!viewingLab}
        onClose={() => setViewingLab(null)}
        title={`Registered PCs – ${viewingLab?.name} (${viewingLab?.code})`}
        subtitle={`Total ${workstations.length} workstations provisioned with sequential IPs, MAC addresses, and unique Device IDs.`}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <Input
              placeholder="Search by PC code, IP, MAC, or Device ID..."
              value={workstationSearch}
              onChange={(e) => setWorkstationSearch(e.target.value)}
              className="py-1 text-xs"
            />
            <Badge variant="teal" size="sm">
              {filteredWorkstations.length} PCs Listed
            </Badge>
          </div>

          {isLoadingWorkstations ? (
            <LoadingSkeleton count={3} />
          ) : (
            <div className="max-h-96 overflow-y-auto rounded-lg border border-light-border dark:border-dark-border">
              <table className="w-full text-left text-xs">
                <thead className="bg-light-bg dark:bg-dark-bg text-light-muted dark:text-dark-muted font-semibold sticky top-0 border-b border-light-border dark:border-dark-border">
                  <tr>
                    <th className="p-2.5">PC / Seat</th>
                    <th className="p-2.5">Sequential IP</th>
                    <th className="p-2.5">MAC Address</th>
                    <th className="p-2.5">Unique Device ID</th>
                    <th className="p-2.5 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-light-border dark:divide-dark-border bg-light-surface dark:bg-dark-surface">
                  {filteredWorkstations.map((ws) => (
                    <tr key={ws.id} className="hover:bg-slate-50 dark:hover:bg-[#202b2c]/80 transition-colors">
                      <td className="p-2.5 font-bold text-light-text dark:text-dark-text font-mono">
                        {ws.workstation_code}
                      </td>
                      <td className="p-2.5 font-mono text-brand-teal dark:text-brand-darkAction font-semibold">
                        {ws.ip_address || '—'}
                      </td>
                      <td className="p-2.5 font-mono text-light-muted dark:text-dark-muted text-[11px]">
                        {ws.mac_address || '—'}
                      </td>
                      <td className="p-2.5 font-mono text-[11px] text-light-muted dark:text-dark-muted truncate max-w-[140px]" title={ws.device_id}>
                        {ws.device_id || '—'}
                      </td>
                      <td className="p-2.5 text-right">
                        <Badge variant="success" size="sm" dot>
                          {ws.status || 'Active'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button variant="secondary" size="sm" onClick={() => setViewingLab(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* CONFIRM DELETE MODAL */}
      <Modal
        isOpen={!!labToDelete}
        onClose={() => setLabToDelete(null)}
        title="Delete Laboratory?"
        subtitle="This action will remove the laboratory and its registered PC entries."
      >
        <p className="text-xs text-light-muted dark:text-dark-muted mb-4">
          Are you sure you want to delete <strong>{labToDelete?.name}</strong>? This operation cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setLabToDelete(null)}>
            Cancel
          </Button>
          <Button variant="danger" isLoading={isDeleting} onClick={handleDeleteLab}>
            Delete Laboratory
          </Button>
        </div>
      </Modal>
    </div>
  );
}
