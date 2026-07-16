import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function MaterialProjectionPage() {
  const [proj, setProj] = useState<any>(null);
  const [materials, setMaterials] = useState<{ id: number; code: string; name: string }[]>([]);
  const [plants, setPlants] = useState<{ id: number; name: string }[]>([]);
  const [materialId, setMaterialId] = useState<number | null>(null);
  const [plantId, setPlantId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/inventory-health', { headers: authHeaders() })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const seenMaterials = new Set<number>();
          const uniqueMaterials: any[] = [];
          const seenPlants = new Set<number>();
          const uniquePlants: any[] = [];

          data.forEach(item => {
            if (item.material_id && !seenMaterials.has(item.material_id)) {
              seenMaterials.add(item.material_id);
              uniqueMaterials.push({
                id: item.material_id,
                code: item.material_code,
                name: item.material_name
              });
            }
            if (item.plant_id && !seenPlants.has(item.plant_id)) {
              seenPlants.add(item.plant_id);
              uniquePlants.push({
                id: item.plant_id,
                name: item.plant_name
              });
            }
          });

          setMaterials(uniqueMaterials);
          setPlants(uniquePlants);

          if (uniqueMaterials.length > 0) setMaterialId(uniqueMaterials[0].id);
          if (uniquePlants.length > 0) setPlantId(uniquePlants[0].id);
        }
      })
      .catch((err) => console.error("Error fetching inventory health", err));
  }, []);

  useEffect(() => {
    if (materialId === null || plantId === null) return;
    setLoading(true);
    fetch(`http://localhost:8000/api/v1/planning/projection?material_id=${materialId}&plant_id=${plantId}`, { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setProj(res);
        setLoading(false);
      })
      .catch(() => {
        setProj(null);
        setLoading(false);
      });
  }, [materialId, plantId]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Material Projection</h1>
          <p className="text-muted-foreground">Time-phased projected inventory balance timeline based on supply & demand.</p>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          {materials.length > 0 && (
            <select
              value={materialId || ''}
              onChange={(e) => setMaterialId(Number(e.target.value))}
              className="border p-2 rounded bg-background text-sm flex-1 md:flex-initial"
            >
              {materials.map((m) => (
                <option key={m.id} value={m.id}>{m.code} - {m.name}</option>
              ))}
            </select>
          )}
          {plants.length > 0 && (
            <select
              value={plantId || ''}
              onChange={(e) => setPlantId(Number(e.target.value))}
              className="border p-2 rounded bg-background text-sm flex-1 md:flex-initial"
            >
              {plants.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {loading || !proj || proj.detail ? (
        <div className="text-center py-8">
          {materials.length === 0 ? "No inventory records available to project." : "Calculating projection..."}
        </div>
      ) : (
        <div className="grid gap-6">
          <Card className="bg-card/45 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Daily Projected Balance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={proj.timeline} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="projected_balance" name="Projected Balance" stroke="#10b981" strokeWidth={3} activeDot={{ r: 8 }} />
                    <Line type="monotone" dataKey="incoming_supply" name="Incoming Supply" stroke="#3b82f6" />
                    <Line type="monotone" dataKey="production_demand" name="Demand" stroke="#ef4444" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/45 backdrop-blur-md">
            <CardContent className="pt-6">
              <div className="grid gap-4 grid-cols-2 md:grid-cols-4 text-center">
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Initial Balance</span>
                  <span className="text-2xl font-bold block">{proj.initial_balance} pcs</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">First Shortage</span>
                  <span className={`text-2xl font-bold block ${proj.first_shortage_date ? 'text-destructive' : 'text-green-500'}`}>
                    {proj.first_shortage_date || "None"}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Max Shortage Qty</span>
                  <span className="text-2xl font-bold block text-destructive">{proj.shortage_quantity} pcs</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Days of Coverage</span>
                  <span className="text-2xl font-bold block">{proj.days_of_coverage} days</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
