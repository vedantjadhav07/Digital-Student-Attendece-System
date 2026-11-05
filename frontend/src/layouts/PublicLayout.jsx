import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/common/Navbar';

export default function PublicLayout() {
  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text transition-colors flex flex-col">
      <Navbar isPublic={true} />
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}

