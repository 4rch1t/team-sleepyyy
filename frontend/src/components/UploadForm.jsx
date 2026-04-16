import { useState, useRef } from 'react';
import client from '../api/client';

function UploadForm({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const aadhaarRef = useRef(null);
  const panRef = useRef(null);
  const utilityRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const aadhaarFile = aadhaarRef.current?.files[0];
    const panFile = panRef.current?.files[0];
    const utilityFile = utilityRef.current?.files[0];

    if (!aadhaarFile || !panFile || !utilityFile) {
      setError("ERROR: Provide all three documents required for payload execution.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('aadhaar', aadhaarFile);
    formData.append('pan', panFile);
    formData.append('utility_bill', utilityFile);

    try {
      const res = await client.post('/verify', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      if(onSuccess) onSuccess(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "SYS OVF ERROR: Network error. Make sure files are under 5MB threshold.");
    } finally {
      setLoading(false);
      // Reset forms safely
      if(aadhaarRef.current) aadhaarRef.current.value = "";
      if(panRef.current) panRef.current.value = "";
      if(utilityRef.current) utilityRef.current.value = "";
    }
  };

  return (
    <div className="card-sharp flex flex-col w-full">
      <h2 className="text-2xl mb-6">Execution Payload</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        
        {error && <div className="bg-black border border-accent text-accent p-3 text-sm font-body shadow-[0_0_10px_rgba(255,61,0,0.2)]">{error}</div>}

        <div className="flex flex-col gap-2 relative">
          <label className="text-sm font-display text-neutral-500 uppercase tracking-widest">Module 01: Aadhaar Document</label>
          <input 
            type="file" 
            ref={aadhaarRef}
            accept="image/jpeg, image/png, application/pdf"
            className="input-sharp py-3 px-2 border-neutral-800 text-sm"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-display text-neutral-500 uppercase tracking-widest">Module 02: PAN Document</label>
          <input 
            type="file" 
            ref={panRef}
            accept="image/jpeg, image/png, application/pdf"
            className="input-sharp py-3 px-2 border-neutral-800 text-sm"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-display text-neutral-500 uppercase tracking-widest">Module 03: Utility Registry</label>
          <input 
            type="file" 
            ref={utilityRef}
            accept="image/jpeg, image/png, application/pdf"
            className="input-sharp py-3 px-2 border-neutral-800 text-sm"
          />
        </div>

        <button type="submit" className="btn-primary mt-4 w-full" disabled={loading}>
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="font-display">PROCESSING SEQUENCE...</span>
            </span>
          ) : "Execute Pipeline Sequence"}
        </button>
      </form>
    </div>
  );
}

export default UploadForm;
