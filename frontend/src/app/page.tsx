'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { healthCheck } from '@/lib/api';

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<string>('检查中...');

  useEffect(() => {
    healthCheck()
      .then(() => setBackendStatus('运行中'))
      .catch(() => setBackendStatus('未连接'));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">仪表盘</h2>
        <p className="text-slate-500 mt-1">高校AI招投标分析系统概览</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          title="后端服务"
          value={backendStatus}
          status={backendStatus === '运行中' ? 'online' : 'offline'}
        />
        <StatusCard
          title="数据信源"
          value="中国政府采购网"
          status="online"
        />
        <StatusCard
          title="AI引擎"
          value="DeepSeek / Dify"
          status="online"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <QuickActionCard
          title="新建采集分析任务"
          description="设置关键词和时间范围，自动采集并分析招投标信息"
          href="/tasks/create"
          actionLabel="创建任务"
        />
        <QuickActionCard
          title="查看历史任务"
          description="浏览已创建的任务，查看分析结果并导出数据"
          href="/tasks"
          actionLabel="查看任务"
        />
      </div>
    </div>
  );
}

function StatusCard({
  title,
  value,
  status,
}: {
  title: string;
  value: string;
  status: 'online' | 'offline';
}) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-slate-500">{title}</p>
      <div className="flex items-center gap-2 mt-2">
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            status === 'online' ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="text-lg font-semibold text-slate-800">{value}</span>
      </div>
    </div>
  );
}

function QuickActionCard({
  title,
  description,
  href,
  actionLabel,
}: {
  title: string;
  description: string;
  href: string;
  actionLabel: string;
}) {
  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 mb-4">{description}</p>
      <Link
        href={href}
        className="inline-flex items-center px-4 py-2 bg-slate-800 text-white rounded-md text-sm hover:bg-slate-700 transition-colors"
      >
        {actionLabel} →
      </Link>
    </div>
  );
}
