/**
 * SLyK-53 Authentication Service
 * Handles AWS Cognito authentication and credential management
 */

import { 
  CognitoIdentityClient, 
  GetIdCommand, 
  GetCredentialsForIdentityCommand 
} from '@aws-sdk/client-cognito-identity';
import config from '../config';

class AuthService {
  constructor() {
    this.credentials = null;
    this.identityId = null;
    this.expirationTime = null;
    this.client = new CognitoIdentityClient({ region: config.region });
  }

  /**
   * Get AWS credentials for unauthenticated access (guest)
   * In production, this would use Console IAM session federation
   */
  async getCredentials() {
    // Check if we have valid cached credentials
    if (this.credentials && this.expirationTime && new Date() < this.expirationTime) {
      return this.credentials;
    }

    try {
      // Get identity ID
      const idResponse = await this.client.send(new GetIdCommand({
        IdentityPoolId: config.identityPoolId,
      }));
      
      this.identityId = idResponse.IdentityId;

      // Get credentials for the identity
      const credResponse = await this.client.send(new GetCredentialsForIdentityCommand({
        IdentityId: this.identityId,
      }));

      this.credentials = {
        accessKeyId: credResponse.Credentials.AccessKeyId,
        secretAccessKey: credResponse.Credentials.SecretKey,
        sessionToken: credResponse.Credentials.SessionToken,
      };

      // Set expiration (credentials typically last 1 hour)
      this.expirationTime = credResponse.Credentials.Expiration;

      return this.credentials;
    } catch (error) {
      console.error('Failed to get credentials:', error);
      throw error;
    }
  }

  /**
   * Get credentials with IAM role assumption (for Console-authenticated users)
   * This uses the existing AWS Console session
   */
  async getCredentialsWithIAM(idToken) {
    try {
      const idResponse = await this.client.send(new GetIdCommand({
        IdentityPoolId: config.identityPoolId,
        Logins: {
          [`cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}`]: idToken,
        },
      }));

      this.identityId = idResponse.IdentityId;

      const credResponse = await this.client.send(new GetCredentialsForIdentityCommand({
        IdentityId: this.identityId,
        Logins: {
          [`cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}`]: idToken,
        },
      }));

      this.credentials = {
        accessKeyId: credResponse.Credentials.AccessKeyId,
        secretAccessKey: credResponse.Credentials.SecretKey,
        sessionToken: credResponse.Credentials.SessionToken,
      };

      this.expirationTime = credResponse.Credentials.Expiration;

      return this.credentials;
    } catch (error) {
      console.error('Failed to get IAM credentials:', error);
      throw error;
    }
  }

  /**
   * Check if credentials are valid and not expired
   */
  isAuthenticated() {
    return this.credentials && this.expirationTime && new Date() < this.expirationTime;
  }

  /**
   * Clear cached credentials
   */
  clearCredentials() {
    this.credentials = null;
    this.identityId = null;
    this.expirationTime = null;
  }

  /**
   * Get the current identity ID
   */
  getIdentityId() {
    return this.identityId;
  }
}

// Export singleton instance
const authService = new AuthService();
export default authService;
