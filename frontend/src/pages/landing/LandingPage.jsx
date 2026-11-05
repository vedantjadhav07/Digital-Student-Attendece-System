import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Radio,
  BarChart3,
  Users,
  Cpu,
  FileSpreadsheet,
  CheckCircle2,
  ArrowRight,
  Send,
  Sparkles,
  Server,
  Lock,
  Layers
} from 'lucide-react';
import { toast } from 'sonner';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Card from '../../components/common/Card';
import api from '../../services/api';

const TYPEWRITER_PHRASES = [
  'Digital Attendance',
  'Smart Lab Monitoring',
  'Real-Time Attendance',
  'Intelligent Analytics',
  'Secure Academic Management',
];

export default function LandingPage() {
  const navigate = useNavigate();

  // Typewriter effect state
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  // Contact form state
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fullText = TYPEWRITER_PHRASES[phraseIndex];
    const typingSpeed = isDeleting ? 40 : 90;

    const timer = setTimeout(() => {
      if (!isDeleting) {
        setCurrentText(fullText.substring(0, currentText.length + 1));
        if (currentText.length + 1 === fullText.length) {
          setTimeout(() => setIsDeleting(true), 1800);
        }
      } else {
        setCurrentText(fullText.substring(0, currentText.length - 1));
        if (currentText.length === 0) {
          setIsDeleting(false);
          setPhraseIndex((prev) => (prev + 1) % TYPEWRITER_PHRASES.length);
        }
      }
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [currentText, isDeleting, phraseIndex]);

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      toast.error('Please fill in all required fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await api.post('/api/contact', contactForm);
      toast.success(res.data.message || 'Your inquiry has been received! Our team will contact you shortly.');
      setContactForm({ name: '', email: '', subject: '', message: '' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit message. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div id="home" className="space-y-24 pb-16 overflow-hidden">
      {/* 1. HERO SECTION */}
      <section className="relative pt-16 sm:pt-24 lg:pt-32 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Brand Tag */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-teal/30 bg-brand-soft/20 text-brand-deep dark:text-brand-darkAction text-xs font-semibold tracking-wide uppercase shadow-subtle mb-6">
          <Sparkles className="w-3.5 h-3.5 text-brand-teal dark:text-brand-darkAction" />
          Next-Gen Academic Laboratory Platform
        </div>

        {/* Main Title & Typewriter */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-light-text dark:text-dark-text max-w-4xl mx-auto leading-tight sm:leading-none">
          Next Generation of <br />
          <span className="text-brand-teal dark:text-brand-darkAction inline-block min-h-[1.2em]">
            {currentText}
            <span className="inline-block w-1 h-9 sm:h-12 bg-brand-teal dark:bg-brand-darkAction ml-1 animate-pulse align-middle" />
          </span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-light-muted dark:text-dark-muted max-w-2xl mx-auto">
          Labora transforms academic laboratories into smart, secure, and automated learning spaces with real-time workstation telemetry, live session management, and instant analytics.
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Button
            size="lg"
            variant="primary"
            onClick={() => navigate('/login')}
            className="shadow-subtle"
          >
            Launch Attendance Portal
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>
          <a href="#features">
            <Button size="lg" variant="secondary">
              Explore Capabilities
            </Button>
          </a>
        </div>

        {/* Hero Visual Mockup Preview */}
        <div className="mt-14 max-w-5xl mx-auto relative rounded-xl border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-card p-4 sm:p-6 transition-all hover:border-brand-teal/40">
          <div className="flex items-center justify-between pb-4 border-b border-light-border dark:border-dark-border text-xs text-light-muted dark:text-dark-muted">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
              <span className="ml-2 font-mono text-[11px]">labora.academic.portal / live-session</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold uppercase text-[10px] tracking-wider">Live Monitoring Active</span>
            </div>
          </div>
          {/* Simulated Lab Grid Preview */}
          <div className="mt-6 grid grid-cols-5 sm:grid-cols-10 gap-2 sm:gap-3 py-4">
            {Array.from({ length: 30 }).map((_, idx) => {
              const isOccupied = idx < 22;
              return (
                <div
                  key={idx}
                  className={`h-11 sm:h-12 rounded-lg flex flex-col items-center justify-center border text-[11px] font-bold transition-all ${
                    isOccupied
                      ? 'bg-brand-soft/20 border-brand-teal/40 text-brand-teal dark:text-brand-darkAction dark:bg-brand-teal/15'
                      : 'bg-light-bg dark:bg-dark-bg border-light-border dark:border-dark-border text-light-muted dark:text-dark-muted'
                  }`}
                >
                  <Cpu className="w-3.5 h-3.5 mb-0.5 opacity-80" />
                  <span>WS-{(idx + 1).toString().padStart(2, '0')}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 2. CORE FEATURES (Alternating Cards) */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-teal dark:text-brand-darkAction">
            Enterprise Features
          </h2>
          <h3 className="text-3xl font-extrabold text-light-text dark:text-dark-text tracking-tight mt-1">
            Engineered for Academic Rigor & Performance
          </h3>
          <p className="mt-2 text-sm text-light-muted dark:text-dark-muted">
            From single-click verified attendance to instant exportable reports, Labora elevates laboratory management.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center mb-4">
              <Radio className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Real-Time Workstation Grid
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              Dynamically scales to 30, 60, or 90 workstations. Teachers monitor live check-ins through authenticated WebSockets without manual refreshes.
            </p>
          </Card>

          {/* Feature 2 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Subnet & Geofence Verification
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              Prevents proxy and remote logins by validating client IP addresses against registered campus laboratory subnet ranges.
            </p>
          </Card>

          {/* Feature 3 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Student Attendance Defaulter Alerts
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              Instant visual highlights and automated tracking for students falling below the mandatory 75% attendance threshold.
            </p>
          </Card>

          {/* Feature 4 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center mb-4">
              <Users className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Bulk Student & Faculty Onboarding
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              Effortlessly import hundreds of student records using CSV or Excel files with pre-validation and row-level error reporting.
            </p>
          </Card>

          {/* Feature 5 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center mb-4">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Direct Excel & PDF Reporting
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              Produce beautifully styled, official academic attendance sheets ready for departmental reviews and university audits.
            </p>
          </Card>

          {/* Feature 6 */}
          <Card hover className="relative">
            <div className="w-10 h-10 rounded-lg bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction flex items-center justify-center mb-4">
              <Lock className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Argon2id Secure Authentication
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2 leading-relaxed">
              State-of-the-art password hashing, strict CSRF defense, rate-limited endpoints, and role-based access control.
            </p>
          </Card>
        </div>
      </section>

      {/* 3. HOW IT WORKS (3 Steps Timeline) */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-teal dark:text-brand-darkAction">
            Workflow Architecture
          </h2>
          <h3 className="text-3xl font-extrabold text-light-text dark:text-dark-text tracking-tight mt-1">
            How Labora Works in Three Steps
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Step 1 */}
          <div className="relative p-6 rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-card flex flex-col items-center text-center">
            <div className="w-10 h-10 rounded-full bg-brand-deep dark:bg-brand-teal text-white dark:text-[#151D1E] font-bold text-sm flex items-center justify-center shadow-subtle mb-4">
              1
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Faculty Launches Lab Session
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2">
              The teacher selects the assigned subject, chooses the laboratory room, and configures the session duration and workstation capacity.
            </p>
          </div>

          {/* Step 2 */}
          <div className="relative p-6 rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-card flex flex-col items-center text-center">
            <div className="w-10 h-10 rounded-full bg-brand-deep dark:bg-brand-teal text-white dark:text-[#151D1E] font-bold text-sm flex items-center justify-center shadow-subtle mb-4">
              2
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Student Checks In
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2">
              The student logs in from their designated lab workstation. The portal detects the active session and verifies subnet integrity with a single click.
            </p>
          </div>

          {/* Step 3 */}
          <div className="relative p-6 rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-card flex flex-col items-center text-center">
            <div className="w-10 h-10 rounded-full bg-brand-deep dark:bg-brand-teal text-white dark:text-[#151D1E] font-bold text-sm flex items-center justify-center shadow-subtle mb-4">
              3
            </div>
            <h4 className="text-base font-bold text-light-text dark:text-dark-text">
              Live Telemetry & Reporting
            </h4>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2">
              The teacher's screen updates in real time via WebSockets. Once the session ends, attendance data is archived with full audit logs and Excel exports.
            </p>
          </div>
        </div>
      </section>

      {/* 4. CONTACT US SECTION */}
      <section id="contact" className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="p-6 sm:p-10 border-light-border dark:border-dark-border shadow-card">
          <div className="text-center max-w-xl mx-auto mb-8">
            <h2 className="text-xs font-bold uppercase tracking-wider text-brand-teal dark:text-brand-darkAction">
              Get In Touch
            </h2>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-light-text dark:text-dark-text tracking-tight mt-1">
              Have Questions or Need College Deployment?
            </h3>
            <p className="text-xs text-light-muted dark:text-dark-muted mt-2">
              Send us a message and our technical administrators will respond promptly.
            </p>
          </div>

          <form onSubmit={handleContactSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name"
                required
                placeholder="Dr. Rajesh Sharma"
                value={contactForm.name}
                onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
              />
              <Input
                label="Email Address"
                type="email"
                required
                placeholder="rajesh@college.edu"
                value={contactForm.email}
                onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
              />
            </div>
            <Input
              label="Subject / College Department"
              placeholder="Computer Science & Engineering Lab Deployment"
              value={contactForm.subject}
              onChange={(e) => setContactForm({ ...contactForm, subject: e.target.value })}
            />
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-light-text dark:text-dark-text">
                Message <span className="text-brand-teal">*</span>
              </label>
              <textarea
                rows={4}
                required
                className="w-full rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text p-3 text-sm outline-none focus:ring-1 focus:ring-brand-teal focus:border-brand-teal"
                placeholder="Write your questions or deployment requirements here..."
                value={contactForm.message}
                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
              />
            </div>
            <div className="pt-2 flex justify-end">
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                icon={Send}
              >
                Send Inquiry
              </Button>
            </div>
          </form>
        </Card>
      </section>

      {/* 5. FOOTER */}
      <footer className="border-t border-light-border dark:border-dark-border pt-12 text-xs text-light-muted dark:text-dark-muted">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-brand-deep p-1 flex items-center justify-center">
              <img src="/logo.svg" alt="Labora" className="w-full h-full object-contain" />
            </div>
            <span className="font-bold text-light-text dark:text-dark-text text-sm">
              Labora – Smart Digital Attendance
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#home" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Home</a>
            <a href="#features" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">How It Works</a>
            <a href="#contact" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Contact</a>
          </div>
          <div>
            &copy; {new Date().getFullYear()} Labora. Academic Computer Laboratories. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

