import { useState, useEffect } from 'react';
import client from '../api/client';
import HistoryTable from '../components/HistoryTable';
import ResultCard from '../components/ResultCard';

function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReportId, setSelectedReportId] = useState(null);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await client.get('/verify/history');
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleView = async (id) => {
    setSelectedReportId(id);
    try {
      const res = await client.get(`/verify/${id}`);
      setReportData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="w-full flex flex-col relative fade-in">
       <div className="w-full border-b border-neutral-800 mb-8 pb-4">
        <h1 className="text-4xl mb-2">Operation History</h1>
        <p className="text-neutral-400 font-body text-sm uppercase tracking-wide">Historical execution logs mapping decrypted payloads.</p>
      </div>

      {loading ? (
        <div className="text-center font-display tracking-widest text-accent mt-12 animate-pulse">LOADING LOGS...</div>
      ) : (
        <HistoryTable data={history} onView={handleView} />
      )}

      {selectedReportId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-sm" 
            onClick={() => { setSelectedReportId(null); setReportData(null); }}
          ></div>
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto no-scrollbar border-l border-r border-accent p-2 bg-black">
            <button 
                onClick={() => { setSelectedReportId(null); setReportData(null); }}
                className="absolute top-4 right-4 text-white hover:text-accent font-display z-10 px-4 py-1 bg-black border border-neutral-700"
            >
              CLOSE
            </button>
            <div className="mt-12 w-full">
              {reportData ? (
                 <ResultCard reportData={reportData} />
              ) : (
                 <div className="bg-black p-12 text-center border border-neutral-800 text-accent font-display tracking-widest animate-pulse">
                    DECRYPTING PAYLOAD DB...
                 </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HistoryPage;
