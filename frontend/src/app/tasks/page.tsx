'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listTasks } from '@/lib/api';
import type { Task } from '@/lib/types';

const statusLabels: Record<string, string> = {
  pending: '等待中',
  spidering: '采集中',
  awaiting_decision: '等待决策',
  analyzing: 'AI分析中',
  completed: '已完成',
  failed: '失败',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  spidering: 'bg-blue-100 text-blue-800',
  awaiting_decision: 'bg-orange-100 text-orange-800',
  analyzing: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listTasks()
      .then((data) => setTasks(data.tasks))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">任务列表</h2>
          <p className="text-slate-500 mt-1">管理所有采集分析任务</p>
        </div>
        <Link
          href="/tasks/create"
          className="px-4 py-2 bg-slate-800 text-white rounded-md text-sm hover:bg-slate-700 transition-colors"
        >
          + 创建任务
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">加载中...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <p className="text-slate-500">暂无任务</p>
          <Link href="/tasks/create" className="text-blue-600 hover:underline mt-2 inline-block">
            创建第一个任务
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-slate-50">
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">任务ID</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">关键词</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">状态</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">进度</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">数据量</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">创建时间</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">操作</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id} className="border-b last:border-0">
                  <td className="px-4 py-3 text-sm font-mono text-slate-600">{task.id}</td>
                  <td className="px-4 py-3 text-sm text-slate-800">{task.keyword}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${statusColors[task.status] || 'bg-gray-100'}`}>
                      {statusLabels[task.status] || task.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="w-24 bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-slate-800 h-2 rounded-full transition-all"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {task.analyzed_items}/{task.total_items}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(task.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/tasks/${task.id}`}
                      className="text-blue-600 hover:underline text-sm"
                    >
                      查看详情
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
