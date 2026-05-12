'use client';

import { useEffect, useState, use, useCallback } from 'react';
import {
  getTask,
  getTaskResults,
  getSpiderResults,
  startAnalysis,
  getExportExcelUrl,
  getExportCsvUrl,
} from '@/lib/api';
import { useTaskPolling } from '@/hooks/useTaskPolling';
import type { Task, ResultRecord, SpiderResult } from '@/lib/types';

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
  const [spiderResults, setSpiderResults] = useState<SpiderResult[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [startingAnalysis, setStartingAnalysis] = useState(false);

  // WebSocket-enabled polling
  useTaskPolling(id, useCallback((t: Task) => {
    setTask(t);
    setLoading(false);
  }, []));

  // Fetch initial task data
  useEffect(() => {
    getTask(id)
      .then((t) => {
        setTask(t);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  // Load spider results when waiting for decision
  useEffect(() => {
    if (task?.status === 'awaiting_decision') {
      getSpiderResults(id)
        .then((data) => {
          setSpiderResults(data.results);
          // Select all by default
          setSelectedIndices(new Set(data.results.map((_, i) => i)));
        })
        .catch(console.error);
    }
  }, [task?.status, id]);

  // Load analyzed results when completed
  useEffect(() => {
    if (task?.status === 'completed') {
      getTaskResults(id, 0, 500)
        .then((data) => {
          setResults(data.results);
          setTotal(data.total);
          setSuccessCount(data.success_count);
        })
        .catch(console.error);
    }
  }, [task?.status, id]);

  const handleStartAnalysis = async () => {
    setStartingAnalysis(true);
    try {
      await startAnalysis(id, {
        selected_indices: Array.from(selectedIndices),
      });
      // Task status will update via WebSocket
    } catch (err) {
      console.error('Failed to start analysis:', err);
    } finally {
      setStartingAnalysis(false);
    }
  };

  const toggleSelectAll = () => {
    if (selectedIndices.size === spiderResults.length) {
      setSelectedIndices(new Set());
    } else {
      setSelectedIndices(new Set(spiderResults.map((_, i) => i)));
    }
  };

  const toggleItem = (index: number) => {
    const next = new Set(selectedIndices);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setSelectedIndices(next);
  };

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

      {/* Task Info Card */}
      <div className="bg-white rounded-lg border p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InfoItem label="关键词" value={task.keyword} />
          <InfoItem
            label="状态"
            value={
              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[task.status] || ''}`}>
                {statusLabels[task.status] || task.status}
              </span>
            }
          />
          <InfoItem label="进度" value={`${task.progress}%`} />
          <InfoItem label="数据量" value={`${task.total_items} 条`} />
        </div>

        {task.filter_keywords.length > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-slate-500">过滤词:</span>
            <div className="flex flex-wrap gap-1">
              {task.filter_keywords.map((kw) => (
                <span key={kw} className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Progress bar for running tasks */}
        {task.status !== 'completed' && task.status !== 'failed' && (
          <div className="mt-4">
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div
                className="bg-slate-800 h-3 rounded-full transition-all duration-700"
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {task.status === 'spidering' && '正在采集招投标数据...'}
              {task.status === 'awaiting_decision' && '采集完成，请选择需要AI分析的条目'}
              {task.status === 'analyzing' && '正在AI分析招投标文件...'}
            </p>
          </div>
        )}

        {task.status === 'failed' && task.error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">{task.error}</div>
        )}
      </div>

      {/* Stage: Awaiting Decision — Show spider results with checkboxes */}
      {task.status === 'awaiting_decision' && (
        <div className="bg-white rounded-lg border overflow-hidden">
          <div className="px-4 py-3 border-b bg-orange-50 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-slate-800">
                第一阶段采集结果（共 {spiderResults.length} 条）
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                已选择 {selectedIndices.size} 条，请勾选需要进入AI分析的条目
              </p>
            </div>
            <button
              onClick={handleStartAnalysis}
              disabled={startingAnalysis || selectedIndices.size === 0}
              className="px-4 py-2 bg-orange-600 text-white rounded-md text-sm hover:bg-orange-700 disabled:opacity-50 transition-colors"
            >
              {startingAnalysis ? '启动中...' : `启动AI分析 (${selectedIndices.size}条)`}
            </button>
          </div>

          {spiderResults.length === 0 ? (
            <div className="text-center py-8 text-slate-500">暂无采集结果</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="px-3 py-2 w-10">
                      <input
                        type="checkbox"
                        checked={selectedIndices.size === spiderResults.length && spiderResults.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded"
                      />
                    </th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">#</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">标题</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">采购人</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">发布日期</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-slate-600">来源</th>
                  </tr>
                </thead>
                <tbody>
                  {spiderResults.map((item, idx) => (
                    <tr key={idx} className={`border-b last:border-0 ${selectedIndices.has(idx) ? 'bg-blue-50/30' : ''}`}>
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={selectedIndices.has(idx)}
                          onChange={() => toggleItem(idx)}
                          className="rounded"
                        />
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-500">{idx + 1}</td>
                      <td className="px-3 py-2 text-sm max-w-md truncate" title={item.标题}>
                        <a href={item.URL} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {item.标题 || '-'}
                        </a>
                      </td>
                      <td className="px-3 py-2 text-sm text-slate-600">{item.采购人 || '-'}</td>
                      <td className="px-3 py-2 text-sm text-slate-500">{item.发布日期 || '-'}</td>
                      <td className="px-3 py-2 text-sm text-slate-500">{item.来源 || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Stage: Analyzing — show progress */}
      {task.status === 'analyzing' && (
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3">
            <div className="animate-spin w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full" />
            <div>
              <p className="font-medium text-slate-800">AI分析进行中...</p>
              <p className="text-sm text-slate-500 mt-0.5">
                已分析 {task.analyzed_items}/{task.total_items} 条
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stage: Completed — Export + Results */}
      {task.status === 'completed' && (
        <>
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
        </>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-800 mt-0.5">{value}</p>
    </div>
  );
}
