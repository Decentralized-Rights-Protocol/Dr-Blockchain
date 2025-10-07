"use client";

import React from "react";

export default function TransparencyPage() {
  // Minimal scaffold with mocked data; wire to API later
  const decisions = [
    { id: "dec_1234", outcome: "approved", confidence: 0.94 },
  ];
  const models = [
    { model_id: "face_verification_v1", version: "1.2.0" },
  ];
  return (
    <div style={{ padding: 24 }}>
      <h1>AI Transparency</h1>
      <h2>Recent Decisions</h2>
      <ul>
        {decisions.map((d) => (
          <li key={d.id}>
            {d.id} • {d.outcome} • {(d.confidence * 100).toFixed(1)}%
          </li>
        ))}
      </ul>
      <h2>Models</h2>
      <ul>
        {models.map((m) => (
          <li key={m.model_id}>
            {m.model_id} v{m.version}
          </li>
        ))}
      </ul>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Area, AreaChart
} from 'recharts';

// Types
interface AIDecision {
  decision_id: string;
  model_version: string;
  decision: string;
  confidence: number;
  explanation: string;
  timestamp: string;
  signature: string;
  elder_node: string;
  decision_type: string;
  processing_time_ms: number;
  review_required: boolean;
  explainability?: {
    method: string;
    decision_factors: string[];
    confidence_breakdown: {
      positive_factors: number;
      negative_factors: number;
      uncertainty: number;
    };
  };
}

interface AIStats {
  time_period: string;
  total_decisions: number;
  outcomes: Record<string, number>;
  decision_types: Record<string, number>;
  average_confidence: number;
  average_processing_time_ms: number;
  review_required: number;
  review_rate: number;
}

interface BiasAlert {
  decision_id: string;
  timestamp: string;
  model_id: string;
  bias_type: string;
  confidence: number;
  severity: string;
}

interface DisputeStats {
  total_disputes: number;
  resolved_disputes: number;
  ai_supported: number;
  ai_overturned: number;
  ai_accuracy_percent: number;
  pending_disputes: number;
}

interface ModelInfo {
  model_id: string;
  version: string;
  description: string;
  intended_use: string;
  last_audit_date: string;
  audit_score: number;
  bias_assessment: {
    overall_bias_level: string;
    demographic_parity: number;
    equalized_odds: number;
  };
  limitations: string[];
  performance_metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
  };
}

// Color scheme
const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  purple: '#8b5cf6',
  pink: '#ec4899'
};

const SEVERITY_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981'
};

