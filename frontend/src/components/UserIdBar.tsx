import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function UserIdBar() {
  const { userId, siteId, setUserId, setSiteId } = useAuth();
  const [editing, setEditing] = useState(false);
  const [tmpUser, setTmpUser] = useState(userId);
  const [tmpSite, setTmpSite] = useState(siteId);

  if (!editing) {
    return (
      <div className="flex items-center gap-4 bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800">
        <span className="font-semibold">[임시 인증]</span>
        <span>User: <code className="font-mono bg-yellow-100 px-1">{userId || '(미설정)'}</code></span>
        <span>Site: <code className="font-mono bg-yellow-100 px-1">{siteId || '(미설정)'}</code></span>
        <button
          onClick={() => { setTmpUser(userId); setTmpSite(siteId); setEditing(true); }}
          className="ml-2 underline text-yellow-700 hover:text-yellow-900"
        >
          변경
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm">
      <span className="font-semibold text-yellow-800">[임시 인증]</span>
      <label className="text-yellow-800">User ID:</label>
      <input
        className="border border-yellow-300 rounded px-2 py-0.5 w-44 font-mono text-xs"
        value={tmpUser ?? ''}
        onChange={(e) => setTmpUser(e.target.value === '' ? null : Number(e.target.value))}
      />
      <label className="text-yellow-800">Site ID:</label>
      <input
        className="border border-yellow-300 rounded px-2 py-0.5 w-36 font-mono text-xs"
        value={tmpSite ?? ''}
        onChange={(e) => setTmpSite(e.target.value === '' ? null : Number(e.target.value))}
      />
      <button
        onClick={() => { setUserId(tmpUser); setSiteId(tmpSite); setEditing(false); }}
        className="bg-yellow-500 text-white px-3 py-0.5 rounded hover:bg-yellow-600"
      >
        저장
      </button>
      <button onClick={() => setEditing(false)} className="text-yellow-700 underline">
        취소
      </button>
    </div>
  );
}
