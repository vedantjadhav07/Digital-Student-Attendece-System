import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Button from '../../components/common/Button';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text">
      <div className="w-16 h-16 rounded-2xl bg-brand-violet/10 text-brand-violet flex items-center justify-center mb-4">
        <ShieldAlert className="w-8 h-8" />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight">404</h1>
      <h2 className="text-xl font-bold mt-2">Page Not Found</h2>
      <p className="text-xs text-light-muted dark:text-dark-muted max-w-sm mt-1 mb-6">
        The requested URL was not found on the Labora academic platform.
      </p>
      <Link to="/">
        <Button variant="primary" size="md" icon={ArrowLeft}>
          Return to Labora Home
        </Button>
      </Link>
    </div>
  );
}

