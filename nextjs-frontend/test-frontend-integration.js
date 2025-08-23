#!/usr/bin/env node

/**
 * Frontend Integration Test Runner
 * 
 * This script provides a simple way to test your Next.js frontend
 * integration with the FastAPI backend without complex test frameworks.
 * 
 * Usage: node test-frontend-integration.js
 */

const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  frontendUrl: process.env.NEXTAUTH_URL || 'http://localhost:8501',
  testTimeout: 30000 // 30 seconds
};

class FrontendIntegrationTester {
  constructor() {
    this.testResults = [];
    this.startTime = Date.now();
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
      'info': 'ℹ️',
      'success': '✅',
      'error': '❌',
      'warning': '⚠️'
    }[type] || 'ℹ️';
    
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  async testApiClientConfiguration() {
    this.log('Testing API Client Configuration...', 'info');
    
    const tests = [
      {
        name: 'API Client Base URL',
        test: () => {
          // Read the API client file
          const apiClientPath = path.join(process.cwd(), 'src', 'lib', 'api-client.ts');
          if (!fs.existsSync(apiClientPath)) {
            throw new Error('API client file not found');
          }
          
          const content = fs.readFileSync(apiClientPath, 'utf8');
          
          // Check for proper configuration
          const hasBaseURL = content.includes('baseURL:') || content.includes('API_URL');
          const hasTimeout = content.includes('timeout:');
          const hasAuth = content.includes('Authorization') || content.includes('Bearer');
          
          return { hasBaseURL, hasTimeout, hasAuth };
        }
      },
      {
        name: 'Environment Variables Setup',
        test: () => {
          const envPath = path.join(process.cwd(), '.env.local');
          const envExamplePath = path.join(process.cwd(), 'env.example');
          
          const hasEnvLocal = fs.existsSync(envPath);
          const hasEnvExample = fs.existsSync(envExamplePath);
          
          let envVars = {};
          if (hasEnvLocal) {
            const envContent = fs.readFileSync(envPath, 'utf8');
            envVars = this.parseEnvFile(envContent);
          }
          
          return { hasEnvLocal, hasEnvExample, envVars };
        }
      },
      {
        name: 'Type Definitions',
        test: () => {
          const typesPath = path.join(process.cwd(), 'src', 'types', 'index.ts');
          if (!fs.existsSync(typesPath)) {
            throw new Error('Types file not found');
          }
          
          const content = fs.readFileSync(typesPath, 'utf8');
          
          // Check for key interfaces
          const hasEnvironment = content.includes('interface Environment');
          const hasStorageItem = content.includes('interface StorageItem');
          const hasApiResponse = content.includes('interface ApiResponse');
          const hasUser = content.includes('interface User');
          
          return { hasEnvironment, hasStorageItem, hasApiResponse, hasUser };
        }
      }
    ];

    for (const test of tests) {
      try {
        const result = test.test();
        this.testResults.push({
          name: test.name,
          success: true,
          result: result
        });
        this.log(`${test.name}: PASS`, 'success');
      } catch (error) {
        this.testResults.push({
          name: test.name,
          success: false,
          error: error.message
        });
        this.log(`${test.name}: FAIL - ${error.message}`, 'error');
      }
    }
  }

  async testComponentStructure() {
    this.log('Testing Component Structure...', 'info');
    
    const requiredComponents = [
      'src/components/environments/EnvironmentManagement.tsx',
      'src/components/layout/MainLayout.tsx', 
      'src/components/auth/ProtectedRoute.tsx',
      'src/app/dashboard/page.tsx',
      'src/app/environments/page.tsx',
      'src/app/api/auth/[...nextauth]/route.ts'
    ];

    for (const componentPath of requiredComponents) {
      const fullPath = path.join(process.cwd(), componentPath);
      const exists = fs.existsSync(fullPath);
      
      this.testResults.push({
        name: `Component: ${componentPath}`,
        success: exists,
        error: exists ? null : 'File not found'
      });
      
      if (exists) {
        this.log(`Component ${componentPath}: EXISTS`, 'success');
      } else {
        this.log(`Component ${componentPath}: MISSING`, 'error');
      }
    }
  }

