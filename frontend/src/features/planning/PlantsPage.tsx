import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin } from 'lucide-react';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function PlantsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/warehouses', { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setData(res?.items || []);
        setLoading(false);
      })
      .catch(() => {
        setData([]);
        setLoading(false);
      });
  }, []);

  const items = Array.isArray(data) ? data : [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Plants</h1>
        <p className="text-muted-foreground">Manufacturing sites, storage capacities, and contact endpoints.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-8">Loading Plants...</div>
        ) : (
          items.map((p, idx) => (
            <Card key={idx} className="bg-card/45 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base font-semibold">{p.name}</CardTitle>
                <MapPin className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Plant Code:</span>
                  <span className="font-semibold">{p.code}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Location:</span>
                  <span>{p.city}, {p.country}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Manager:</span>
                  <span>{p.contact_person || "N/A"}</span>
                </div>
                <div className="mt-2 pt-2 border-t flex justify-end">
                  <Badge variant={p.is_active ? 'default' : 'secondary'}>
                    {p.is_active ? 'OPERATIONAL' : 'INACTIVE'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
