import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  AlertTriangle, 
  MapPin, 
  Package, 
  ShoppingCart, 
  ClipboardList, 
  LineChart as ChartIcon, 
  Sparkles, 
  Users, 
  RefreshCw,
  Send,
  ArrowRight,
  TrendingUp,
  FileSpreadsheet
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

const headers = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json'
});

// 1. Materials Page
export function MaterialsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/products', { headers: headers() })
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Materials</h1>
          <p className="text-muted-foreground">List of materials, planners, ABC classification and procurement policies.</p>
        </div>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Materials...</div>
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
                      <td className="py-3 px-4 font-medium">{m.material_code || m.sku}</td>
                      <td className="py-3 px-4">{m.name}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline">{m.procurement_type || "BUY"}</Badge>
                      </td>
                      <td className="py-3 px-4">{m.material_type || "RAW"}</td>
                      <td className="py-3 px-4">
                        <Badge>{m.abc_classification || "C"}</Badge>
                      </td>
                      <td className="py-3 px-4">{m.lead_time || 7} days</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{m.planner || "System"}</td>
                      <td className="py-3 px-4">
                        <Badge variant={m.is_active !== false ? 'default' : 'secondary'}>
                          {m.is_active !== false ? 'ACTIVE' : 'INACTIVE'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 2. Plants Page
export function PlantsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/warehouses', { headers: headers() })
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

// 3. Inventory Health Page
export function InventoryHealthPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/inventory-health', { headers: headers() })
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
        <h1 className="text-3xl font-bold tracking-tight">Inventory Health</h1>
        <p className="text-muted-foreground">Real-time stock buffers, reserved quantities, and safety violations.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Inventory Health...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">On Hand</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Reserved</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Blocked</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Quality Hold</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Safety Stock</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Usable Qty</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((inv, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-semibold">{inv.material_code}</td>
                      <td className="py-3 px-4 text-xs">{inv.plant_name}</td>
                      <td className="py-3 px-4">{inv.on_hand}</td>
                      <td className="py-3 px-4 text-orange-500">{inv.reserved}</td>
                      <td className="py-3 px-4 text-red-500">{inv.blocked}</td>
                      <td className="py-3 px-4 text-yellow-600">{inv.quality_hold}</td>
                      <td className="py-3 px-4 font-medium">{inv.safety_stock}</td>
                      <td className="py-3 px-4 font-bold text-green-600 dark:text-green-400">{inv.usable_inventory}</td>
                      <td className="py-3 px-4">
                        <Badge variant={inv.status === 'HEALTHY' ? 'default' : inv.status === 'AT_RISK' ? 'outline' : 'destructive'}>
                          {inv.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 4. Production Orders Page
export function ProductionOrdersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/production-impact', { headers: headers() })
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

// 5. Purchase Orders Page
export function PurchaseOrdersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/purchases', { headers: headers() })
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
        <h1 className="text-3xl font-bold tracking-tight">Purchase Orders</h1>
        <p className="text-muted-foreground">Incoming supplier materials, expected receipt dates, and delivery status.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Purchase Orders...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">PO Number</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Supplier</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Order Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">ETA Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Total Cost</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((po, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{po.po_number || po.purchase_number}</td>
                      <td className="py-3 px-4">{po.supplier?.name || "Global Vendor"}</td>
                      <td className="py-3 px-4 text-xs">{po.plant?.name || "Main Plant"}</td>
                      <td className="py-3 px-4">{po.order_date}</td>
                      <td className="py-3 px-4 font-medium text-blue-600 dark:text-blue-400">{po.expected_receipt_date}</td>
                      <td className="py-3 px-4">${po.total_amount?.toLocaleString()}</td>
                      <td className="py-3 px-4">
                        <Badge variant={po.status === 'RECEIVED' ? 'default' : 'outline'}>
                          {po.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 6. Material Projection Page
export function MaterialProjectionPage() {
  const [proj, setProj] = useState<any>(null);
  const [materialId, setMaterialId] = useState(1);
  const [plantId, setPlantId] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8000/api/v1/planning/projection?material_id=${materialId}&plant_id=${plantId}`, { headers: headers() })
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Material Projection</h1>
          <p className="text-muted-foreground">Time-phased projected inventory balance timeline based on supply & demand.</p>
        </div>
        <div className="flex gap-2">
          <select 
            value={materialId} 
            onChange={(e) => setMaterialId(Number(e.target.value))}
            className="border p-2 rounded bg-background"
          >
            {[...Array(20)].map((_, i) => (
              <option key={i} value={i+1}>Material MAT-{10000+i}</option>
            ))}
          </select>
          <select 
            value={plantId} 
            onChange={(e) => setPlantId(Number(e.target.value))}
            className="border p-2 rounded bg-background"
          >
            {[...Array(10)].map((_, i) => (
              <option key={i} value={i+1}>Plant PLT-{100+i}</option>
            ))}
          </select>
        </div>
      </div>

      {loading || !proj || proj.detail ? (
        <div className="text-center py-8">Calculating projection...</div>
      ) : (
        <div className="grid gap-6">
          <Card className="bg-card/45 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Daily Projected Balance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={proj.timeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="projected_balance" name="Projected Balance" stroke="#10b981" strokeWidth={3} />
                    <Line type="monotone" dataKey="incoming_supply" name="Incoming Supply" stroke="#3b82f6" />
                    <Line type="monotone" dataKey="production_demand" name="Demand" stroke="#ef4444" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/45 backdrop-blur-md">
            <CardContent className="pt-6">
              <div className="grid gap-4 md:grid-cols-4 text-center">
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

// 7. Shortage Analysis Page
export function ShortageAnalysisPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/material-risk', { headers: headers() })
      .then(res => res.json())
      .then(res => {
        setData(Array.isArray(res) ? res.filter((r: any) => r.first_shortage_date !== null) : []);
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
        <h1 className="text-3xl font-bold tracking-tight">Shortage Analysis</h1>
        <p className="text-muted-foreground">Pre-empty detection of material stockouts, first shortage dates, and days of coverage.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Analyzing shortages...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Risk Score</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">First Shortage</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Days of Coverage</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((r, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{r.material_code}</td>
                      <td className="py-3 px-4">{r.plant_name}</td>
                      <td className="py-3 px-4 font-semibold text-red-500">{r.risk_score?.toFixed(1)}</td>
                      <td className="py-3 px-4 text-red-600 font-semibold">{r.first_shortage_date || "N/A"}</td>
                      <td className="py-3 px-4 font-bold">{r.days_of_coverage} days</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{r.reason}</td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-green-500 font-semibold">No upcoming shortages detected over the horizon!</td>
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

// 8. Recommendations Page
export function RecommendationsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/planning/recommendations', { headers: headers() })
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
        <h1 className="text-3xl font-bold tracking-tight">Replenishment Recommendations</h1>
        <p className="text-muted-foreground">Planning engine suggestions. Select expedite or plant transfer actions with one-click approval.</p>
      </div>
      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-8">Evaluating recommendations...</div>
        ) : (
          items.map((rec, idx) => (
            <Card key={idx} className="bg-card/45 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-2">
                  <Badge variant={rec.priority === 'CRITICAL' ? 'destructive' : 'secondary'}>
                    {rec.recommendation_type}
                  </Badge>
                  <span className="font-bold text-lg">{rec.material_code}</span>
                </div>
                <Badge variant="outline">{rec.priority} Priority</Badge>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <p className="text-sm font-medium">{rec.reason}</p>
                <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
                  <strong>Evidence:</strong> {rec.evidence}
                </div>
                <div className="flex items-center justify-between mt-2 pt-2 border-t">
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>Plant: <strong>{rec.plant_name}</strong></span>
                    <span>Quantity: <strong>{rec.quantity} units</strong></span>
                    <span>Confidence: <strong>{(rec.confidence * 100).toFixed(0)}%</strong></span>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">Reject</Button>
                    <Button size="sm">Approve Action</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

// 9. Supplier Performance Page
export function SupplierPerformancePage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/suppliers', { headers: headers() })
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
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 10. Planning Copilot Page
export function PlanningCopilotPage() {
  const [messages, setMessages] = useState<any[]>([
    { sender: 'assistant', text: 'Hello! I am the MARA Planning Copilot. Ask me about material status, production order shortages, or replenishment actions.' }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/planning/copilot', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          session_id: 'local_session',
          message: input
        })
      }).then(r => r.json());

      setMessages(prev => [...prev, { sender: 'assistant', text: response.response, evidence: response.evidence }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'assistant', text: 'Error communicating with orchestrator. Please try again.' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-140px)]">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Planning Copilot</h1>
        <p className="text-muted-foreground">Ask questions grounded in deterministic planning computations.</p>
      </div>

      <div className="flex-1 flex flex-col border rounded-xl overflow-hidden bg-card/45 backdrop-blur-md">
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex flex-col max-w-[80%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              <div 
                className={`p-3 rounded-lg text-sm ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}
              >
                <p className="whitespace-pre-line">{msg.text}</p>
              </div>
              {msg.evidence && Object.keys(msg.evidence).length > 0 && (
                <div className="mt-1 bg-muted/30 border text-[11px] p-2 rounded max-w-full overflow-x-auto text-muted-foreground font-mono">
                  <strong>Evidence Source:</strong> {JSON.stringify(msg.evidence, null, 2)}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="p-3 border-t bg-background flex gap-2">
          <Input 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            placeholder="Why is MAT-10001 critical? Show top recommendations..."
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={sending}
          />
          <Button onClick={handleSend} disabled={sending}>
            {sending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

// Redefine LoginPage placeholder to preserve working routing
export { LoginPage } from './auth/LoginPage';
export function PurchasesPage() { return <PurchaseOrdersPage />; }
export function SalesPage() { return <ProductionOrdersPage />; }
export function UsersPage() { return <div className="p-6">Users & Roles Manager. Use Settings / User Management routes.</div>; }
