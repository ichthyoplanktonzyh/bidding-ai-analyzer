'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createTask, getDefaultKeywords, listKeywordPresets } from '@/lib/api';
import type { FilterKeywordsPreset } from '@/lib/types';

export default function CreateTaskPage() {
  const router = useRouter();
  const [keyword, setKeyword] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [filterKeywords, setFilterKeywords] = useState<string[]>([]);
  const [newFilterWord, setNewFilterWord] = useState('');
  const [presets, setPresets] = useState<FilterKeywordsPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getDefaultKeywords()
      .then((data) => setFilterKeywords(data.keywords))
      .catch(() => setFilterKeywords(['大学', '学院']));
    listKeywordPresets()
      .then((data) => setPresets(data))
      .catch(() => {});
  }, []);

  const addFilterKeyword = () => {
    const word = newFilterWord.trim();
    if (word && !filterKeywords.includes(word)) {
      setFilterKeywords([...filterKeywords, word]);
      setNewFilterWord('');
    }
  };

  const removeFilterKeyword = (word: string) => {
    setFilterKeywords(filterKeywords.filter((k) => k !== word));
  };

  const applyPreset = (presetId: string) => {
    const preset = presets.find((p) => p.id === presetId);
    if (preset) setFilterKeywords(preset.keywords);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) {
      setError('请输入搜索关键词');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const task = await createTask({
        keyword: keyword.trim(),
        start_time: startTime || undefined,
        end_time: endTime || undefined,
        filter_keywords: filterKeywords,
      });
      router.push(`/tasks/${task.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建任务失败');
    } finally {
      setLoading(false);
    }
  };

  const quickKeywords = ['AI', '人工智能', '大模型', '智能', '机器学习', '深度学习'];

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">创建采集分析任务</h2>
        <p className="text-slate-500 mt-1">设置关键词和过滤条件，系统将自动采集招投标信息</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border p-6 space-y-5">
        {/* Search Keyword */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            搜索关键词 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="例如：AI、人工智能、大模型"
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <div className="flex flex-wrap gap-2 mt-2">
            {quickKeywords.map((kw) => (
              <button
                key={kw}
                type="button"
                onClick={() => setKeyword(kw)}
                className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs hover:bg-slate-200 transition-colors"
              >
                {kw}
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">开始日期</label>
            <input
              type="date"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">结束日期</label>
            <input
              type="date"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
        </div>

        {/* Filter Keywords */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm font-medium text-slate-700">
              高校过滤关键词
            </label>
            {presets.length > 0 && (
              <select
                onChange={(e) => applyPreset(e.target.value)}
                defaultValue=""
                className="text-xs border rounded px-2 py-1 text-slate-500"
              >
                <option value="" disabled>选择预设方案...</option>
                {presets.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            )}
          </div>
          <p className="text-xs text-slate-400 mb-2">
            采集结果中标题或采购人包含以下任一关键词才会被保留
          </p>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {filterKeywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
              >
                {kw}
                <button
                  type="button"
                  onClick={() => removeFilterKeyword(kw)}
                  className="text-blue-400 hover:text-red-500"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newFilterWord}
              onChange={(e) => setNewFilterWord(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addFilterKeyword(); } }}
              placeholder="输入过滤词后按回车添加"
              className="flex-1 px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
            <button
              type="button"
              onClick={addFilterKeyword}
              className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-md text-sm hover:bg-slate-200 transition-colors"
            >
              添加
            </button>
          </div>
        </div>

        {error && (
          <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded">{error}</div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-slate-800 text-white rounded-md text-sm hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '创建中...' : '创建并启动采集'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2 border rounded-md text-sm text-slate-600 hover:bg-slate-50"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  );
}