export default function TransparencyDashboard() {
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [stats, setStats] = useState<AIStats | null>(null);
  const [biasAlerts, setBiasAlerts] = useState<BiasAlert[]>([]);
  const [disputeStats, setDisputeStats] = useState<DisputeStats | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState('24h');

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // Fetch all data in parallel
        const [decisionsRes, statsRes, biasRes, disputesRes, modelsRes] = await Promise.all([
          fetch(`${baseUrl}/api/v1/ai/decisions?limit=50`),
          fetch(`${baseUrl}/api/v1/ai/stats?time_period=${timePeriod}`),
          fetch(`${baseUrl}/api/v1/ai/bias-alerts`),
          fetch(`${baseUrl}/api/v1/ai/disputes`),
          fetch(`${baseUrl}/api/v1/ai/models`)
        ]);

        if (!decisionsRes.ok || !statsRes.ok || !biasRes.ok || !disputesRes.ok || !modelsRes.ok) {
          throw new Error('Failed to fetch data from API');
        }

        const [decisionsData, statsData, biasData, disputesData, modelsData] = await Promise.all([
          decisionsRes.json(),
          statsRes.json(),
          biasRes.json(),
          modelsRes.json()
        ]);

        setDecisions(decisionsData.decisions || []);
        setStats(statsData);
        setBiasAlerts(biasData.bias_alerts || []);
        setDisputeStats(disputesData.statistics);
        setModels(modelsData.models || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load transparency data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timePeriod]);

  // Chart data preparation
  const outcomesData = stats ? Object.entries(stats.outcomes).map(([outcome, count]) => ({
    outcome: outcome.charAt(0).toUpperCase() + outcome.slice(1),
    count,
    percentage: (count / stats.total_decisions * 100).toFixed(1)
  })) : [];

  const decisionTypesData = stats ? Object.entries(stats.decision_types).map(([type, count]) => ({
    type: type.replace('_', ' ').toUpperCase(),
    count
  })) : [];

  const confidenceData = decisions.slice(0, 20).map((decision, index) => ({
    index: index + 1,
    confidence: decision.confidence,
    decision_type: decision.decision_type
  }));

  const biasSeverityData = biasAlerts.reduce((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const biasPieData = Object.entries(biasSeverityData).map(([severity, count]) => ({
    name: severity.charAt(0).toUpperCase() + severity.slice(1),
    value: count,
    color: SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || COLORS.gray
  }));

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading AI Transparency Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert className="max-w-md">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AI Transparency Dashboard</h1>
          <p className="text-gray-600">
            Real-time monitoring of AI Elder decisions, bias detection, and human oversight
          </p>
        </div>

        {/* Time Period Selector */}
        <div className="mb-6">
          <div className="flex space-x-2">
            {['1h', '24h', '7d', '30d'].map((period) => (
              <Button
                key={period}
                variant={timePeriod === period ? 'default' : 'outline'}
                onClick={() => setTimePeriod(period)}
                size="sm"
              >
                {period}
              </Button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Decisions</CardTitle>
              <div className="h-4 w-4 text-blue-600">📊</div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_decisions || 0}</div>
              <p className="text-xs text-gray-500">Last {timePeriod}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
              <div className="h-4 w-4 text-green-600">🎯</div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.average_confidence ? (stats.average_confidence * 100).toFixed(1) : 0}%
              </div>
              <p className="text-xs text-gray-500">AI decision confidence</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bias Alerts</CardTitle>
              <div className="h-4 w-4 text-red-600">⚠️</div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{biasAlerts.length}</div>
              <p className="text-xs text-gray-500">Requiring attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Accuracy</CardTitle>
              <div className="h-4 w-4 text-purple-600">🤖</div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {disputeStats?.ai_accuracy_percent || 0}%
              </div>
              <p className="text-xs text-gray-500">vs Human consensus</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="decisions">Decisions</TabsTrigger>
            <TabsTrigger value="bias">Bias Detection</TabsTrigger>
            <TabsTrigger value="disputes">Disputes</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Decision Outcomes Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Decision Outcomes</CardTitle>
                  <CardDescription>Distribution of AI Elder decisions</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={outcomesData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="outcome" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill={COLORS.primary} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Decision Types Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Decision Types</CardTitle>
                  <CardDescription>Types of AI decisions made</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={decisionTypesData}
                        dataKey="count"
                        nameKey="type"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill={COLORS.primary}
                      >
                        {decisionTypesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={Object.values(COLORS)[index % Object.values(COLORS).length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Confidence Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Decision Confidence Trend</CardTitle>
                <CardDescription>Recent AI decision confidence scores</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={confidenceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="index" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip formatter={(value) => [(value as number * 100).toFixed(1) + '%', 'Confidence']} />
                    <Line type="monotone" dataKey="confidence" stroke={COLORS.primary} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Decisions Tab */}
          <TabsContent value="decisions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent AI Decisions</CardTitle>
                <CardDescription>Latest decisions from AI Elder nodes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {decisions.map((decision) => (
                    <div key={decision.decision_id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant={decision.decision === 'approved' ? 'default' : 'destructive'}>
                            {decision.decision}
                          </Badge>
                          <span className="text-sm text-gray-500">{decision.decision_type}</span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(decision.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{decision.explanation}</p>
                      <div className="flex items-center justify-between text-sm">
                        <span>Confidence: {(decision.confidence * 100).toFixed(1)}%</span>
                        <span>Processing: {decision.processing_time_ms}ms</span>
                        <span>Elder: {decision.elder_node}</span>
                      </div>
                      {decision.explainability && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                          <strong>Decision Factors:</strong>
                          <ul className="list-disc list-inside mt-1">
                            {decision.explainability.decision_factors.map((factor, idx) => (
                              <li key={idx}>{factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bias Detection Tab */}
          <TabsContent value="bias" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Bias Severity Distribution</CardTitle>
                  <CardDescription>Distribution of bias alerts by severity</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={biasPieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                      >
                        {biasPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Bias Alerts</CardTitle>
                  <CardDescription>Latest bias detection alerts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {biasAlerts.slice(0, 5).map((alert) => (
                      <div key={alert.decision_id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">{alert.bias_type}</div>
                          <div className="text-sm text-gray-500">
                            Model: {alert.model_id} • Confidence: {(alert.confidence * 100).toFixed(1)}%
                          </div>
                        </div>
                        <Badge 
                          variant={alert.severity === 'high' ? 'destructive' : 'secondary'}
                        >
                          {alert.severity}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Disputes Tab */}
          <TabsContent value="disputes" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>AI vs Human Agreement</CardTitle>
                  <CardDescription>Consensus statistics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    {disputeStats?.ai_accuracy_percent || 0}%
                  </div>
                  <p className="text-sm text-gray-500">AI accuracy vs human consensus</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Total Disputes</CardTitle>
                  <CardDescription>All time disputes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{disputeStats?.total_disputes || 0}</div>
                  <p className="text-sm text-gray-500">
                    {disputeStats?.pending_disputes || 0} pending resolution
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Resolved Cases</CardTitle>
                  <CardDescription>Successfully resolved</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{disputeStats?.resolved_disputes || 0}</div>
                  <p className="text-sm text-gray-500">
                    {disputeStats?.ai_supported || 0} AI supported, {disputeStats?.ai_overturned || 0} overturned
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Models Tab */}
          <TabsContent value="models" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {models.map((model) => (
                <Card key={model.model_id}>
                  <CardHeader>
                    <CardTitle>{model.model_id}</CardTitle>
                    <CardDescription>v{model.version}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-700 mb-4">{model.description}</p>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Audit Score:</span>
                        <span className="text-sm">{(model.audit_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Bias Level:</span>
                        <Badge variant={model.bias_assessment.overall_bias_level === 'low' ? 'default' : 'destructive'}>
                          {model.bias_assessment.overall_bias_level}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Accuracy:</span>
                        <span className="text-sm">{(model.performance_metrics.accuracy * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Last Audit:</span>
                        <span className="text-sm">{new Date(model.last_audit_date).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="mt-4">
                      <h4 className="text-sm font-medium mb-2">Limitations:</h4>
                      <ul className="text-xs text-gray-600 list-disc list-inside">
                        {model.limitations.slice(0, 3).map((limitation, idx) => (
                          <li key={idx}>{limitation}</li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