  async testPackageConfiguration() {
    this.log('Testing Package Configuration...', 'info');
    
    try {
      const packagePath = path.join(process.cwd(), 'package.json');
      const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
      
      // Check required dependencies
      const requiredDeps = [
        'next',
        'react',
        'react-dom',
        'next-auth',
        'axios',
        '@tanstack/react-query',
        'antd'
      ];

      const missingDeps = requiredDeps.filter(dep => 
        !packageJson.dependencies?.[dep] && !packageJson.devDependencies?.[dep]
      );

      this.testResults.push({
        name: 'Required Dependencies',
        success: missingDeps.length === 0,
        result: { missing: missingDeps, total: requiredDeps.length }
      });

      if (missingDeps.length === 0) {
        this.log('All required dependencies present', 'success');
      } else {
        this.log(`Missing dependencies: ${missingDeps.join(', ')}`, 'error');
      }

      // Check scripts
      const requiredScripts = ['dev', 'build', 'start'];
      const missingScripts = requiredScripts.filter(script => !packageJson.scripts?.[script]);

      this.testResults.push({
        name: 'Required Scripts',
        success: missingScripts.length === 0,
        result: { missing: missingScripts }
      });

      if (missingScripts.length === 0) {
        this.log('All required scripts present', 'success');
      } else {
        this.log(`Missing scripts: ${missingScripts.join(', ')}`, 'warning');
      }

    } catch (error) {
      this.testResults.push({
        name: 'Package JSON',
        success: false,
        error: error.message
      });
      this.log(`Package.json error: ${error.message}`, 'error');
    }
  }

