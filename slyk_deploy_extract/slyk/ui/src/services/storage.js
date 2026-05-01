/**
 * SLyK-53 Storage Service
 * Handles DynamoDB operations for sessions and audit logging
 */

import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { 
  DynamoDBDocumentClient, 
  PutCommand, 
  GetCommand, 
  QueryCommand,
  UpdateCommand 
} from '@aws-sdk/lib-dynamodb';
import config from '../config';
import authService from './auth';

class StorageService {
  constructor() {
    this.client = null;
    this.docClient = null;
  }

  /**
   * Initialize DynamoDB client
   */
  async initClient() {
    const credentials = await authService.getCredentials();
    this.client = new DynamoDBClient({
      region: config.region,
      credentials,
    });
    this.docClient = DynamoDBDocumentClient.from(this.client);
  }

  /**
   * Ensure client is initialized
   */
  async ensureClient() {
    if (!this.docClient) {
      await this.initClient();
    }
  }

  // ─── Session Management ───────────────────────────────────────────────────

  /**
   * Save a chat session
   */
  async saveSession(sessionId, messages, metadata = {}) {
    await this.ensureClient();

    const item = {
      sessionId,
      messages,
      updatedAt: new Date().toISOString(),
      createdAt: metadata.createdAt || new Date().toISOString(),
      userId: authService.getIdentityId(),
      ...metadata,
    };

    await this.docClient.send(new PutCommand({
      TableName: config.sessionsTable,
      Item: item,
    }));

    return item;
  }

  /**
   * Load a chat session
   */
  async loadSession(sessionId) {
    await this.ensureClient();

    const response = await this.docClient.send(new GetCommand({
      TableName: config.sessionsTable,
      Key: { sessionId },
    }));

    return response.Item;
  }

  /**
   * List recent sessions for the current user
   */
  async listSessions(limit = 20) {
    await this.ensureClient();

    const userId = authService.getIdentityId();
    if (!userId) return [];

    const response = await this.docClient.send(new QueryCommand({
      TableName: config.sessionsTable,
      IndexName: 'userId-updatedAt-index',
      KeyConditionExpression: 'userId = :userId',
      ExpressionAttributeValues: {
        ':userId': userId,
      },
      ScanIndexForward: false, // Most recent first
      Limit: limit,
    }));

    return response.Items || [];
  }

  // ─── Audit Logging ────────────────────────────────────────────────────────

  /**
   * Log an audit event
   */
  async logAuditEvent(eventType, details = {}) {
    await this.ensureClient();

    const item = {
      eventId: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      eventType,
      userId: authService.getIdentityId(),
      sessionId: details.sessionId,
      action: details.action,
      resource: details.resource,
      result: details.result,
      metadata: details.metadata || {},
    };

    await this.docClient.send(new PutCommand({
      TableName: config.auditTable,
      Item: item,
    }));

    return item;
  }

  /**
   * Query audit logs
   */
  async queryAuditLogs(filters = {}) {
    await this.ensureClient();

    const { startDate, endDate, eventType, limit = 100 } = filters;

    let keyCondition = 'eventType = :eventType';
    const expressionValues = {
      ':eventType': eventType || 'ALL',
    };

    if (startDate && endDate) {
      keyCondition += ' AND #ts BETWEEN :start AND :end';
      expressionValues[':start'] = startDate;
      expressionValues[':end'] = endDate;
    }

    const response = await this.docClient.send(new QueryCommand({
      TableName: config.auditTable,
      IndexName: 'eventType-timestamp-index',
      KeyConditionExpression: keyCondition,
      ExpressionAttributeValues: expressionValues,
      ExpressionAttributeNames: startDate ? { '#ts': 'timestamp' } : undefined,
      ScanIndexForward: false,
      Limit: limit,
    }));

    return response.Items || [];
  }

  // ─── Assessment Results ───────────────────────────────────────────────────

  /**
   * Save assessment results
   */
  async saveAssessmentResult(assessmentId, results) {
    await this.ensureClient();

    const item = {
      assessmentId,
      timestamp: new Date().toISOString(),
      userId: authService.getIdentityId(),
      results,
      summary: {
        total: results.length,
        passed: results.filter(r => r.status === 'PASS').length,
        failed: results.filter(r => r.status === 'FAIL').length,
        warnings: results.filter(r => r.status === 'WARNING').length,
      },
    };

    await this.docClient.send(new PutCommand({
      TableName: config.sessionsTable,
      Item: {
        sessionId: `assessment-${assessmentId}`,
        ...item,
      },
    }));

    // Log audit event
    await this.logAuditEvent('ASSESSMENT', {
      action: 'run_assessment',
      result: item.summary,
    });

    return item;
  }
}

// Export singleton instance
const storageService = new StorageService();
export default storageService;
