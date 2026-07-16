import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Package } from 'lucide-react';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function MaterialsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/products', { headers: authHeaders() })
      .then(res => res.json())
      .then(res => { setData(res?.items || []); setLoading(false); })
      .catch(() => { setData([]); setLoading(false); });
  }, []);

  const items = Array.isArray(data) ? data : [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Materials</h1>
          <p className="text-muted-foreground">List of materials, planners, ABC classification and procurement policies.</p>
        </div>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8 flex items-center justify-center gap-2">
              <Package className="h-5 w-5 animate-pulse" /> Loading Materials...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material Code</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Name</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Procurement</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Type</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">ABC Class</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Lead Time</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Planner</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((m, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold text-primary">{m.material_code || m.sku}</td>
                      <td className="py-3 px-4 font-medium">{m.name}</td>
                      <td className="py-3 px-4">{m.procurement_type || 'EXTERNAL'}</td>
                      <td className="py-3 px-4">{m.material_type || m.type || '—'}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline">{m.abc_class || '—'}</Badge>
                      </td>
                      <td className="py-3 px-4">{m.lead_time_days != null ? `${m.lead_time_days} days` : '—'}</td>
                      <td className="py-3 px-4 text-xs">{m.planner || '—'}</td>
                      <td className="py-3 px-4">
                        <Badge variant={m.is_active ? 'default' : 'secondary'}>
                          {m.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr><td colSpan={8} className="text-center py-8 text-muted-foreground">No materials found.</td></tr>
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