  async testBackendConnectivity() {
    this.log('Testing Backend Connectivity...', 'info');
    
    try {
      // Use Node.js fetch (available in Node 18+) or require https
      const https = require('https');
      const http = require('http');
      const url = require('url');
      
      const testEndpoint = async (endpoint) => {
        return new Promise((resolve, reject) => {
          const parsedUrl = url.parse(`${CONFIG.apiUrl}${endpoint}`);
          const client = parsedUrl.protocol === 'https:' ? https : http;
          
          const req = client.get(parsedUrl, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
              resolve({
                status: res.statusCode,
                data: data,
                headers: res.headers
              });
            });
          });
          
          req.on('error', reject);
          req.setTimeout(5000, () => {
            req.destroy();
            reject(new Error('Request timeout'));
          });
        });
      };

      // Test health endpoint
      try {
        const healthResponse = await testEndpoint('/health');
        this.testResults.push({
          name: 'Backend Health Check',
          success: healthResponse.status === 200,
          result: { status: healthResponse.status }
        });
        
        if (healthResponse.status === 200) {
          this.log('Backend health check: PASS', 'success');
        } else {
          this.log(`Backend health check: FAIL (status: ${healthResponse.status})`, 'error');
        }
      } catch (error) {
        this.testResults.push({
          name: 'Backend Health Check',
          success: false,
          error: error.message
        });
        this.log(`Backend health check: FAIL (${error.message})`, 'error');
      }

      // Test CORS
      try {
        const corsResponse = await testEndpoint('/health');
        const corsHeaders = corsResponse.headers['access-control-allow-origin'] || 
                           corsResponse.headers['Access-Control-Allow-Origin'];
        
        this.testResults.push({
          name: 'CORS Configuration',
          success: !!corsHeaders,
          result: { corsHeaders }
        });
        
        if (corsHeaders) {
          this.log(`CORS configured: ${corsHeaders}`, 'success');
        } else {
          this.log('CORS headers not found', 'warning');
        }
      } catch (error) {
        this.log(`CORS test error: ${error.message}`, 'warning');
      }

    } catch (error) {
      this.log(`Backend connectivity test error: ${error.message}`, 'error');
    }
  }

  parseEnvFile(content) {
    const vars = {};
    const lines = content.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          vars[key.trim()] = valueParts.join('=').trim();
        }
      }
    }
    
    return vars;
  }

  generateReport() {
    const endTime = Date.now();
    const duration = endTime - this.startTime;
    
    console.log('\n' + '='.repeat(60));
    console.log('🎯 FRONTEND INTEGRATION TEST REPORT');
    console.log('='.repeat(60));
    
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.success).length;
    const successRate = totalTests > 0 ? (passedTests / totalTests) * 100 : 0;
    
    console.log(`\n📊 Summary:`);
    console.log(`   Tests: ${passedTests}/${totalTests} (${successRate.toFixed(1)}%)`);
    console.log(`   Duration: ${duration}ms`);
    console.log(`   Timestamp: ${new Date().toISOString()}`);
    
    // Categorize results
    const categories = {
      'Configuration': this.testResults.filter(r => 
        r.name.includes('API Client') || r.name.includes('Environment Variables') || r.name.includes('Package')
      ),
      'Components': this.testResults.filter(r => r.name.includes('Component')),
      'Backend': this.testResults.filter(r => 
        r.name.includes('Backend') || r.name.includes('CORS')
      ),
      'Types': this.testResults.filter(r => r.name.includes('Type'))
    };
    
    console.log(`\n📋 Results by Category:`);
    for (const [category, tests] of Object.entries(categories)) {
      if (tests.length > 0) {
        const categoryPassed = tests.filter(t => t.success).length;
        const categoryRate = (categoryPassed / tests.length) * 100;
        const icon = categoryRate === 100 ? '✅' : categoryRate >= 50 ? '⚠️' : '❌';
        console.log(`   ${icon} ${category}: ${categoryPassed}/${tests.length} (${categoryRate.toFixed(0)}%)`);
      }
    }
    
    // Failed tests
    const failedTests = this.testResults.filter(r => !r.success);
    if (failedTests.length > 0) {
      console.log(`\n❌ Failed Tests:`);
      failedTests.forEach(test => {
        console.log(`   • ${test.name}: ${test.error || 'Unknown error'}`);
      });
    }
    
    // Integration readiness
    console.log(`\n🎯 Integration Readiness:`);
    if (successRate >= 90) {
      console.log('   🟢 EXCELLENT - Frontend ready for backend integration!');
    } else if (successRate >= 75) {
      console.log('   🟡 GOOD - Minor configuration needed');
    } else if (successRate >= 50) {
      console.log('   🟠 FAIR - Several issues to resolve');
    } else {
      console.log('   🔴 POOR - Major setup problems');
    }
    
    // Save report
    const reportData = {
      timestamp: new Date().toISOString(),
      duration: duration,
      summary: {
        total: totalTests,
        passed: passedTests,
        failed: totalTests - passedTests,
        successRate: successRate
      },
      configuration: CONFIG,
      results: this.testResults
    };
    
    fs.writeFileSync('frontend-integration-report.json', JSON.stringify(reportData, null, 2));
    console.log(`\n📄 Detailed report saved to: frontend-integration-report.json`);
    
    console.log('='.repeat(60));
  }

  async runAllTests() {
    this.log('🧪 Starting Frontend Integration Tests...', 'info');
    this.log(`Frontend URL: ${CONFIG.frontendUrl}`, 'info');
    this.log(`Backend URL: ${CONFIG.apiUrl}`, 'info');
    console.log('-'.repeat(60));
    
    await this.testPackageConfiguration();
    await this.testApiClientConfiguration();
    await this.testComponentStructure();
    await this.testBackendConnectivity();
    
    this.generateReport();
  }
}

// Run tests
async function main() {
  const tester = new FrontendIntegrationTester();
  await tester.runAllTests();
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { FrontendIntegrationTester };
