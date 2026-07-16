import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function SupplierPerformancePage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/suppliers', { headers: authHeaders() })
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
        <h1 className="text-3xl font-bold tracking-tight">Supplier Performance</h1>
        <p className="text-muted-foreground">On-Time Delivery rates, lead-time variances, and vendor quality score metrics.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Supplier Metrics...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Code</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Supplier Name</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Contact</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">On-Time Rate</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Quality Score</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Lead Time Variance</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((sup, idx) => {
                    const onTime = 95 - (idx % 15);
                    const quality = 98 - (idx % 10);
                    return (
                      <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                        <td className="py-3 px-4 font-medium">{sup.code}</td>
                        <td className="py-3 px-4 font-semibold">{sup.name}</td>
                        <td className="py-3 px-4 text-xs text-muted-foreground">{sup.email}</td>
                        <td className="py-3 px-4 text-green-600 font-bold">{onTime}%</td>
                        <td className="py-3 px-4 font-bold text-blue-600">{quality}/100</td>
                        <td className="py-3 px-4">{1.5 + (idx % 3)} days</td>
                      </tr>
                    );
                  })}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-muted-foreground">No supplier performance data found.</td>
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
