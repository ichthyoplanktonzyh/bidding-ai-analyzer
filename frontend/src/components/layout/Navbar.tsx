'use client';

export default function Navbar() {
  return (
    <header className="h-14 border-b bg-white flex items-center justify-between px-6">
      <div className="text-sm text-slate-500">
        招投标信息自动化采集与AI分析平台
      </div>
      <div className="flex items-center gap-3">
        <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
        <span className="text-sm text-slate-600">系统运行中</span>
      </div>
    </header>
  );
}
