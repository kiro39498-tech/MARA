import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  Package, 
  ShoppingCart, 
  AlertTriangle,
  ArrowRight,
  ClipboardList,
  Activity,
  Layers,
  MapPin
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

export function DashboardPage() {
  const [kpis, setKpis] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const token = localStorage.getItem('access_token') || '';
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [kpisRes, recsRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/planning/dashboard-kpis', { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),
          fetch('http://localhost:8000/api/v1/planning/recommendations', { headers })
            .then(r => r.ok ? r.json() : [])
            .catch(() => [])
        ]);
        
        if (kpisRes && !kpisRes.detail) {
          setKpis(kpisRes);
        }
        if (Array.isArray(recsRes)) {
          setRecs(recsRes);
        }
      } catch (err) {
        console.error("Error loading dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="p-8 text-center">Loading Planning Dashboard...</div>;
  }

  // Mock projection timeline data for Chart
  const chartData = [
    { date: 'Jul 14', Demand: 120, Supply: 150, Projected: 30 },
    { date: 'Jul 15', Demand: 140, Supply: 100, Projected: -10 },
    { date: 'Jul 16', Demand: 90, Supply: 200, Projected: 100 },
    { date: 'Jul 17', Demand: 210, Supply: 150, Projected: 40 },
    { date: 'Jul 18', Demand: 110, Supply: 80, Projected: 10 },
    { date: 'Jul 19', Demand: 130, Supply: 190, Projected: 70 },
  ];

  const recommendationsList = Array.isArray(recs) ? recs : [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Planning Dashboard</h1>
        <p className="text-muted-foreground">Manufacturing Decision Support & Replenishment Control Room.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/45 backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Materials</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis?.critical_shortages ?? 0}</div>
            <p className="text-xs text-muted-foreground">Immediate stockout risk detected.</p>
          </CardContent>
        </Card>

        <Card className="bg-card/45 backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Production Orders At Risk</CardTitle>
            <ClipboardList className="h-4 w-4 text-warning text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis?.impacted_production_orders ?? 0}</div>
            <p className="text-xs text-muted-foreground">Delayed due to missing components.</p>
          </CardContent>
        </Card>

        <Card className="bg-card/45 backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Safety Stock Violations</CardTitle>
            <Package className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis?.safety_stock_violations ?? 0}</div>
            <p className="text-xs text-muted-foreground">Stock levels below policy buffers.</p>
          </CardContent>
        </Card>

        <Card className="bg-card/45 backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Plants</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis?.total_plants ?? 0}</div>
            <p className="text-xs text-muted-foreground">Manufacturing nodes active.</p>
          </CardContent>
        </Card>
      </div>

      {/* Projection Timeline Chart */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-card/45 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Material Projection Timeline</CardTitle>
            <CardDescription>Aggregate time-phased balance projection vs incoming supply and demand.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="Projected" stroke="#8884d8" strokeWidth={3} />
                  <Line type="monotone" dataKey="Demand" stroke="#ef4444" strokeWidth={1} />
                  <Line type="monotone" dataKey="Supply" stroke="#10b981" strokeWidth={1} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Replenishment Recommendations */}
        <Card className="col-span-3 bg-card/45 backdrop-blur-md">
          <CardHeader>
            <CardTitle>Top Recommendations</CardTitle>
            <CardDescription>Generated actions by the planning engine.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {recommendationsList.slice(0, 4).map((rec, idx) => (
              <div key={idx} className="flex items-start justify-between border-b pb-3 last:border-0 last:pb-0">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={rec.priority === 'CRITICAL' ? 'destructive' : 'secondary'}>
                      {rec.recommendation_type}
                    </Badge>
                    <span className="text-sm font-semibold">{rec.material_code}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">{rec.reason}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold block">{rec.quantity} units</span>
                  <span className="text-xs text-muted-foreground">{rec.plant_name}</span>
                </div>
              </div>
            ))}
            {recommendationsList.length === 0 && (
              <div className="text-center text-sm text-muted-foreground">No recommendations pending.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
