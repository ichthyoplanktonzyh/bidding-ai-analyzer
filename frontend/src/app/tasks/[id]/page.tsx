'use client';

import { useEffect, useState, use } from 'react';
import { getTask, getTaskResults, getExportExcelUrl, getExportCsvUrl } from '@/lib/api';
import type { Task, ResultRecord } from '@/lib/types';

const statusLabels: Record<string, string> = {
  pending: '等待中',
  spidering: '采集中',
  analyzing: '分析中',
  completed: '已完成',
  failed: '失败',
};

export default function TaskDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [task, setTask] = useState<Task | null>(null);
  const [results, setResults] = useState<ResultRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let pollTimer: ReturnType<typeof setInterval>;

    const fetchTask = async () => {
      try {
        const t = await getTask(id);
        setTask(t);

        if (t.status === 'completed' || t.status === 'failed') {
          clearInterval(pollTimer);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTask();
    pollTimer = setInterval(fetchTask, 3000);
    return () => clearInterval(pollTimer);
  }, [id]);

  useEffect(() => {
    if (task?.status === 'completed') {
      getTaskResults(id, 0, 100)
        .then((data) => {
          setResults(data.results);
          setTotal(data.total);
          setSuccessCount(data.success_count);
        })
        .catch(console.error);
    }
  }, [task?.status, id]);

  if (loading) {
    return <div className="text-center py-12 text-slate-500">加载中...</div>;
  }

  if (!task) {
    return <div className="text-center py-12 text-red-500">任务未找到</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">任务详情</h2>
        <p className="text-slate-500 mt-1">ID: {task.id}</p>
      </div>

      {/* Task Info */}
      <div className="bg-white rounded-lg border p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InfoItem label="关键词" value={task.keyword} />
          <InfoItem label="状态" value={statusLabels[task.status] || task.status} />
          <InfoItem label="进度" value={`${task.progress}%`} />
          <InfoItem label="数据量" value={`${task.analyzed_items}/${task.total_items}`} />
        </div>

        {/* Progress bar */}
        {task.status !== 'completed' && task.status !== 'failed' && (
          <div className="mt-4">
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div
                className="bg-slate-800 h-3 rounded-full transition-all duration-500"
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {task.status === 'spidering' ? '正在采集招投标数据...' : '正在AI分析招投标文件...'}
            </p>
          </div>
        )}

        {task.status === 'failed' && task.error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">{task.error}</div>
        )}
      </div>

      {/* Export buttons */}
      {task.status === 'completed' && (
        <div className="flex gap-3">
          <a
            href={getExportExcelUrl(id)}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition-colors"
          >
            导出 Excel
          </a>
          <a
            href={getExportCsvUrl(id)}
            className="px-4 py-2 bg-slate-600 text-white rounded-md text-sm hover:bg-slate-700 transition-colors"
          >
            导出 CSV
          </a>
        </div>
      )}

      {/* Results table */}
      {task.status === 'completed' && (
        <div className="bg-white rounded-lg border overflow-hidden">
          <div className="px-4 py-3 border-b bg-slate-50">
            <h3 className="font-medium text-slate-800">
              分析结果（共 {total} 条，成功 {successCount} 条）
            </h3>
          </div>

          {results.length === 0 ? (
            <div className="text-center py-8 text-slate-500">暂无分析结果</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">标题</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">采购方</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">项目状态</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">产品/服务</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">预算</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">供应商</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => {
                    const data = r.analysis?.data;
                    return (
                      <tr key={r.index} className="border-b last:border-0">
                        <td className="px-3 py-2 text-sm max-w-xs truncate" title={r.original?.标题}>
                          <a href={r.original?.URL} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {r.original?.标题 || '-'}
                          </a>
                        </td>
                        <td className="px-3 py-2 text-sm">{data?.purchasing_entity || r.original?.采购人 || '-'}</td>
                        <td className="px-3 py-2 text-sm">{data?.project_status || '-'}</td>
                        <td className="px-3 py-2 text-sm max-w-xs truncate" title={data?.product_type || ''}>
                          {data?.product_type || '-'}
                        </td>
                        <td className="px-3 py-2 text-sm">{data?.budget_amount || '-'}</td>
                        <td className="px-3 py-2 text-sm">{data?.supplier_name || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-800 mt-0.5">{value}</p>
    </div>
  );
}
