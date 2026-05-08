'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { label: '仪表盘', href: '/', icon: '📊' },
  { label: '任务列表', href: '/tasks', icon: '📋' },
  { label: '创建任务', href: '/tasks/create', icon: '➕' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-800 text-white min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold">Bidding AI Analyzer</h1>
        <p className="text-sm text-slate-400 mt-1">高校AI招投标分析系统</p>
      </div>

      <nav>
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-slate-700 text-white'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-auto pt-8 text-xs text-slate-500">
        v0.1.0 · MIT License
      </div>
    </aside>
  );
}
