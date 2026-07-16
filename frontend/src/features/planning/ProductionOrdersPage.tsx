import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function ProductionOrdersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/production-impact', { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setData(res || []);
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
        <h1 className="text-3xl font-bold tracking-tight">Production Orders</h1>
        <p className="text-muted-foreground">Scheduled assembly orders, required components and stock shortages.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Production Orders...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Order No</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Assembly Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Qty</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Required Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Priority</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Shortage Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((po, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{po.order_number}</td>
                      <td className="py-3 px-4">{po.material_code} - {po.material_name}</td>
                      <td className="py-3 px-4 text-xs">{po.plant_name}</td>
                      <td className="py-3 px-4">{po.quantity}</td>
                      <td className="py-3 px-4">{po.required_date}</td>
                      <td className="py-3 px-4">
                        <Badge variant={po.priority === 'CRITICAL' || po.priority === 'HIGH' ? 'destructive' : 'secondary'}>
                          {po.priority}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">{po.status}</td>
                      <td className="py-3 px-4 text-xs text-red-500 font-medium">{po.shortage_reason}</td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={8} className="text-center py-8 text-muted-foreground">All production orders fully covered. No component shortages detected.</td>
                    </tr>
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
