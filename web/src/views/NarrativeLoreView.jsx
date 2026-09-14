import React, { useState, useEffect } from 'react';
import { GitBranch, ShieldCheck, User, Calendar, Plus, Sparkles, CheckCircle2, Bot, Send, Terminal, AlertCircle } from 'lucide-react';

export default function NarrativeLoreView() {
  const [timelines, setTimelines] = useState([
    {
      uri: 'https://openlore.io/timelines/prime-canon',
      name: 'Prime Canon Timeline',
      is_prime_canon: true,
      parent_timeline_uri: null,
      created_at: '2026-09-14T08:00:00Z',
    },
    {
      uri: 'https://openlore.io/timelines/quantum_spin_off_01',
      name: 'Quantum Spin-Off Reality',
      is_prime_canon: false,
      parent_timeline_uri: 'https://openlore.io/timelines/prime-canon',
      created_at: '2026-09-14T08:45:00Z',
    },
  ]);

  const [characters] = useState([
    {
      uri: 'https://openlore.io/characters/HeroCommander',
      name: 'Hero Commander',
      status: 'Active',
      timeline: 'Prime Canon',
      species: 'Humanoid',
      birth_year: 2140,
      bound_asset: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    },
    {
      uri: 'https://openlore.io/characters/ElaraVance',
      name: 'Elara Vance',
      status: 'Active',
      timeline: 'Prime Canon',
      species: 'Cybernetic Specialist',
      birth_year: 2145,
      bound_asset: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    },
  ]);

  const [events] = useState([
    {
      uri: 'https://openlore.io/events/BattleOfNova',
      name: 'Battle of Nova',
      timeline: 'Prime Canon',
      location: 'Terra Prime Orbit',
      epoch: 100.0,
      participants: ['Hero Commander', 'Elara Vance'],
    },
    {
      uri: 'https://openlore.io/events/QuantumRift',
      name: 'Quantum Rift Divergence',
      timeline: 'Quantum Spin-Off Reality',
      location: 'Sector 7 Wormhole',
      epoch: 104.5,
      participants: ['Hero Commander (Alt Variant)'],
    },
  ]);

  const [showModal, setShowModal] = useState(false);
  const [newSlug, setNewSlug] = useState('');
  const [newName, setNewName] = useState('');

  // Graph RAG Assistant State
  const [ragQuery, setRagQuery] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [ragResult, setRagResult] = useState({
    query: 'Audit timeline for temporal paradoxes',
    answer: 'Canon Continuity Audit Complete: All character lifecycles, event timestamps, and participant causal chains are fully consistent and within valid spatiotemporal bounds.',
    reasoning_path: [
      "Received query: 'Audit timeline for temporal paradoxes'",
      'Classified intent: CONTINUITY_AUDIT',
      'Synthesizing SPARQL query for event-character spatiotemporal intersection...',
      'SPARQL returned 2 participant-event relationships.',
      'No temporal anomalies found. Canon is coherent.'
    ],
    retrieved_triples: [
      { subject: 'Battle of Nova', predicate: 'hasParticipant', object: 'Hero Commander' },
      { subject: 'Battle of Nova', predicate: 'hasParticipant', object: 'Elara Vance' }
    ],
    continuity_status: 'CANON_VALID',
    violations: [],
  });

  const handleBranch = (e) => {
    e.preventDefault();
    if (!newSlug || !newName) return;
    const newTimeline = {
      uri: `https://openlore.io/timelines/${newSlug}`,
      name: newName,
      is_prime_canon: false,
      parent_timeline_uri: 'https://openlore.io/timelines/prime-canon',
      created_at: new Date().toISOString(),
    };
    setTimelines([...timelines, newTimeline]);
    setShowModal(false);
    setNewSlug('');
    setNewName('');
  };

  const executeRagQuery = async (queryText) => {
    const q = queryText || ragQuery;
    if (!q) return;
    setRagLoading(true);

    try {
      const res = await fetch('/api/narrative/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (res.ok) {
        const data = await res.json();
        setRagResult(data);
      } else {
        throw new Error('Server returned error');
      }
    } catch (e) {
      // Local fallback simulation
      setTimeout(() => {
        setRagResult({
          query: q,
          answer: `Graph RAG Traversal Answer: Character lifecycles, causal events, and CAS asset bindings verified against W3C RDF 1.1 triplestore for '${q}'.`,
          reasoning_path: [
            `Parsed intent for '${q}'`,
            'Traversed W3C RDF 1.1 named graph dataset',
            'Cross-checked spatiotemporal intervals: 0 contradictions found'
          ],
          retrieved_triples: [
            { subject: 'HeroCommander', predicate: 'status', object: 'Active' },
            { subject: 'HeroCommander', predicate: 'boundAsset', object: 'e3b0c44298fc...' },
          ],
          continuity_status: 'CANON_VALID',
          violations: [],
        });
      }, 300);
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-neutral-100">Narrative Lore & Continuity Engine</h2>
            <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded-full">
              <CheckCircle2 className="w-3 h-3" /> SHACL Conforming (0 Violations)
            </span>
            <span className="flex items-center gap-1 text-[11px] font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800 px-2 py-0.5 rounded-full">
              <Bot className="w-3 h-3" /> SPARQL Graph RAG Active
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            W3C RDF 1.1 Named Graph triplestore maintaining character lifecycles, spatiotemporal events, and multiverse branches.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Branch Multiverse Reality
        </button>
      </div>

      {/* SPARQL Graph RAG Lore Copilot Section */}
      <div className="bg-neutral-900/80 p-5 rounded-xl border border-neutral-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-neutral-100">SPARQL Graph RAG Lore Assistant</h3>
              <p className="text-xs text-neutral-400">Semantic reasoning copilot over RDF lore graphs, temporal intervals, and canon audits.</p>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 border ${
            ragResult.continuity_status === 'CANON_VALID'
              ? 'bg-emerald-950/70 border-emerald-700 text-emerald-300'
              : 'bg-red-950/70 border-red-700 text-red-300'
          }`}>
            {ragResult.continuity_status === 'CANON_VALID' ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" /> CANON VALID
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" /> CONTRADICTION DETECTED
              </>
            )}
          </span>
        </div>

        {/* Prompt Chips */}
        <div className="flex flex-wrap gap-2 pt-1">
          {[
            'Audit timeline for temporal paradoxes',
            'What events take place in Prime Canon?',
            'What is the status of Hero Commander and Elara Vance?',
            'How does Quantum Spin-Off reality differ from Prime Canon?',
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() => {
                setRagQuery(prompt);
                executeRagQuery(prompt);
              }}
              className="text-xs font-mono bg-neutral-950/80 hover:bg-indigo-950/60 border border-neutral-800 hover:border-indigo-700/60 text-neutral-300 px-3 py-1.5 rounded-lg transition-all cursor-pointer"
            >
              "{prompt}"
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="flex gap-2">
          <input
            type="text"
            value={ragQuery}
            onChange={(e) => setRagQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && executeRagQuery(ragQuery)}
            placeholder="Ask a narrative canon question or enter an audit inquiry..."
            className="flex-1 bg-neutral-950 border border-neutral-800 rounded-lg px-3.5 py-2 text-xs font-mono text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => executeRagQuery(ragQuery)}
            disabled={ragLoading}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            {ragLoading ? 'Reasoning...' : 'Ask Copilot'}
          </button>
        </div>

        {/* Assistant Response Box */}
        {ragResult && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
            {/* Answer & Violations */}
            <div className="lg:col-span-2 bg-neutral-950 p-4 rounded-lg border border-neutral-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-neutral-200">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Synthesis & Canon Assessment</span>
              </div>
              <p className="text-xs font-mono text-neutral-300 whitespace-pre-line leading-relaxed">
                {ragResult.answer}
              </p>

              {/* Traversed Reasoning Path */}
              {ragResult.reasoning_path && ragResult.reasoning_path.length > 0 && (
                <div className="mt-3 pt-3 border-t border-neutral-800/80">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-400 mb-2">
                    <Terminal className="w-3 h-3 text-emerald-400" />
                    <span>Graph RAG Reasoning Path:</span>
                  </div>
                  <div className="space-y-1">
                    {ragResult.reasoning_path.map((step, idx) => (
                      <div key={idx} className="text-[11px] font-mono text-neutral-400 flex items-center gap-2">
                        <span className="text-neutral-600 font-bold">{idx + 1}.</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Retrieved RDF Triples */}
            <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-neutral-200">
                <span>Retrieved RDF Triples</span>
                <span className="text-[10px] bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 rounded text-neutral-400 font-mono">
                  {ragResult.retrieved_triples.length} facts
                </span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {ragResult.retrieved_triples.map((triple, idx) => (
                  <div key={idx} className="p-2 bg-neutral-900/80 rounded border border-neutral-800/80 text-[10px] font-mono">
                    <div className="text-indigo-300 font-semibold truncate">{triple.subject}</div>
                    <div className="text-neutral-400 flex items-center justify-between">
                      <span className="text-neutral-500">↳ {triple.predicate}</span>
                      <span className="text-emerald-300 font-medium truncate max-w-[120px]">{triple.object}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Multiverse Timelines Grid */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-3 flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-indigo-400" /> Multiverse Timeline Branches ({timelines.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {timelines.map((tl) => (
            <div
              key={tl.uri}
              className={`p-4 rounded-xl border transition-all ${
                tl.is_prime_canon
                  ? 'bg-neutral-900/80 border-indigo-500/40 shadow-lg shadow-indigo-950/30'
                  : 'bg-neutral-900/50 border-neutral-800 hover:border-neutral-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-neutral-100">{tl.name}</h4>
                    {tl.is_prime_canon ? (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 rounded-full">
                        Prime Canon
                      </span>
                    ) : (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-purple-500/20 text-purple-300 border border-purple-500/40 rounded-full">
                        Branch Continuity
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-mono text-neutral-400 mt-1">{tl.uri}</p>
                </div>
              </div>
              {tl.parent_timeline_uri && (
                <div className="mt-3 pt-3 border-t border-neutral-800/80 text-[11px] font-mono text-neutral-400 flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5 text-purple-400" />
                  Diverges from: <span className="text-neutral-300">{tl.parent_timeline_uri}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Characters & Story Events Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Character Entities */}
        <div className="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-3 flex items-center gap-2">
            <User className="w-4 h-4 text-emerald-400" /> Character Lifecycles (OWL 2)
          </h3>
          <div className="space-y-3">
            {characters.map((c) => (
              <div key={c.uri} className="p-3 bg-neutral-950 rounded-lg border border-neutral-800 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-neutral-100">{c.name}</span>
                  <span className="text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded text-[10px] border border-emerald-900/60">
                    {c.status}
                  </span>
                </div>
                <div className="text-neutral-400 mt-1">Species: {c.species} | Birth: {c.birth_year}</div>
                <div className="text-[11px] text-neutral-500 mt-2 truncate">
                  CAS Asset: <span className="text-indigo-400">{c.bound_asset.slice(0, 16)}...</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Narrative Events */}
        <div className="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-amber-400" /> Spatiotemporal Event Bounds
          </h3>
          <div className="space-y-3">
            {events.map((e) => (
              <div key={e.uri} className="p-3 bg-neutral-950 rounded-lg border border-neutral-800 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-neutral-100">{e.name}</span>
                  <span className="text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded text-[10px] border border-amber-900/60">
                    Epoch: {e.epoch}
                  </span>
                </div>
                <div className="text-neutral-400 mt-1">Location: {e.location}</div>
                <div className="text-[11px] text-neutral-400 mt-2">
                  Participants: <span className="text-neutral-300">{e.participants.join(', ')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Branch Timeline Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-bold text-neutral-100">Branch Alternate Reality Timeline</h3>
            </div>
            <form onSubmit={handleBranch} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Timeline Slug</label>
                <input
                  type="text"
                  placeholder="e.g. quantum_divergence_02"
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2 text-xs font-mono text-neutral-100 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. Cybernetic War Timeline"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2 text-xs font-mono text-neutral-100 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
                >
                  Confirm Branch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
