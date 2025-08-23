# 🧪 CMB Cluster Integration Testing Guide

This directory contains comprehensive testing tools to verify that your Next.js frontend integrates seamlessly with your FastAPI backend.

## 🚀 Quick Start

### 1. Backend Integration Test
Tests your FastAPI backend endpoints and compatibility:

```bash
# Install dependencies
pip install requests python-dotenv

# Run backend tests
python test_integration.py

# With custom backend URL
python test_integration.py --url http://your-backend-url:8000
```

### 2. Frontend Integration Test  
Tests your Next.js frontend configuration and structure:

```bash
cd nextjs-frontend

# Run frontend tests
node test-frontend-integration.js
```

### 3. Manual UI Testing
Follow the comprehensive manual test cases:

```bash
# Review the test plan
open UI_TEST_CASES.md

# Start both services
cd backend && python main.py &
cd nextjs-frontend && npm run dev &

# Open browser and follow test cases
open http://localhost:8501
```

## 📋 Test Coverage

### Backend API Tests ✅
- ✅ Health check endpoint
- ✅ Authentication flow  
- ✅ Environment management (CRUD)
- ✅ Storage management
- ✅ User environment variables
- ✅ File upload/download
- ✅ Activity logging
- ✅ CORS configuration
- ✅ Error handling
- ✅ Data format compatibility

### Frontend Configuration Tests ✅
- ✅ API client configuration
- ✅ Environment variables setup
- ✅ Component structure
- ✅ Type definitions
- ✅ Package dependencies
- ✅ Build scripts
- ✅ Backend connectivity

### Integration Flow Tests ✅
- ✅ OAuth authentication
- ✅ Environment lifecycle management
- ✅ Real-time updates  
- ✅ Storage operations
- ✅ File management
- ✅ Error handling
- ✅ Mobile responsiveness
- ✅ Performance optimization

## 🎯 Expected Results

### ✅ If Everything Works
```
🎉 INTEGRATION TEST REPORT
========================== 
Tests Passed: 15/15 (100%)
🟢 EXCELLENT - Ready for production!

✅ Integration Checklist:
   ✅ Authentication
   ✅ Environment Management  
   ✅ Storage Operations
   ✅ User Settings
   ✅ CORS Configured
   ✅ Data Compatibility
```

### ⚠️ Common Issues and Fixes

**Issue**: CORS errors
```bash
# Fix: Update backend CORS settings
allow_origins=["http://localhost:8501", "your-frontend-url"]
```

**Issue**: Authentication failures  
```bash
# Fix: Check environment variables
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
NEXTAUTH_SECRET=your-secret
```

**Issue**: API endpoint not found
```bash  
# Fix: Verify backend is running
curl http://localhost:8000/health
```

**Issue**: Storage class mismatch
```bash
# Fix: Use uppercase in backend or normalize in frontend
"STANDARD" vs "standard"
```

## 📊 Test Reports

Both test scripts generate detailed JSON reports:

- `integration_test_report.json` - Backend API test results
- `frontend-integration-report.json` - Frontend structure test results

## 🔧 Development Workflow

1. **Code Changes**: Make changes to frontend or backend
2. **Run Tests**: Execute integration tests
3. **Check Reports**: Review generated reports
4. **Fix Issues**: Address any failing tests
5. **Manual Verification**: Follow UI test cases
6. **Deploy**: Push to production when all tests pass

## 🎭 Mock Data for Testing

The test scripts include realistic mock data that matches your backend models:

```typescript
// Test environments
const mockEnvironments = [
  {
    id: 'env-running-123',
    status: 'running', 
    resource_config: {
      cpu_limit: 2.0,
      memory_limit: '4Gi',
      storage_size: '50Gi'
    }
  }
];

// Test storage items
const mockStorageOptions = [
  {
    id: 'storage-123',
    display_name: 'Research Data Workspace',
    storage_class: 'standard',
    status: 'active'
  }
];
```

## 🐛 Debugging Tips

### Backend Issues
```bash
# Check backend logs
python main.py --debug

# Test specific endpoint
curl -H "Authorization: Bearer dev-token" http://localhost:8000/environments/list

# Verify database
sqlite3 cmbcluster.db ".tables"
```

### Frontend Issues
```bash
# Check browser console for errors
# Open DevTools → Console

# Verify environment variables
cat .env.local

# Check network requests
# DevTools → Network tab
```

### Integration Issues
```bash
# Test end-to-end flow manually
1. Login via Google OAuth
2. Create environment  
3. Check if environment appears
4. Test environment actions
5. Verify real-time updates
```

## 🎪 Demo Scenarios

### Scenario 1: New User Onboarding
1. First-time Google login
2. Dashboard tour
3. Launch first environment
4. Upload configuration files
5. Access running environment

### Scenario 2: Research Workflow
1. Upload data files
2. Set environment variables
3. Launch heavy computation environment
4. Monitor resource usage
5. Scale with additional environments
6. Clean up when done

### Scenario 3: Multi-Environment Management
1. Create multiple environments
2. Switch between them
3. Use different storage configurations
4. Batch operations (stop/restart multiple)
5. Monitor all environments

## 📈 Performance Expectations

- **Page Load**: < 2 seconds
- **API Response**: < 1 second  
- **Environment Creation**: < 30 seconds
- **Real-time Updates**: 10 second intervals
- **File Upload**: Depends on file size

## 🏆 Success Criteria

Your integration is successful when:

✅ All automated tests pass (90%+ success rate)
✅ Manual UI test cases complete without errors
✅ OAuth authentication works smoothly  
✅ Environment management functions correctly
✅ Real-time updates work reliably
✅ Error handling is graceful
✅ Mobile interface is responsive
✅ Performance meets expectations

## 🚢 Ready for Production

When all tests pass, your Next.js frontend is fully compatible with your FastAPI backend and ready for production deployment!

**Next Steps:**
1. Set up production environment variables
2. Configure production OAuth credentials  
3. Set up monitoring and logging
4. Deploy both frontend and backend
5. Run integration tests against production
6. Monitor for any edge case issues

**Congratulations! Your Streamlit → Next.js migration is complete! 🎉**
