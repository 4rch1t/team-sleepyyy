import React from 'react';

function HistoryTable({ data, onView }) {
  
  if (!data || data.length === 0) {
    return (
        <div className="card-sharp flex h-32 items-center justify-center text-neutral-600 border-dashed border-neutral-800">
            <span className="font-display tracking-widest uppercase">No Log Data Found</span>
        </div>
    );
  }

  const getDecisionColor = (decision) => {
    if (decision === 'APPROVED') return 'text-green-500';
    if (decision === 'ESCALATED') return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="w-full overflow-x-auto border border-neutral-800">
      <table className="w-full text-left font-body text-sm">
        <thead className="bg-neutral-900 border-b border-neutral-800">
          <tr>
            <th className="px-6 py-4 font-display tracking-widest uppercase text-neutral-400">Timestamp</th>
            <th className="px-6 py-4 font-display tracking-widest uppercase text-neutral-400">Report ID</th>
            <th className="px-6 py-4 font-display tracking-widest uppercase text-neutral-400">Confidence</th>
            <th className="px-6 py-4 font-display tracking-widest uppercase text-neutral-400">Outcome</th>
            <th className="px-6 py-4 font-display tracking-widest uppercase text-neutral-400 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-800 bg-black">
          {data.map((row) => (
            <tr key={row.id} className="hover:bg-neutral-900/50 transition-colors">
              <td className="px-6 py-4 text-neutral-300">
                 {new Date(row.created_at).toLocaleString()}
              </td>
              <td className="px-6 py-4 text-neutral-500">
                 {row.id.substring(0,8)}...
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <div className="w-16 bg-neutral-800 h-1">
                        <div className="bg-accent h-full" style={{ width: `${row.confidence_score * 100}%`}}></div>
                    </div>
                    <span className="text-white">{(row.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </td>
              <td className="px-6 py-4">
                 <span className={`font-display tracking-widest ${getDecisionColor(row.decision)}`}>
                    {row.decision}
                 </span>
              </td>
              <td className="px-6 py-4 text-right">
                <button 
                  onClick={() => onView(row.id)}
                  className="btn-secondary !text-xs !px-4 !py-1 transition-colors hover:text-accent hover:border-accent"
                >
                  DECRYPT
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default HistoryTable;
