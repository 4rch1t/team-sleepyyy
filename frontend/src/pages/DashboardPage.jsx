import { useState } from 'react';
import client from '../api/client';
import UploadForm from '../components/UploadForm';
import ResultCard from '../components/ResultCard';

function DashboardPage() {
  const [result, setResult] = useState(null);

  const handleSuccess = (data) => {
    fetchFullResult(data.id);
  };

  const fetchFullResult = async (id) => {
    try {
      const res = await client.get(`/verify/${id}`);
      setResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-8 w-full fade-in">
      <div className="w-full border-b border-neutral-800 pb-4">
        <h1 className="text-4xl mb-2">Verification Node</h1>
        <p className="text-neutral-400 font-body text-sm uppercase tracking-wide">Secure execution payload mapping.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start">
        <div className="w-full">
          <UploadForm onSuccess={handleSuccess} />
        </div>
        
        <div className="w-full">
          {result ? (
            <ResultCard reportData={result} />
          ) : (
            <div className="card-sharp flex flex-col h-64 items-center justify-center text-neutral-600 border-dashed border-neutral-800 gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="square" strokeLinejoin="miter"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              <span className="font-display tracking-widest uppercase">Awaiting Submission Stream</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
