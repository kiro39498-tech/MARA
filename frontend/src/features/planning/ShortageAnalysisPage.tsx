import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function ShortageAnalysisPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'material' | 'product' | 'plant'>('material');
  const [filterText, setFilterText] = useState('');
  const [filterRiskLevel, setFilterRiskLevel] = useState('all');

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/material-risk', { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setData(Array.isArray(res) ? res : []);
        setLoading(false);
      })
      .catch(() => {
        setData([]);
        setLoading(false);
      });
  }, []);

  const getRiskLevel = (score: number) => {
    if (score >= 60) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
  };

  const getRiskBadge = (score: number) => {
    const level = getRiskLevel(score);
    if (level === 'high') return <Badge className="bg-red-600 text-white text-xs">High</Badge>;
    if (level === 'medium') return <Badge className="bg-yellow-500 text-white text-xs">Medium</Badge>;
    return <Badge className="bg-green-600 text-white text-xs">Low</Badge>;
  };

  const filtered = data.filter(r => {
    const matchText = filterText === '' ||
      r.material_code?.toLowerCase().includes(filterText.toLowerCase()) ||
      r.material_name?.toLowerCase().includes(filterText.toLowerCase()) ||
      r.plant_name?.toLowerCase().includes(filterText.toLowerCase());
    const matchRisk = filterRiskLevel === 'all' || getRiskLevel(r.risk_score) === filterRiskLevel;
    return matchText && matchRisk;
  });

  const plantGroups = filtered.reduce((acc: Record<string, any>, r) => {
    const key = r.plant_name || 'Unknown';
    if (!acc[key]) acc[key] = { plant_name: key, count: 0, avgRisk: 0, totalRisk: 0, shortages: 0 };
    acc[key].count++;
    acc[key].totalRisk += r.risk_score || 0;
    acc[key].avgRisk = acc[key].totalRisk / acc[key].count;
    if (r.first_shortage_date) acc[key].shortages++;
    return acc;
  }, {});
  const plantRows = Object.values(plantGroups).sort((a: any, b: any) => b.avgRisk - a.avgRisk);

  const shortageItems = filtered.filter(r => r.first_shortage_date !== null);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Shortage Analysis</h1>
        <p className="text-muted-foreground">Pre-emptive detection of material stockouts, first shortage dates, and days of coverage.</p>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <input
          type="text"
          placeholder="Filter by material code, name, or plant..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="border p-2 rounded bg-background text-sm flex-1 min-w-[200px]"
        />
        <select
          value={filterRiskLevel}
          onChange={(e) => setFilterRiskLevel(e.target.value)}
          className="border p-2 rounded bg-background text-sm"
        >
          <option value="all">All Risk Levels</option>
          <option value="high">High Risk (≥60)</option>
          <option value="medium">Medium Risk (30-59)</option>
          <option value="low">Low Risk (&lt;30)</option>
        </select>
      </div>

      <div className="flex gap-1 border-b">
        {(['material', 'product', 'plant'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${activeTab === tab
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'}`}
          >
            {tab === 'material' ? 'Material Risk' : tab === 'product' ? 'By Shortage Status' : 'Plant-Wise Risk'}
          </button>
        ))}
      </div>

      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Analyzing shortages...</div>
          ) : activeTab === 'material' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Risk Level</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Risk Score</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">First Shortage</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Days of Coverage</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div className="font-bold">{r.material_code}</div>
                        <div className="text-xs text-muted-foreground">{r.material_name}</div>
                      </td>
                      <td className="py-3 px-4">{r.plant_name}</td>
                      <td className="py-3 px-4">{getRiskBadge(r.risk_score)}</td>
                      <td className="py-3 px-4 font-semibold text-red-500">{r.risk_score?.toFixed(1)}</td>
                      <td className="py-3 px-4 text-red-600 font-semibold">{r.first_shortage_date || '—'}</td>
                      <td className="py-3 px-4 font-bold">{r.days_of_coverage} days</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs truncate">{r.reason}</td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={7} className="text-center py-8 text-green-500 font-semibold">No risks match the current filters.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'product' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Risk Score</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">First Shortage Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Days of Coverage</th>
                  </tr>
                </thead>
                <tbody>
                  {shortageItems.map((r, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{r.material_code}</td>
                      <td className="py-3 px-4">{r.plant_name}</td>
                      <td className="py-3 px-4">{getRiskBadge(r.risk_score)}</td>
                      <td className="py-3 px-4 text-red-600 font-semibold">{r.first_shortage_date}</td>
                      <td className="py-3 px-4">{r.days_of_coverage} days</td>
                    </tr>
                  ))}
                  {shortageItems.length === 0 && (
                    <tr><td colSpan={5} className="text-center py-8 text-green-500 font-semibold">No upcoming shortages detected!</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Total Materials</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Avg Risk Score</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Materials With Shortage</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {plantRows.map((p: any, idx: number) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{p.plant_name}</td>
                      <td className="py-3 px-4">{p.count}</td>
                      <td className="py-3 px-4 font-semibold">{p.avgRisk.toFixed(1)}</td>
                      <td className="py-3 px-4 text-red-600 font-semibold">{p.shortages}</td>
                      <td className="py-3 px-4">{getRiskBadge(p.avgRisk)}</td>
                    </tr>
                  ))}
                  {plantRows.length === 0 && (
                    <tr><td colSpan={5} className="text-center py-8 text-muted-foreground">No plant risk data available.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
