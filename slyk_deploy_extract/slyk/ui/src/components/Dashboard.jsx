import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = {
  pass: '#4ade80',
  fail: '#f87171',
  warning: '#fbbf24',
  info: '#4a9eff',
};

function Dashboard({ assessmentData }) {
  const [stats, setStats] = useState({
    complianceScore: 0,
    totalControls: 0,
    passed: 0,
    failed: 0,
    warnings: 0,
    lastAssessment: null,
  });

  const [controlsByFamily, setControlsByFamily] = useState([]);
  const [recentFindings, setRecentFindings] = useState([]);

  useEffect(() => {
    if (assessmentData) {
      processAssessmentData(assessmentData);
    } else {
      // Load mock data for demo
      loadMockData();
    }
  }, [assessmentData]);

  const processAssessmentData = (data) => {
    const summary = data.summary || {};
    const controls = data.controls || [];

    setStats({
      complianceScore: summary.compliance_percentage || 0,
      totalControls: summary.total_controls || controls.length,
      passed: summary.passed || controls.filter(c => c.status === 'PASS').length,
      failed: summary.failed || controls.filter(c => c.status === 'FAIL').length,
      warnings: summary.warnings || controls.filter(c => c.status === 'WARNING').length,
      lastAssessment: new Date().toISOString(),
    });

    // Group by family
    const families = {};
    controls.forEach(c => {
      const family = c.family || c.control_id?.split('-')[0] || 'Unknown';
      if (!families[family]) {
        families[family] = { family, pass: 0, fail: 0, warning: 0 };
      }
      if (c.status === 'PASS') families[family].pass++;
      else if (c.status === 'FAIL') families[family].fail++;
      else families[family].warning++;
    });
    setControlsByFamily(Object.values(families));

    // Recent findings (failed controls)
    setRecentFindings(
      controls
        .filter(c => c.status === 'FAIL')
        .slice(0, 5)
        .map(c => ({
          controlId: c.control_id,
          name: c.control_name,
          finding: c.findings?.[0] || 'Control check failed',
          severity: 'HIGH',
        }))
    );
  };

  const loadMockData = () => {
    setStats({
      complianceScore: 71.4,
      totalControls: 7,
      passed: 5,
      failed: 2,
      warnings: 0,
      lastAssessment: new Date().toISOString(),
    });

    setControlsByFamily([
      { family: 'AC', pass: 1, fail: 1, warning: 0 },
      { family: 'AU', pass: 1, fail: 0, warning: 0 },
      { family: 'IA', pass: 1, fail: 0, warning: 0 },
      { family: 'SC', pass: 1, fail: 1, warning: 0 },
      { family: 'SI', pass: 1, fail: 0, warning: 0 },
    ]);

    setRecentFindings([
      { controlId: 'AC-2', name: 'Account Management', finding: '3 users without MFA', severity: 'HIGH' },
      { controlId: 'SC-28', name: 'Protection at Rest', finding: '2 S3 buckets without encryption', severity: 'MEDIUM' },
    ]);
  };

  const pieData = [
    { name: 'Passed', value: stats.passed, color: COLORS.pass },
    { name: 'Failed', value: stats.failed, color: COLORS.fail },
    { name: 'Warnings', value: stats.warnings, color: COLORS.warning },
  ].filter(d => d.value > 0);

  return (
    <div className="dashboard">
      {/* Stats Cards */}
      <div className="dashboard-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-title">Compliance Score</span>
            <span className="stat-card-icon">📊</span>
          </div>
          <div className="stat-card-value" style={{ color: stats.complianceScore >= 80 ? COLORS.pass : stats.complianceScore >= 60 ? COLORS.warning : COLORS.fail }}>
            {stats.complianceScore.toFixed(1)}%
          </div>
          <div className={`stat-card-change ${stats.complianceScore >= 70 ? 'positive' : 'negative'}`}>
            {stats.complianceScore >= 70 ? '↑' : '↓'} {stats.complianceScore >= 70 ? 'Above' : 'Below'} target (70%)
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-title">Controls Passed</span>
            <span className="stat-card-icon">✅</span>
          </div>
          <div className="stat-card-value" style={{ color: COLORS.pass }}>
            {stats.passed}
          </div>
          <div className="stat-card-change positive">
            of {stats.totalControls} total controls
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-title">Controls Failed</span>
            <span className="stat-card-icon">❌</span>
          </div>
          <div className="stat-card-value" style={{ color: COLORS.fail }}>
            {stats.failed}
          </div>
          <div className="stat-card-change negative">
            Requires remediation
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-title">Last Assessment</span>
            <span className="stat-card-icon">🕐</span>
          </div>
          <div className="stat-card-value" style={{ fontSize: '20px' }}>
            {stats.lastAssessment ? new Date(stats.lastAssessment).toLocaleDateString() : 'Never'}
          </div>
          <div className="stat-card-change">
            {stats.lastAssessment ? new Date(stats.lastAssessment).toLocaleTimeString() : 'Run an assessment'}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {/* Compliance by Family */}
        <div className="data-table">
          <div className="data-table-header">
            <span className="data-table-title">Compliance by Control Family</span>
          </div>
          <div style={{ padding: '20px', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={controlsByFamily} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333355" />
                <XAxis type="number" stroke="#a0a0a0" />
                <YAxis dataKey="family" type="category" stroke="#a0a0a0" width={40} />
                <Tooltip 
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333355' }}
                  labelStyle={{ color: '#e0e0e0' }}
                />
                <Bar dataKey="pass" stackId="a" fill={COLORS.pass} name="Passed" />
                <Bar dataKey="fail" stackId="a" fill={COLORS.fail} name="Failed" />
                <Bar dataKey="warning" stackId="a" fill={COLORS.warning} name="Warning" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution */}
        <div className="data-table">
          <div className="data-table-header">
            <span className="data-table-title">Control Status Distribution</span>
          </div>
          <div style={{ padding: '20px', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333355' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Findings Table */}
      <div className="data-table">
        <div className="data-table-header">
          <span className="data-table-title">Recent Findings</span>
          <button className="quick-action" style={{ padding: '6px 12px' }}>
            View All →
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Control</th>
              <th>Name</th>
              <th>Finding</th>
              <th>Severity</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {recentFindings.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                  No findings. Run an assessment to check compliance.
                </td>
              </tr>
            ) : (
              recentFindings.map((finding, i) => (
                <tr key={i}>
                  <td><code>{finding.controlId}</code></td>
                  <td>{finding.name}</td>
                  <td>{finding.finding}</td>
                  <td>
                    <span className={`badge ${finding.severity === 'HIGH' ? 'fail' : finding.severity === 'MEDIUM' ? 'warning' : 'info'}`}>
                      {finding.severity}
                    </span>
                  </td>
                  <td>
                    <button className="quick-action" style={{ padding: '4px 10px', fontSize: '12px' }}>
                      Remediate
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
