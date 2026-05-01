// SLyK-53 Configuration
// These values are populated during deployment

const config = {
  // AWS Region
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  
  // Bedrock Agent
  agentId: process.env.REACT_APP_AGENT_ID || '',
  agentAliasId: process.env.REACT_APP_AGENT_ALIAS_ID || '',
  
  // Cognito
  identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID || '',
  userPoolId: process.env.REACT_APP_USER_POOL_ID || '',
  userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || '',
  
  // API Gateway
  apiEndpoint: process.env.REACT_APP_API_ENDPOINT || '',
  
  // DynamoDB
  sessionsTable: process.env.REACT_APP_SESSIONS_TABLE || 'slyk-sessions',
  auditTable: process.env.REACT_APP_AUDIT_TABLE || 'slyk-audit-log',
  
  // S3
  documentsBucket: process.env.REACT_APP_DOCUMENTS_BUCKET || '',
  
  // Feature flags
  enableKnowledgeBase: process.env.REACT_APP_ENABLE_KB === 'true',
  enableSecurityHub: process.env.REACT_APP_ENABLE_SECURITYHUB !== 'false',
  
  // UI Settings
  maxMessageLength: 4000,
  sessionTimeoutMinutes: 30,
};

export default config;
