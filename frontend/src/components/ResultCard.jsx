import React, { useState } from 'react';

function ResultCard({ reportData }) {
  if (!reportData) return null;

  const { decision, confidence_score, report } = reportData;
  const breakDown = report?.breakdown;

  const getDecisionColor = () => {
    if (decision === 'APPROVED') return 'text-green-500 border-green-500 bg-green-500/10';
    if (decision === 'ESCALATED') return 'text-yellow-500 border-yellow-500 bg-yellow-500/10';
    return 'text-red-500 border-red-500 bg-red-500/10';
  };

  const ExpandableSection = ({ title, score, children, defaultOpen = false }) => {
    const [open, setOpen] = useState(defaultOpen);
    return (
      <div className="border border-neutral-800 mb-2">
        <button 
          onClick={() => setOpen(!open)}
          className="w-full flex justify-between items-center bg-neutral-900 border-b border-neutral-800 p-4 hover:bg-neutral-800 transition-colors"
        >
          <span className="font-display tracking-widest uppercase">{title}</span>
          <div className="flex items-center gap-4">
            <span className="text-sm font-body text-neutral-400">{(score * 100).toFixed(0)}% Match</span>
            <span className="text-accent">{open ? '−' : '+'}</span>
          </div>
        </button>
        {open && (
          <div className="p-4 bg-black font-body text-sm text-neutral-300">
            {children}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="card-sharp flex flex-col w-full !p-0">
      <div className="p-6 border-b border-neutral-800 flex justify-between items-end">
        <div>
          <h2 className="text-2xl mb-1">Execution Report</h2>
          <p className="text-neutral-500 text-sm font-display tracking-widest">ID: {reportData.id}</p>
        </div>
        <div className={`px-4 py-1 border font-display tracking-widest text-lg ${getDecisionColor()}`}>
          {decision}
        </div>
      </div>

      <div className="p-6 border-b border-neutral-800">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm uppercase tracking-widest font-display text-neutral-400">Total System Confidence</span>
          <span className="text-xl font-display">{(confidence_score * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-neutral-900 h-2">
          <div 
            className="h-full bg-accent transition-all duration-1000" 
            style={{ width: `${(confidence_score * 100).toFixed(0)}%` }}
          />
        </div>
      </div>

      {breakDown && (
        <div className="p-6 flex flex-col gap-2">
          
          {decision === 'REJECTED' && breakDown.tamper?.score === 0 && (
             <div className="mb-4 bg-red-950/40 border border-red-500 p-4">
               <h3 className="text-red-500 font-display tracking-widest mb-1 text-lg">⚠️ FORENSIC FAILURE</h3>
               <p className="font-body text-sm text-red-200">{breakDown.tamper.details}</p>
             </div>
          )}

          <ExpandableSection title="I. Tamper Forensics" score={breakDown.tamper?.score || 0}>
            <p>{breakDown.tamper?.details}</p>
          </ExpandableSection>
          
          <ExpandableSection title="II. Structure Extraction" score={breakDown.extraction?.score || 0}>
            {breakDown.extraction?.low_confidence_fields?.length > 0 ? (
              <div>
                <p className="text-yellow-500 mb-2">Low confidence entity abstractions detected:</p>
                <ul className="list-disc pl-5">
                  {breakDown.extraction.low_confidence_fields.map((field, idx) => (
                    <li key={idx} className="text-neutral-400">{field}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>All entity vectors mapped with target threshold confidence.</p>
            )}
          </ExpandableSection>
          
          <ExpandableSection title="III. Consistency Synthesis" score={breakDown.consistency?.score || 0}>
             {breakDown.consistency?.mismatches?.length > 0 ? (
              <ul className="flex flex-col gap-2">
                {breakDown.consistency.mismatches.map((mismatch, idx) => (
                  <li key={idx} className="bg-neutral-900 border-l border-accent p-2 pl-3">{mismatch}</li>
                ))}
              </ul>
            ) : (
              <p>Perfect synthesis alignment across documents.</p>
            )}
          </ExpandableSection>
          
          <ExpandableSection title="IV. Compliance Verification" score={breakDown.compliance?.score || 0}>
             {breakDown.compliance?.rules?.length > 0 && (
               <div className="grid grid-cols-1 gap-2">
                 {breakDown.compliance.rules.map((rule, idx) => (
                    <div key={idx} className="flex flex-col gap-1 bg-neutral-900 p-3">
                      <div className="flex justify-between">
                         <span className="font-display tracking-widest text-white">{rule.rule}</span>
                         <span className={rule.passed ? "text-green-500" : "text-red-500"}>{rule.passed ? "PASS" : "FAIL"}</span>
                      </div>
                      <p className="text-xs text-neutral-400">{rule.reason}</p>
                    </div>
                 ))}
               </div>
             )}
          </ExpandableSection>

        </div>
      )}

    </div>
  );
}

export default ResultCard;
