/**
 * SLyK-53 Bedrock Agent Service
 * Handles communication with the SLyK Bedrock Agent
 */

import { 
  BedrockAgentRuntimeClient, 
  InvokeAgentCommand 
} from '@aws-sdk/client-bedrock-agent-runtime';
import config from '../config';
import authService from './auth';

class AgentService {
  constructor() {
    this.client = null;
    this.sessionId = this.generateSessionId();
  }

  /**
   * Generate a unique session ID
   */
  generateSessionId() {
    return crypto.randomUUID ? crypto.randomUUID() : 
      'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
  }

  /**
   * Initialize the Bedrock client with credentials
   */
  async initClient() {
    const credentials = await authService.getCredentials();
    this.client = new BedrockAgentRuntimeClient({
      region: config.region,
      credentials,
    });
  }

  /**
   * Send a message to the SLyK agent and stream the response
   */
  async sendMessage(message, onChunk) {
    if (!this.client) {
      await this.initClient();
    }

    const command = new InvokeAgentCommand({
      agentId: config.agentId,
      agentAliasId: config.agentAliasId,
      sessionId: this.sessionId,
      inputText: message,
      enableTrace: false,
    });

    try {
      const response = await this.client.send(command);
      let fullResponse = '';

      // Process the streaming response
      for await (const event of response.completion) {
        if (event.chunk?.bytes) {
          const chunk = new TextDecoder().decode(event.chunk.bytes);
          fullResponse += chunk;
          if (onChunk) {
            onChunk(chunk, fullResponse);
          }
        }
      }

      return fullResponse;
    } catch (error) {
      console.error('Agent invocation failed:', error);
      
      // Handle credential expiration
      if (error.name === 'ExpiredTokenException' || error.name === 'CredentialsProviderError') {
        authService.clearCredentials();
        await this.initClient();
        // Retry once
        return this.sendMessage(message, onChunk);
      }
      
      throw error;
    }
  }

  /**
   * Start a new conversation session
   */
  newSession() {
    this.sessionId = this.generateSessionId();
    return this.sessionId;
  }

  /**
   * Get the current session ID
   */
  getSessionId() {
    return this.sessionId;
  }

  /**
   * Quick action shortcuts
   */
  async assessCompliance(families = 'ALL') {
    return this.sendMessage(`Assess my NIST 800-53 compliance for ${families} controls`);
  }

  async hardenS3() {
    return this.sendMessage('Scan and harden all my S3 buckets');
  }

  async hardenEC2() {
    return this.sendMessage('Scan and harden all my EC2 instances');
  }

  async hardenIAM() {
    return this.sendMessage('Scan and harden my IAM users and policies');
  }

  async getSecurityHubFindings(severity = 'CRITICAL,HIGH') {
    return this.sendMessage(`Show me Security Hub findings with severity ${severity}`);
  }

  async remediateControl(controlId) {
    return this.sendMessage(`Generate remediation for control ${controlId}`);
  }

  async generateSSP(systemName) {
    return this.sendMessage(`Generate a System Security Plan for ${systemName}`);
  }
}

// Export singleton instance
const agentService = new AgentService();
export default agentService;
